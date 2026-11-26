import asyncio
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from sqlalchemy.future import select
from sqlalchemy import func

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.entities import Job, JobLead, KnownRecord
from app.adapters.base import BaseSourceAdapter
from app.adapters.mock_adapter import MockOdishaAdapter
from app.adapters.justdial_adapter import JustdialAdapter
from app.services.deduper import DeduplicationEngine
from app.services.exporter import generate_leads_excel
from app.services.normalizer import clean_phone_number, normalize_text

logger = logging.getLogger("leadharvest.job_runner")

STAGE_LABELS = {
    "preparing": "Getting everything ready…",
    "searching": "Searching business directory…",
    "collecting": "Collecting business details…",
    "filtering": "Checking against your previous files…",
    "creating_file": "Building your Excel file…",
    "almost_done": "Final checks… getting ready to deliver",
    "success": "All done! Your new leads are ready.",
    "paused": "Collection paused.",
    "cancelled": "Collection stopped by user.",
    "failed": "A problem occurred."
}

ROTATING_TIPS = [
    "You can keep this tab open. We'll keep working.",
    "Deduplicating leads against your uploaded files in real-time.",
    "Normalizing phone numbers to standard 10-digit Indian mobile format.",
    "Applying RapidFuzz token sorting for high-precision address matching.",
    "Auto-fitting columns and embedding clickable links in your Excel file."
]

class JobSession:
    def __init__(self, job_id: str, job_record: Job):
        self.job_id = job_id
        self.status = job_record.status
        self.adapter_name = job_record.adapter_name
        self.cities = json.loads(job_record.cities_json)
        self.categories = json.loads(job_record.categories_json)
        self.remember_leads = job_record.remember_leads
        
        self.total_found = 0
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
        
        self.pause_event = asyncio.Event()
        self.pause_event.set() # Initially unpaused
        
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
        total_est = (elapsed / (self.progress_pct / 100.0))
        return max(0, int(total_est - elapsed))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.job_id,
            "status": self.status,
            "adapter_name": self.adapter_name,
            "total_found": self.total_found,
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
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "elapsed_seconds": self.get_elapsed_seconds(),
            "estimated_remaining_seconds": self.get_estimated_remaining_seconds(),
            "friendly_tip": ROTATING_TIPS[(self.get_elapsed_seconds() // 6) % len(ROTATING_TIPS)]
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

    async def start_job(self, job_record: Job) -> JobSession:
        session = JobSession(job_record.id, job_record)
        self.active_jobs[job_record.id] = session
        
        # Load known records into Deduper from SQLite DB
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(KnownRecord))
            records = result.scalars().all()
            dict_records = [
                {
                    "phone_clean": r.phone_clean,
                    "alt_phone_clean": r.alt_phone_clean,
                    "business_name": r.business_name,
                    "address": r.normalized_address,
                    "city": r.city,
                    "source": r.source,
                    "source_file": r.source_file
                }
                for r in records
            ]
            session.deduper.load_known_records(dict_records)
            logger.info(f"Loaded {len(dict_records)} known records into job {job_record.id} deduplication engine.")

        # Launch background execution task
        session.task = asyncio.create_task(self._run_job_lifecycle(session))
        return session

    async def pause_job(self, job_id: str) -> bool:
        session = self.get_session(job_id)
        if not session or session.status not in ["running", "pending"]:
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

    async def cancel_job(self, job_id: str) -> bool:
        session = self.get_session(job_id)
        if not session or session.status in ["completed", "failed", "cancelled"]:
            return False
        session.is_cancelled = True
        session.status = "cancelling"
        session.pause_event.set() # Unpause to allow loop to exit cleanly
        session.current_stage = "creating_file"
        session.current_detail = "Finishing current batch and building partial Excel file..."
        await session.broadcast()
        return True

    async def _run_job_lifecycle(self, session: JobSession):
        adapter: Optional[BaseSourceAdapter] = None
        try:
            session.status = "running"
            session.current_stage = "preparing"
            session.current_detail = STAGE_LABELS["preparing"]
            await session.broadcast()
            await self._sync_db_state(session)

            if session.adapter_name == "justdial":
                adapter = JustdialAdapter()
            else:
                adapter = MockOdishaAdapter()

            total_combos = len(session.cities) * len(session.categories)
            combo_index = 0

            for city in session.cities:
                if session.is_cancelled:
                    break
                session.current_city = city

                for category in session.categories:
                    if session.is_cancelled:
                        break
                    session.current_category = category
                    combo_index += 1
                    
                    base_progress = ((combo_index - 1) / max(total_combos, 1)) * 80.0
                    session.progress_pct = base_progress
                    session.current_stage = "searching"
                    session.current_detail = f"Searching {category} in {city}…"
                    await session.broadcast()

                    async def on_listing(raw_listing: Dict[str, Any]):
                        session.total_found += 1
                        session.current_stage = "filtering"
                        session.current_detail = f"Auditing listing against known databases… ({session.total_found} found)"
                        
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
                            # Register with deduper to prevent intra-run dupes
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

                    async def check_pause_cancel() -> (bool, bool):
                        return session.is_paused, session.is_cancelled

                    async def wait_for_resume():
                        await session.pause_event.wait()

                    # Run adapter collection
                    await adapter.collect(
                        city=city,
                        category=category,
                        max_scrolls=settings.DEFAULT_MAX_SCROLLS,
                        on_listing_collected=on_listing,
                        on_progress_update=on_progress,
                        check_pause_cancel=check_pause_cancel,
                        wait_for_resume=wait_for_resume
                    )

                    # Update combo progress & sync state to DB after each page
                    session.progress_pct = (combo_index / max(total_combos, 1)) * 80.0
                    await self._sync_db_state(session)
                    await session.broadcast()

            # Stage 5: Creating file
            session.current_stage = "creating_file"
            session.progress_pct = 88.0
            session.current_detail = "Building your styled 3-sheet Excel workbook…"
            await session.broadcast()
            await asyncio.sleep(0.6)

            # Generate Excel
            timestamp_str = datetime.utcnow().strftime("%Y-%m-%d_%H%M")
            filename = f"LeadHarvest_Odisha_{timestamp_str}.xlsx"
            excel_path = settings.EXPORTS_DIR / filename

            duration_sec = session.get_elapsed_seconds()
            duration_fmt = f"{duration_sec // 60}m {duration_sec % 60}s"

            summary_meta = {
                "run_timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "duration": duration_fmt,
                "cities": session.cities,
                "categories": session.categories,
                "total_found": session.total_found,
                "adapter": "Justdial Live" if session.adapter_name == "justdial" else "Odisha Business Directory Engine"
            }

            generate_leads_excel(
                leads=session.collected_leads,
                skipped_duplicates=session.skipped_duplicates,
                summary_meta=summary_meta,
                output_path=excel_path
            )
            session.excel_file = filename

            # Stage 6: Almost done
            session.current_stage = "almost_done"
            session.progress_pct = 96.0
            session.current_detail = "Final checks… getting ready to deliver"
            await session.broadcast()
            await asyncio.sleep(0.5)

            # Remember leads if enabled
            if session.remember_leads and session.collected_leads:
                await self._persist_new_leads_to_known_records(session)

            # Finalize status
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
                    job.duplicates_skipped = session.duplicates_skipped
                    job.new_leads = session.new_leads
                    job.progress_pct = session.progress_pct
                    job.current_stage = session.current_stage
                    job.current_detail = session.current_detail
                    job.current_city = session.current_city
                    job.current_category = session.current_category
                    job.error_message = session.error_message
                    job.excel_file = session.excel_file
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
                        phone_clean=cand_phone,
                        phone_raw=lead.get("phone"),
                        alt_phone_clean=cand_alt,
                        business_name=lead.get("business_name", ""),
                        normalized_name=normalize_text(lead.get("business_name")),
                        normalized_address=normalize_text(lead.get("address")),
                        city=lead.get("city", ""),
                        district=lead.get("district"),
                        category=lead.get("category"),
                        source="harvest_job",
                        run_id=session.job_id
                    )
                    db.add(rec)
                await db.commit()
                logger.info(f"Persisted {len(session.collected_leads)} new leads into KnownRecord index.")
        except Exception as ex:
            logger.error(f"Failed to persist leads to KnownRecord: {ex}")

job_runner_service = JobRunnerService()
