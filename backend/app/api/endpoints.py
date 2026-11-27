import asyncio
import json
import logging
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, Response
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, delete
import pandas as pd

from app.core.config import settings
from app.core.database import get_db
from app.models.entities import Job, KnownRecord, Preset, UploadedFileAudit, User, Guest, AnalyticsEvent
from app.schemas.lead import (
    LocationItem, StateItem, CategoryItem, PresetItem, PresetCreate,
    CreateJobRequest, JobStatusResponse, FileAuditCard,
    ColumnMappingUpdate, KnownRecordsStats, ConfirmationPreview
)
from app.services.auditor import audit_file
from app.services.normalizer import clean_phone_number, normalize_text
from app.services.job_runner import job_runner_service
from app.services.lead_filters import PITCH_PRESETS
from app.services.auth import (
    get_current_user_optional, get_or_create_guest, check_rate_limit,
    hash_value, get_client_ip, sign_token, unsign_token
)
from app.services.entitlements import can_user_do, get_user_effective_plan
from app.adapters.mock_adapter import MockOdishaAdapter
from app.adapters.justdial_adapter import JustdialAdapter

router = APIRouter(prefix="/api")
logger = logging.getLogger("leadharvest.api")


def _load_india_locations() -> List[Dict[str, Any]]:
    path = settings.CONFIG_DIR / "india_locations.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    # Fallback to Odisha-only
    od_path = settings.CONFIG_DIR / "odisha_locations.json"
    if od_path.exists():
        with open(od_path, "r", encoding="utf-8") as f:
            return [{"id": "odisha", "name": "Odisha", "type": "State", "cities": json.load(f)}]
    return []


# -------------------------------------------------------------
# Configuration & Meta
# -------------------------------------------------------------
@router.get("/config/locations", response_model=List[LocationItem])
async def get_locations():
    """Backwards-compatible Odisha locations endpoint."""
    india = _load_india_locations()
    for st in india:
        if st.get("id") == "odisha":
            return st.get("cities", [])
    return []


@router.get("/config/india-locations", response_model=List[StateItem])
async def get_india_locations():
    """Returns all 28 Indian states and 8 union territories with cities."""
    return _load_india_locations()


@router.get("/config/categories", response_model=List[CategoryItem])
async def get_categories():
    path = settings.CONFIG_DIR / "categories.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Categories config not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/config/pitch-presets")
async def get_pitch_presets():
    return PITCH_PRESETS


@router.get("/config/adapters")
async def get_adapter_capabilities():
    return {
        "mock": MockOdishaAdapter().capabilities(),
        "justdial": JustdialAdapter().capabilities(),
    }


# -------------------------------------------------------------
# Presets (Per-User Scoped)
# -------------------------------------------------------------
@router.get("/presets", response_model=List[PresetItem])
async def list_presets(
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    if not user:
        return []
    result = await db.execute(
        select(Preset).where(Preset.user_id == user.id).order_by(Preset.created_at.desc())
    )
    presets = result.scalars().all()
    return [
        PresetItem(
            id=p.id,
            name=p.name,
            states=json.loads(p.states_json) if p.states_json else ["Odisha"],
            cities=json.loads(p.cities_json),
            categories=json.loads(p.categories_json),
            filters=json.loads(p.filters_json) if p.filters_json else None,
            created_at=p.created_at,
        )
        for p in presets
    ]


@router.post("/presets", response_model=PresetItem)
async def create_preset(
    req: PresetCreate,
    request: Request,
    response: Response,
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    actor = user or await get_or_create_guest(request, response, db)
    allowed, msg, hint = await can_user_do(db, actor, "save_preset")
    if not allowed:
        raise HTTPException(status_code=403, detail={"message": msg, "upgrade_hint": hint})

    preset_id = str(uuid.uuid4())[:8]
    preset = Preset(
        id=preset_id,
        user_id=user.id,
        name=req.name,
        states_json=json.dumps(req.states),
        cities_json=json.dumps(req.cities),
        categories_json=json.dumps(req.categories),
        filters_json=json.dumps(req.filters.model_dump()) if req.filters else None,
        created_at=datetime.utcnow(),
    )
    db.add(preset)
    await db.commit()
    return PresetItem(
        id=preset.id,
        name=preset.name,
        states=req.states,
        cities=req.cities,
        categories=req.categories,
        filters=req.filters.model_dump() if req.filters else None,
        created_at=preset.created_at,
    )


# -------------------------------------------------------------
# Deduplication File Uploads & Audit (Per-User / Per-Guest)
# -------------------------------------------------------------
@router.post("/uploads", response_model=List[FileAuditCard])
async def upload_dedupe_files(
    request: Request,
    response: Response,
    files: List[UploadFile] = File(...),
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    guest = None if user else await get_or_create_guest(request, response, db)
    results: List[FileAuditCard] = []

    for file in files:
        suffix = Path(file.filename).suffix.lower()
        if suffix not in [".xlsx", ".xls", ".csv"]:
            continue

        file_id = str(uuid.uuid4())
        safe_name = f"{file_id}_{Path(file.filename).name}"
        saved_path = settings.UPLOADS_DIR / safe_name

        content = await file.read()
        if len(content) > 15 * 1024 * 1024:  # 15 MB limit
            raise HTTPException(status_code=400, detail="File exceeds 15 MB limit.")

        with open(saved_path, "wb") as f:
            f.write(content)

        audit_res = audit_file(saved_path)

        db_audit = UploadedFileAudit(
            id=file_id,
            user_id=user.id if user else None,
            guest_id=guest.id if guest else None,
            filename=file.filename,
            stored_path=str(saved_path),
            file_size_bytes=audit_res["file_size_bytes"],
            total_rows=audit_res["total_rows"],
            valid_rows=audit_res["valid_rows"],
            blank_rows=audit_res["blank_rows"],
            invalid_phone_rows=audit_res["invalid_phone_rows"],
            duplicate_rows=audit_res["duplicate_rows"],
            column_mapping_json=json.dumps(audit_res["column_mapping"]),
            detected_columns_json=json.dumps(audit_res["detected_columns"]),
            status=audit_res["status"],
            uploaded_at=datetime.utcnow(),
        )
        db.add(db_audit)
        await db.commit()

        if audit_res["status"] == "ready":
            await _merge_file_into_known_records(
                db, saved_path, audit_res["column_mapping"], file.filename,
                user_id=user.id if user else None,
                guest_id=guest.id if guest else None,
            )

        results.append(FileAuditCard(
            id=file_id,
            filename=file.filename,
            file_size_bytes=audit_res["file_size_bytes"],
            total_rows=audit_res["total_rows"],
            valid_rows=audit_res["valid_rows"],
            blank_rows=audit_res["blank_rows"],
            invalid_phone_rows=audit_res["invalid_phone_rows"],
            duplicate_rows=audit_res["duplicate_rows"],
            column_mapping=audit_res["column_mapping"],
            detected_columns=audit_res["detected_columns"],
            sample_rows=audit_res["sample_rows"],
            status=audit_res["status"],
            uploaded_at=datetime.utcnow(),
        ))

    return results


async def _merge_file_into_known_records(
    db: AsyncSession,
    file_path: Path,
    mapping: Dict[str, str],
    filename: str,
    user_id: Optional[str] = None,
    guest_id: Optional[str] = None,
):
    try:
        suffix = file_path.suffix.lower()
        df = pd.read_csv(file_path, dtype=str) if suffix == ".csv" else pd.read_excel(file_path, dtype=str)

        phone_col = mapping.get("phone")
        name_col = mapping.get("business_name")
        addr_col = mapping.get("address")
        city_col = mapping.get("city")
        cat_col = mapping.get("category")

        for _, row in df.iterrows():
            name = str(row.get(name_col)) if name_col and pd.notna(row.get(name_col)) else ""
            if not name.strip():
                continue

            phone_raw = str(row.get(phone_col)) if phone_col and pd.notna(row.get(phone_col)) else None
            phone_clean, _ = clean_phone_number(phone_raw)
            city = str(row.get(city_col)) if city_col and pd.notna(row.get(city_col)) else "Odisha"
            addr = str(row.get(addr_col)) if addr_col and pd.notna(row.get(addr_col)) else ""
            cat = str(row.get(cat_col)) if cat_col and pd.notna(row.get(cat_col)) else None

            rec = KnownRecord(
                user_id=user_id,
                guest_id=guest_id,
                phone_clean=phone_clean,
                phone_raw=phone_raw,
                business_name=name,
                normalized_name=normalize_text(name),
                normalized_address=normalize_text(addr),
                city=city,
                category=cat,
                source="upload",
                source_file=filename,
            )
            db.add(rec)
        await db.commit()
    except Exception as e:
        logger.error(f"Error merging file into known records: {e}")


@router.post("/uploads/mapping")
async def update_column_mapping(
    req: ColumnMappingUpdate,
    request: Request,
    response: Response,
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    guest = None if user else await get_or_create_guest(request, response, db)
    result = await db.execute(select(UploadedFileAudit).where(UploadedFileAudit.id == req.audit_id))
    audit = result.scalar_one_or_none()
    if not audit:
        raise HTTPException(status_code=404, detail="Upload audit not found")

    if user and audit.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    if not user and guest and audit.guest_id != guest.id:
        raise HTTPException(status_code=403, detail="Access denied")

    audit.column_mapping_json = json.dumps(req.column_mapping)
    audit.status = "ready"
    await db.commit()

    await _merge_file_into_known_records(
        db, Path(audit.stored_path), req.column_mapping, audit.filename,
        user_id=user.id if user else None,
        guest_id=guest.id if guest else None,
    )
    return {"status": "success", "message": "Column mapping updated and records re-indexed"}


# -------------------------------------------------------------
# Known Records Index Management (Strictly Per-User / Per-Guest)
# -------------------------------------------------------------
@router.get("/known-records/stats", response_model=KnownRecordsStats)
async def get_known_records_stats(
    request: Request,
    response: Response,
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    guest = None if user else await get_or_create_guest(request, response, db)
    cond = (KnownRecord.user_id == user.id) if user else (KnownRecord.guest_id == guest.id)

    total = await db.scalar(select(func.count(KnownRecord.id)).where(cond)) or 0
    city_res = await db.execute(select(KnownRecord.city, func.count(KnownRecord.id)).where(cond).group_by(KnownRecord.city))
    by_city = {str(c): count for c, count in city_res.all()}

    src_res = await db.execute(select(KnownRecord.source, func.count(KnownRecord.id)).where(cond).group_by(KnownRecord.source))
    by_source = {str(s): count for s, count in src_res.all()}

    return KnownRecordsStats(
        total_records=total,
        by_city=by_city,
        by_source=by_source,
        last_updated=datetime.utcnow(),
    )


@router.delete("/known-records")
async def clear_known_records(
    request: Request,
    response: Response,
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    guest = None if user else await get_or_create_guest(request, response, db)
    cond = (KnownRecord.user_id == user.id) if user else (KnownRecord.guest_id == guest.id)
    await db.execute(delete(KnownRecord).where(cond))
    await db.commit()
    return {"status": "success", "message": "Your known records index has been cleared."}


# -------------------------------------------------------------
# Pre-Run Confirmation
# -------------------------------------------------------------
@router.post("/jobs/preview", response_model=ConfirmationPreview)
async def preview_job_scope(
    req: CreateJobRequest,
    request: Request,
    response: Response,
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    guest = None if user else await get_or_create_guest(request, response, db)
    cond = (KnownRecord.user_id == user.id) if user else (KnownRecord.guest_id == guest.id)

    all_categories = list(req.categories)
    if req.custom_categories:
        all_categories.extend(req.custom_categories)

    known_count = await db.scalar(select(func.count(KnownRecord.id)).where(cond)) or 0

    return ConfirmationPreview(
        states_count=len(req.states),
        cities_count=len(req.cities),
        categories_count=len(all_categories),
        total_searches=len(req.cities) * len(all_categories),
        known_records_to_skip=known_count,
        selected_states=req.states,
        selected_cities=req.cities,
        selected_categories=all_categories,
    )


# -------------------------------------------------------------
# Job Execution & Live Controls (With Entitlements & Tenant Isolation)
# -------------------------------------------------------------
def _build_city_state_map() -> Dict[str, str]:
    mapping = {}
    for st in _load_india_locations():
        for c in st.get("cities", []):
            mapping[c["name"]] = st["name"]
    return mapping


async def _verify_job_ownership(job: Job, user: Optional[User], guest: Optional[Guest]):
    if user and user.role == "admin":
        return
    if user and job.user_id == user.id:
        return
    if not user and guest and job.guest_id == guest.id:
        return
    raise HTTPException(status_code=403, detail="You do not have permission to access this run.")


@router.post("/jobs", response_model=JobStatusResponse)
async def start_job(
    req: CreateJobRequest,
    request: Request,
    response: Response,
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    ip_h = hash_value(get_client_ip(request))
    guest = None if user else await get_or_create_guest(request, response, db)
    if not user:
        check_rate_limit(f"guest_run:{ip_h}", max_requests=20, window_seconds=3600)

    actor = user or guest
    filters_dict = req.filters.model_dump() if req.filters else {}

    allowed, msg, hint = await can_user_do(
        db, actor, "start_run",
        {"states": req.states, "cities": req.cities, "filters": filters_dict},
    )
    if not allowed:
        if hint and hint.get("action") == "guest_limit":
            db.add(AnalyticsEvent(guest_id=guest.id, event_name="guest_limit_hit", ip_hash=ip_h))
            await db.commit()
        raise HTTPException(status_code=403, detail={"message": msg, "upgrade_hint": hint})

    all_categories = list(req.categories)
    if req.custom_categories:
        for c in req.custom_categories:
            if c.strip() and c not in all_categories:
                all_categories.append(c.strip())

    # Determine plan caps and priority
    if user:
        plan, _ = await get_user_effective_plan(db, user)
        max_leads_cap = plan.max_leads_per_run
        priority = plan.priority_queue
        retention_days = plan.retention_days
    else:
        max_leads_cap = 50
        priority = 1
        retention_days = 30
        guest.runs_used += 1

    job_id = str(uuid.uuid4())[:12]
    job = Job(
        id=job_id,
        user_id=user.id if user else None,
        guest_id=guest.id if guest else None,
        status="pending",
        adapter_name=req.adapter,
        states_json=json.dumps(req.states),
        cities_json=json.dumps(req.cities),
        categories_json=json.dumps(all_categories),
        filters_json=json.dumps(filters_dict),
        remember_leads=req.remember_leads,
        priority=priority,
        max_leads_cap=max_leads_cap,
        expires_at=datetime.utcnow() + timedelta(days=retention_days),
        started_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )
    db.add(job)
    db.add(AnalyticsEvent(
        user_id=user.id if user else None,
        guest_id=guest.id if guest else None,
        event_name="run_started",
        properties_json=json.dumps({"states": req.states, "cities_count": len(req.cities), "filters": filters_dict}),
        ip_hash=ip_h,
    ))
    await db.commit()

    session = await job_runner_service.start_job(
        job,
        city_state_map=_build_city_state_map(),
        enable_enrichment=req.enable_enrichment,
    )
    return JobStatusResponse(**session.to_dict())


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    request: Request,
    response: Response,
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    guest = None if user else await get_or_create_guest(request, response, db)
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    await _verify_job_ownership(job, user, guest)

    session = job_runner_service.get_session(job_id)
    if session:
        return JobStatusResponse(**session.to_dict())

    return JobStatusResponse(
        id=job.id,
        status=job.status,
        adapter_name=job.adapter_name,
        total_found=job.total_found,
        filtered_out_count=job.filtered_out_count or 0,
        duplicates_skipped=job.duplicates_skipped,
        new_leads=job.new_leads,
        progress_pct=job.progress_pct,
        current_stage=job.current_stage,
        current_detail=job.current_detail,
        current_city=job.current_city,
        current_category=job.current_category,
        verification_needed=job.verification_needed,
        verification_message=job.verification_message,
        error_message=job.error_message,
        excel_file=job.excel_file,
        csv_file=job.csv_file,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


@router.get("/jobs/{job_id}/events")
async def stream_job_events(job_id: str):
    """Server-Sent Events (SSE) streaming live job progress and statistics."""
    session = job_runner_service.get_session(job_id)
    if not session:
        raise HTTPException(status_code=404, detail="Job session is not active")

    q = asyncio.Queue()
    session.event_queues.append(q)
    await q.put(session.to_dict())

    async def event_generator():
        try:
            while True:
                try:
                    data = await asyncio.wait_for(q.get(), timeout=12.0)
                    yield f"data: {json.dumps(data)}\n\n"
                    if data.get("status") in ("completed", "failed", "cancelled"):
                        break
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        finally:
            if q in session.event_queues:
                session.event_queues.remove(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.post("/jobs/{job_id}/pause")
async def pause_job(
    job_id: str,
    request: Request,
    response: Response,
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    guest = None if user else await get_or_create_guest(request, response, db)
    res = await db.execute(select(Job).where(Job.id == job_id))
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    await _verify_job_ownership(job, user, guest)

    if not await job_runner_service.pause_job(job_id):
        raise HTTPException(status_code=400, detail="Cannot pause job")
    return {"status": "success", "message": "Job paused"}


@router.post("/jobs/{job_id}/resume")
async def resume_job(
    job_id: str,
    request: Request,
    response: Response,
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    guest = None if user else await get_or_create_guest(request, response, db)
    res = await db.execute(select(Job).where(Job.id == job_id))
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    await _verify_job_ownership(job, user, guest)

    if not await job_runner_service.resume_job(job_id):
        raise HTTPException(status_code=400, detail="Cannot resume job")
    return {"status": "success", "message": "Job resumed"}


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    request: Request,
    response: Response,
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    guest = None if user else await get_or_create_guest(request, response, db)
    res = await db.execute(select(Job).where(Job.id == job_id))
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    await _verify_job_ownership(job, user, guest)

    if not await job_runner_service.cancel_job(job_id):
        raise HTTPException(status_code=400, detail="Cannot cancel job")
    return {"status": "success", "message": "Job cancelling. Partial Excel file will be prepared."}


@router.get("/jobs/{job_id}/signed-url")
async def get_signed_download_url(
    job_id: str,
    request: Request,
    response: Response,
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    guest = None if user else await get_or_create_guest(request, response, db)
    res = await db.execute(select(Job).where(Job.id == job_id))
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    await _verify_job_ownership(job, user, guest)
    token = sign_token({"job_id": job_id}, salt="download")
    return {"url": f"/api/jobs/{job_id}/download?token={token}", "expires_in_seconds": 900}


@router.get("/jobs/{job_id}/download")
async def download_job_excel(
    job_id: str,
    request: Request,
    response: Response,
    token: Optional[str] = None,
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if token:
        data = unsign_token(token, max_age_seconds=900, salt="download")
        if not data or data.get("job_id") != job_id:
            raise HTTPException(status_code=403, detail="Invalid or expired download link.")
    else:
        guest = None if user else await get_or_create_guest(request, response, db)
        await _verify_job_ownership(job, user, guest)

    excel_filename = job.excel_file
    if not excel_filename:
        session = job_runner_service.get_session(job_id)
        excel_filename = session.excel_file if session else None

    if not excel_filename:
        raise HTTPException(status_code=404, detail="Excel file not ready")

    file_path = settings.EXPORTS_DIR / excel_filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on server")

    return FileResponse(
        path=str(file_path),
        filename=excel_filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.get("/jobs/{job_id}/download-csv")
async def download_job_csv(
    job_id: str,
    request: Request,
    response: Response,
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    guest = None if user else await get_or_create_guest(request, response, db)
    actor = user or guest
    allowed, msg, hint = await can_user_do(db, actor, "csv_export")
    if not allowed:
        raise HTTPException(status_code=403, detail={"message": msg, "upgrade_hint": hint})

    res = await db.execute(select(Job).where(Job.id == job_id))
    job = res.scalar_one_or_none()
    if not job or not job.csv_file:
        raise HTTPException(status_code=404, detail="CSV file not ready")
    await _verify_job_ownership(job, user, guest)

    file_path = settings.EXPORTS_DIR / job.csv_file
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="CSV file not found")

    return FileResponse(path=str(file_path), filename=job.csv_file, media_type="text/csv")


# -------------------------------------------------------------
# History (Strictly Per-User / Per-Guest)
# -------------------------------------------------------------
@router.get("/history")
async def get_history(
    request: Request,
    response: Response,
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    guest = None if user else await get_or_create_guest(request, response, db)
    cond = (Job.user_id == user.id) if user else (Job.guest_id == guest.id)

    result = await db.execute(select(Job).where(cond).order_by(Job.created_at.desc()).limit(50))
    jobs = result.scalars().all()
    return [
        {
            "id": j.id,
            "status": j.status,
            "adapter_name": j.adapter_name,
            "states": json.loads(j.states_json) if j.states_json else ["Odisha"],
            "cities": json.loads(j.cities_json),
            "categories": json.loads(j.categories_json),
            "filters": json.loads(j.filters_json) if j.filters_json else {},
            "total_found": j.total_found,
            "filtered_out_count": j.filtered_out_count or 0,
            "duplicates_skipped": j.duplicates_skipped,
            "new_leads": j.new_leads,
            "excel_file": j.excel_file,
            "csv_file": j.csv_file,
            "started_at": j.started_at,
            "completed_at": j.completed_at,
        }
        for j in jobs
    ]
