import asyncio
import json
import logging
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, delete
import pandas as pd

from app.core.config import settings
from app.core.database import get_db
from app.models.entities import Job, KnownRecord, Preset, UploadedFileAudit
from app.schemas.lead import (
    LocationItem, CategoryItem, PresetItem, PresetCreate,
    CreateJobRequest, JobStatusResponse, FileAuditCard,
    ColumnMappingUpdate, KnownRecordsStats, ConfirmationPreview
)
from app.services.auditor import audit_file
from app.services.normalizer import clean_phone_number, normalize_text
from app.services.job_runner import job_runner_service

router = APIRouter(prefix="/api")
logger = logging.getLogger("leadharvest.api")

# -------------------------------------------------------------
# Configuration & Meta
# -------------------------------------------------------------
@router.get("/config/locations", response_model=List[LocationItem])
async def get_locations():
    path = settings.CONFIG_DIR / "odisha_locations.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Locations config not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@router.get("/config/categories", response_model=List[CategoryItem])
async def get_categories():
    path = settings.CONFIG_DIR / "categories.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Categories config not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# -------------------------------------------------------------
# Presets
# -------------------------------------------------------------
@router.get("/presets", response_model=List[PresetItem])
async def list_presets(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Preset).order_by(Preset.created_at.desc()))
    presets = result.scalars().all()
    return [
        PresetItem(
            id=p.id,
            name=p.name,
            cities=json.loads(p.cities_json),
            categories=json.loads(p.categories_json),
            created_at=p.created_at
        )
        for p in presets
    ]

@router.post("/presets", response_model=PresetItem)
async def create_preset(req: PresetCreate, db: AsyncSession = Depends(get_db)):
    preset_id = str(uuid.uuid4())[:8]
    preset = Preset(
        id=preset_id,
        name=req.name,
        cities_json=json.dumps(req.cities),
        categories_json=json.dumps(req.categories),
        created_at=datetime.utcnow()
    )
    db.add(preset)
    await db.commit()
    return PresetItem(
        id=preset.id,
        name=preset.name,
        cities=req.cities,
        categories=req.categories,
        created_at=preset.created_at
    )

# -------------------------------------------------------------
# Deduplication File Uploads & Audit
# -------------------------------------------------------------
@router.post("/uploads", response_model=List[FileAuditCard])
async def upload_dedupe_files(
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Accepts multiple .xlsx, .xls, .csv files at once.
    Audits each file and returns rich metrics cards.
    """
    results: List[FileAuditCard] = []

    for file in files:
        suffix = Path(file.filename).suffix.lower()
        if suffix not in [".xlsx", ".xls", ".csv"]:
            continue

        file_id = str(uuid.uuid4())
        safe_name = f"{file_id}_{Path(file.filename).name}"
        saved_path = settings.UPLOADS_DIR / safe_name

        content = await file.read()
        with open(saved_path, "wb") as f:
            f.write(content)

        audit_res = audit_file(saved_path)

        db_audit = UploadedFileAudit(
            id=file_id,
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
            uploaded_at=datetime.utcnow()
        )
        db.add(db_audit)
        await db.commit()

        # Also automatically merge valid records into Known Records index
        if audit_res["status"] == "ready":
            await _merge_file_into_known_records(db, saved_path, audit_res["column_mapping"], file.filename)

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
            uploaded_at=datetime.utcnow()
        ))

    return results

async def _merge_file_into_known_records(db: AsyncSession, file_path: Path, mapping: Dict[str, str], filename: str):
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
                phone_clean=phone_clean,
                phone_raw=phone_raw,
                business_name=name,
                normalized_name=normalize_text(name),
                normalized_address=normalize_text(addr),
                city=city,
                category=cat,
                source="upload",
                source_file=filename
            )
            db.add(rec)
        await db.commit()
    except Exception as e:
        logger.error(f"Error merging file into known records: {e}")

@router.post("/uploads/mapping")
async def update_column_mapping(req: ColumnMappingUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UploadedFileAudit).where(UploadedFileAudit.id == req.audit_id))
    audit = result.scalar_one_or_none()
    if not audit:
        raise HTTPException(status_code=404, detail="Upload audit not found")
    
    audit.column_mapping_json = json.dumps(req.column_mapping)
    audit.status = "ready"
    await db.commit()

    # Re-merge with new mapping
    await _merge_file_into_known_records(db, Path(audit.stored_path), req.column_mapping, audit.filename)
    return {"status": "success", "message": "Column mapping updated and records re-indexed"}

# -------------------------------------------------------------
# Known Records Index Management
# -------------------------------------------------------------
@router.get("/known-records/stats", response_model=KnownRecordsStats)
async def get_known_records_stats(db: AsyncSession = Depends(get_db)):
    total = await db.scalar(select(func.count(KnownRecord.id))) or 0
    
    # By city
    city_res = await db.execute(select(KnownRecord.city, func.count(KnownRecord.id)).group_by(KnownRecord.city))
    by_city = {str(c): count for c, count in city_res.all()}
    
    # By source
    src_res = await db.execute(select(KnownRecord.source, func.count(KnownRecord.id)).group_by(KnownRecord.source))
    by_source = {str(s): count for s, count in src_res.all()}

    return KnownRecordsStats(
        total_records=total,
        by_city=by_city,
        by_source=by_source,
        last_updated=datetime.utcnow()
    )

@router.delete("/known-records")
async def clear_known_records(db: AsyncSession = Depends(get_db)):
    await db.execute(delete(KnownRecord))
    await db.commit()
    return {"status": "success", "message": "All known records index cleared"}

# -------------------------------------------------------------
# Pre-Run Confirmation
# -------------------------------------------------------------
@router.post("/jobs/preview", response_model=ConfirmationPreview)
async def preview_job_scope(req: CreateJobRequest, db: AsyncSession = Depends(get_db)):
    all_categories = list(req.categories)
    if req.custom_categories:
        all_categories.extend(req.custom_categories)

    known_count = await db.scalar(select(func.count(KnownRecord.id))) or 0

    return ConfirmationPreview(
        cities_count=len(req.cities),
        categories_count=len(all_categories),
        known_records_to_skip=known_count,
        selected_cities=req.cities,
        selected_categories=all_categories
    )

# -------------------------------------------------------------
# Job Execution & Live Controls
# -------------------------------------------------------------
@router.post("/jobs", response_model=JobStatusResponse)
async def start_job(req: CreateJobRequest, db: AsyncSession = Depends(get_db)):
    all_categories = list(req.categories)
    if req.custom_categories:
        for c in req.custom_categories:
            if c.strip() and c not in all_categories:
                all_categories.append(c.strip())

    job_id = str(uuid.uuid4())[:12]
    job = Job(
        id=job_id,
        status="pending",
        adapter_name=req.adapter,
        cities_json=json.dumps(req.cities),
        categories_json=json.dumps(all_categories),
        remember_leads=req.remember_leads,
        started_at=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    db.add(job)
    await db.commit()

    # Launch background job runner
    session = await job_runner_service.start_job(job)
    return JobStatusResponse(**session.to_dict())

@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    session = job_runner_service.get_session(job_id)
    if session:
        return JobStatusResponse(**session.to_dict())
    
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        id=job.id,
        status=job.status,
        adapter_name=job.adapter_name,
        total_found=job.total_found,
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
        started_at=job.started_at,
        completed_at=job.completed_at
    )

@router.get("/jobs/{job_id}/events")
async def stream_job_events(job_id: str):
    """Server-Sent Events (SSE) streaming live job progress and statistics."""
    session = job_runner_service.get_session(job_id)
    if not session:
        raise HTTPException(status_code=404, detail="Job session is not active")

    q = asyncio.Queue()
    session.event_queues.append(q)

    # Send initial state immediately
    await q.put(session.to_dict())

    async def event_generator():
        try:
            while True:
                try:
                    data = await asyncio.wait_for(q.get(), timeout=12.0)
                    yield f"data: {json.dumps(data)}\n\n"
                    if data.get("status") in ["completed", "failed", "cancelled"]:
                        break
                except asyncio.TimeoutError:
                    # Keep-alive heartbeat
                    yield f": ping\n\n"
        finally:
            if q in session.event_queues:
                session.event_queues.remove(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.post("/jobs/{job_id}/pause")
async def pause_job(job_id: str):
    success = await job_runner_service.pause_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot pause job")
    return {"status": "success", "message": "Job paused"}

@router.post("/jobs/{job_id}/resume")
async def resume_job(job_id: str):
    success = await job_runner_service.resume_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot resume job")
    return {"status": "success", "message": "Job resumed"}

@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    success = await job_runner_service.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot cancel job")
    return {"status": "success", "message": "Job cancelling. Partial Excel file will be prepared."}

@router.get("/jobs/{job_id}/download")
async def download_job_excel(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job or not job.excel_file:
        session = job_runner_service.get_session(job_id)
        if session and session.excel_file:
            excel_filename = session.excel_file
        else:
            raise HTTPException(status_code=404, detail="Excel file not ready or job not found")
    else:
        excel_filename = job.excel_file

    file_path = settings.EXPORTS_DIR / excel_filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on server")

    return FileResponse(
        path=str(file_path),
        filename=excel_filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# -------------------------------------------------------------
# History
# -------------------------------------------------------------
@router.get("/history")
async def get_history(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).order_by(Job.created_at.desc()).limit(50))
    jobs = result.scalars().all()
    return [
        {
            "id": j.id,
            "status": j.status,
            "adapter_name": j.adapter_name,
            "cities": json.loads(j.cities_json),
            "categories": json.loads(j.categories_json),
            "total_found": j.total_found,
            "duplicates_skipped": j.duplicates_skipped,
            "new_leads": j.new_leads,
            "excel_file": j.excel_file,
            "started_at": j.started_at,
            "completed_at": j.completed_at
        }
        for j in jobs
    ]
