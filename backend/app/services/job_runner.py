import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.entities import Job, KnownRecord
from app.adapters.base import BaseSourceAdapter
from app.adapters.mock_adapter import MockOdishaAdapter
from app.adapters.justdial_adapter import JustdialAdapter
from app.services.deduper import DeduplicationEngine
from app.services.exporter import generate_leads_excel, generate_leads_csv
from app.services.lead_filters import (
    enrich_lead_metadata,
    matches_smart_filters,
    detect_chains_across_leads,
    verify_website_enrichment_hook,
)
from app.services.normalizer import clean_phone_number, normalize_text

logger = logging.getLogger("leadharvest.job_runner")

STAGE_LABELS = {
    "preparing": "Getting everything ready…",
    "searching": "Searching business directory…",
    "collecting": "Collecting business details…",
    "filtering": "Checking Smart Filters & previous files…",
    "creating_file": "Building your Excel file…",
    "almost_done": "Final checks… getting ready to deliver",
    "success": "All done! Your new leads are ready.",
    "paused": "Collection paused.",
    "cancelled": "Collection stopped by user.",
    "failed": "A problem occurred.",
}

ROTATING_TIPS = [
    "You can keep this tab open. We'll keep working.",
    "Scoring every lead (0–100) for website & outreach opportunity.",
    "Deduplicating leads against your personal Known Records in real time.",
    "Normalizing phone numbers and generating one-click WhatsApp links.",
    "Auto-fitting columns and embedding clickable links in your Excel file.",
]


class JobSession:
    def __init__(self, job_id: str, job_record: Job, city_state_map: Optional[Dict[str, str]] = None):
        self.job_id = job_id
        self.user_id = job_record.user_id
        self.guest_id = job_record.guest_id
        self.status = job_record.status
        self.adapter_name = job_record.adapter_name
        self.states = json.loads(job_record.states_json) if job_record.states_json else ["Odisha"]
        self.cities = json.loads(job_record.cities_json)
        self.categories = json.loads(job_record.categories_json)
        self.filters = json.loads(job_record.filters_json) if job_record.filters_json else {}
        self.remember_leads = job_record.remember_leads
        self.max_leads_cap = job_record.max_leads_cap or 100
        self.city_state_map = city_state_map or {}

        self.total_found = 0
        self.filtered_out_count = 0
        self.duplicates_skipped = 0
        self.new_leads = 0
        self.progress_pct = 0.0

        self.current_stage = "preparing"
        self.current_detail = STAGE_LABELS["preparing"]
        self.current_city: Optional[str] = None
        self.current_category: Optional[str] = None

        self.is_paused = False
        self.is_cancelled = False
        self.verification_needed = False
        self.verification_message: Optional[str] = None
        self.error_message: Optional[str] = None

        self.started_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None
        self.excel_file: Optional[str] = None
        self.csv_file: Optional[str] = None

        self.pause_event = asyncio.Event()
        self.pause_event.set()

        self.event_queues: List[asyncio.Queue] = []
        self.collected_leads: List[Dict[str, Any]] = []
        self.skipped_duplicates: List[Dict[str, Any]] = []
        self.deduper = DeduplicationEngine()
        self.task: Optional[asyncio.Task] = None

    def get_elapsed_seconds(self) -> int:
        if not self.started_at:
            return 0
        end_time = self.completed_at or datetime.utcnow()
        return max(0, int((end_time - self.started_at).total_seconds()))

    def get_estimated_remaining_seconds(self) -> int:
        if self.progress_pct <= 0 or self.progress_pct >= 100:
            return 0
        elapsed = self.get_elapsed_seconds()
        total_est = elapsed / (self.progress_pct / 100.0)
        return max(0, int(total_est - elapsed))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.job_id,
            "status": self.status,
            "adapter_name": self.adapter_name,
            "total_found": self.total_found,
            "filtered_out_count": self.filtered_out_count,
            "duplicates_skipped": self.duplicates_skipped,
            "new_leads": self.new_leads,
            "progress_pct": round(self.progress_pct, 1),
            "current_stage": self.current_stage,
            "current_detail": self.current_detail,
            "current_city": self.current_city,
            "current_category": self.current_category,
            "verification_needed": self.verification_needed,
            "verification_message": self.verification_message,
            "error_message": self.error_message,
            "excel_file": self.excel_file,
            "csv_file": self.csv_file,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "elapsed_seconds": self.get_elapsed_seconds(),
            "estimated_remaining_seconds": self.get_estimated_remaining_seconds(),
            "friendly_tip": ROTATING_TIPS[(self.get_elapsed_seconds() // 6) % len(ROTATING_TIPS)],
        }

    async def broadcast(self):
        payload = self.to_dict()
        for q in list(self.event_queues):
            try:
                await q.put(payload)
            except Exception:
                pass


class JobRunnerService:
    def __init__(self):
        self.active_jobs: Dict[str, JobSession] = {}

    def get_session(self, job_id: str) -> Optional[JobSession]:
        return self.active_jobs.get(job_id)

    async def start_job(
        self,
        job_record: Job,
        city_state_map: Optional[Dict[str, str]] = None,
        enable_enrichment: bool = False,
    ) -> JobSession:
        session = JobSession(job_record.id, job_record, city_state_map=city_state_map)
        self.active_jobs[job_record.id] = session

        # Strictly per-user (or per-guest) Known Records isolation
        async with AsyncSessionLocal() as db:
            query = select(KnownRecord)
            if session.user_id:
                query = query.where(KnownRecord.user_id == session.user_id)
            elif session.guest_id:
                query = query.where(KnownRecord.guest_id == session.guest_id)
            else:
                query = query.where(KnownRecord.id == -1)

            result = await db.execute(query)
            records = result.scalars().all()
            dict_records = [
                {
                    "phone_clean": r.phone_clean,
                    "alt_phone_clean": r.alt_phone_clean,
                    "business_name": r.business_name,
                    "address": r.normalized_address,
                    "city": r.city,
                    "source": r.source,
                    "source_file": r.source_file,
                }
                for r in records
            ]
            session.deduper.load_known_records(dict_records)

        session.task = asyncio.create_task(self._run_job_lifecycle(session, enable_enrichment=enable_enrichment))
        return session

    async def pause_job(self, job_id: str) -> bool:
        session = self.get_session(job_id)
        if not session or session.status not in ("running", "pending"):
            return False
        session.is_paused = True
        session.status = "paused"
        session.pause_event.clear()
        session.current_stage = "paused"
        session.current_detail = "Collection paused by user. Click Resume to continue."
        await session.broadcast()
        await self._sync_db_state(session)
        return True

    async def resume_job(self, job_id: str) -> bool:
        session = self.get_session(job_id)
        if not session or session.status != "paused":
            return False
        session.is_paused = False
        session.status = "running"
        session.verification_needed = False
        session.verification_message = None
        session.pause_event.set()
        session.current_stage = "collecting"
        session.current_detail = "Resuming collection..."
        await session.broadcast()
        await self._sync_db_state(session)
        return True

    async def trigger_verification_pause(self, job_id: str) -> bool:
        """Admin testing hook to simulate a CAPTCHA/verification pause."""
        session = self.get_session(job_id)
        if not session or session.status not in ("running", "pending"):
            return False
        session.is_paused = True
        session.verification_needed = True
        session.verification_message = "Simulated verification challenge: please complete verification, then press Resume."
        session.status = "paused"
        session.pause_event.clear()
        session.current_stage = "paused"
        session.current_detail = session.verification_message
        await session.broadcast()
        await self._sync_db_state(session)
        return True

    async def cancel_job(self, job_id: str) -> bool:
        session = self.get_session(job_id)
        if not session or session.status in ("completed", "failed", "cancelled"):
            return False
        session.is_cancelled = True
        session.status = "cancelling"
        session.pause_event.set()
        session.current_stage = "creating_file"
        session.current_detail = "Finishing current batch and building partial Excel file..."
        await session.broadcast()
        return True

    async def _run_job_lifecycle(self, session: JobSession, enable_enrichment: bool = False):
        adapter: Optional[BaseSourceAdapter] = None
        try:
            session.status = "running"
            session.current_stage = "preparing"
            session.current_detail = STAGE_LABELS["preparing"]
            await session.broadcast()
            await self._sync_db_state(session)

            adapter = JustdialAdapter() if session.adapter_name == "justdial" else MockOdishaAdapter()

            total_combos = len(session.cities) * len(session.categories)
            combo_index = 0

            for city in session.cities:
                if session.is_cancelled or session.new_leads >= session.max_leads_cap:
                    break
                session.current_city = city
                state_name = session.city_state_map.get(city, session.states[0] if session.states else "Odisha")

                for category in session.categories:
                    if session.is_cancelled or session.new_leads >= session.max_leads_cap:
                        break
                    session.current_category = category
                    combo_index += 1

                    session.progress_pct = ((combo_index - 1) / max(total_combos, 1)) * 80.0
                    session.current_stage = "searching"
                    session.current_detail = f"Searching {category} in {city}, {state_name}…"
                    await session.broadcast()

                    async def on_listing(raw_listing: Dict[str, Any]):
                        if session.new_leads >= session.max_leads_cap:
                            return

                        session.total_found += 1
                        session.current_stage = "filtering"

                        # Optional lightweight website enrichment
                        if enable_enrichment and raw_listing.get("website"):
                            ok = await verify_website_enrichment_hook(raw_listing["website"], enabled=True)
                            if not ok:
                                raw_listing["website"] = None

                        enrich_lead_metadata(raw_listing)

                        # Smart Lead Filters
                        passed, _ = matches_smart_filters(raw_listing, session.filters)
                        if not passed:
                            session.filtered_out_count += 1
                            await session.broadcast()
                            return

                        # 3-Tier Deduplication Check
                        is_dupe, dupe_rule, dupe_source = session.deduper.check_duplicate(raw_listing)
                        if is_dupe:
                            session.duplicates_skipped += 1
                            raw_listing["is_duplicate"] = True
                            raw_listing["duplicate_rule"] = dupe_rule
                            raw_listing["duplicate_source"] = dupe_source
                            session.skipped_duplicates.append(raw_listing)
                            session.current_detail = f"Checking against previous files… ({session.duplicates_skipped} duplicates skipped)"
                        else:
                            session.new_leads += 1
                            raw_listing["is_duplicate"] = False
                            session.collected_leads.append(raw_listing)
                            session.deduper.register_new_lead(raw_listing, source_label="Current Run")
                            session.current_detail = f"Collecting verified details… ({session.new_leads} new leads)"

                        await session.broadcast()

                    async def on_progress(stage: str, detail: str):
                        if stage == "Verification Needed":
                            session.verification_needed = True
                            session.verification_message = detail
                            session.status = "paused"
                            session.pause_event.clear()
                        session.current_detail = detail
                        await session.broadcast()

                    async def check_pause_cancel():
                        return session.is_paused, session.is_cancelled

                    async def wait_for_resume():
                        await session.pause_event.wait()

                    await adapter.collect(
                        city=city,
                        category=category,
                        max_scrolls=settings.DEFAULT_MAX_SCROLLS,
                        on_listing_collected=on_listing,
                        on_progress_update=on_progress,
                        check_pause_cancel=check_pause_cancel,
                        wait_for_resume=wait_for_resume,
                        state=state_name,
                    )

                    session.progress_pct = (combo_index / max(total_combos, 1)) * 80.0
                    await self._sync_db_state(session)
                    await session.broadcast()

            # Chain/franchise heuristic post-pass
            if session.filters.get("exclude_chains") and session.collected_leads:
                detect_chains_across_leads(session.collected_leads)
                kept = [l for l in session.collected_leads if not l.get("is_chain")]
                session.filtered_out_count += len(session.collected_leads) - len(kept)
                session.collected_leads = kept
                session.new_leads = len(kept)

            # Stage 5: Creating Excel & CSV files
            session.current_stage = "creating_file"
            session.progress_pct = 88.0
            session.current_detail = "Building your styled 3-sheet Excel workbook…"
            await session.broadcast()
            await asyncio.sleep(0.3)

            timestamp_str = datetime.utcnow().strftime("%Y-%m-%d_%H%M")
            excel_filename = f"LeadHarvest_India_{session.job_id}_{timestamp_str}.xlsx"
            csv_filename = f"LeadHarvest_India_{session.job_id}_{timestamp_str}.csv"
            excel_path = settings.EXPORTS_DIR / excel_filename
            csv_path = settings.EXPORTS_DIR / csv_filename

            duration_sec = session.get_elapsed_seconds()
            duration_fmt = f"{duration_sec // 60}m {duration_sec % 60}s"

            summary_meta = {
                "run_timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "duration": duration_fmt,
                "states": session.states,
                "cities": session.cities,
                "categories": session.categories,
                "filters_applied": session.filters,
                "total_found": session.total_found,
                "filtered_out_count": session.filtered_out_count,
                "adapter": "Justdial Live" if session.adapter_name == "justdial" else "LeadHarvest India Engine",
            }

            generate_leads_excel(
                leads=session.collected_leads,
                skipped_duplicates=session.skipped_duplicates,
                summary_meta=summary_meta,
                output_path=excel_path,
            )
            generate_leads_csv(leads=session.collected_leads, output_path=csv_path)
            session.excel_file = excel_filename
            session.csv_file = csv_filename

            # Stage 6: Almost done
            session.current_stage = "almost_done"
            session.progress_pct = 96.0
            session.current_detail = "Final checks… getting ready to deliver"
            await session.broadcast()
            await asyncio.sleep(0.25)

            if session.remember_leads and session.collected_leads:
                await self._persist_new_leads_to_known_records(session)

            if session.collected_leads:
                try:
                    from app.services.hot_leads import ingest_signal_leads_from_job
                    async with AsyncSessionLocal() as hl_db:
                        await ingest_signal_leads_from_job(hl_db, session.collected_leads, session.filters)
                except Exception as hl_err:
                    logger.warning(f"Hot lead signal ingestion skipped: {hl_err}")

            session.completed_at = datetime.utcnow()
            session.progress_pct = 100.0
            if session.is_cancelled:
                session.status = "cancelled"
                session.current_stage = "cancelled"
                session.current_detail = f"Collection stopped. {session.new_leads} leads preserved and ready to download."
            else:
                session.status = "completed"
                session.current_stage = "success"
                session.current_detail = f"All done! {session.new_leads} new leads are ready."

            await session.broadcast()
            await self._sync_db_state(session, finalize=True)

        except Exception as e:
            logger.error(f"Error in job {session.job_id}: {str(e)}", exc_info=True)
            session.status = "failed"
            session.current_stage = "failed"
            session.error_message = f"An unexpected error occurred while collecting listings: {str(e)}"
            session.current_detail = "Job encountered an issue. You can retry with demo mode or alternate cities."
            await session.broadcast()
            await self._sync_db_state(session)
        finally:
            if adapter:
                await adapter.close()

    async def _sync_db_state(self, session: JobSession, finalize: bool = False):
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(Job).where(Job.id == session.job_id))
                job = result.scalar_one_or_none()
                if job:
                    job.status = session.status
                    job.total_found = session.total_found
                    job.filtered_out_count = session.filtered_out_count
                    job.duplicates_skipped = session.duplicates_skipped
                    job.new_leads = session.new_leads
                    job.progress_pct = session.progress_pct
                    job.current_stage = session.current_stage
                    job.current_detail = session.current_detail
                    job.current_city = session.current_city
                    job.current_category = session.current_category
                    job.error_message = session.error_message
                    job.excel_file = session.excel_file
                    job.csv_file = session.csv_file
                    job.duration_seconds = session.get_elapsed_seconds()
                    job.verification_needed = session.verification_needed
                    job.verification_message = session.verification_message
                    if finalize:
                        job.completed_at = session.completed_at
                    await db.commit()
        except Exception as ex:
            logger.error(f"Failed to sync job state to database: {ex}")

    async def _persist_new_leads_to_known_records(self, session: JobSession):
        try:
            async with AsyncSessionLocal() as db:
                for lead in session.collected_leads:
                    cand_phone, _ = clean_phone_number(lead.get("phone"))
                    cand_alt, _ = clean_phone_number(lead.get("alt_phone"))
                    rec = KnownRecord(
                        user_id=session.user_id,
                        guest_id=session.guest_id,
                        phone_clean=cand_phone,
                        phone_raw=lead.get("phone"),
                        alt_phone_clean=cand_alt,
                        business_name=lead.get("business_name", ""),
                        normalized_name=normalize_text(lead.get("business_name")),
                        normalized_address=normalize_text(lead.get("address")),
                        city=lead.get("city", ""),
                        state=lead.get("state", "Odisha"),
                        district=lead.get("district"),
                        category=lead.get("category"),
                        source="harvest_job",
                        run_id=session.job_id,
                    )
                    db.add(rec)
                await db.commit()
        except Exception as ex:
            logger.error(f"Failed to persist leads to KnownRecord: {ex}")


job_runner_service = JobRunnerService()
