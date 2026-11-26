from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime
from app.core.database import Base

class KnownRecord(Base):
    """Index of already collected or uploaded leads for persistent deduplication."""
    __tablename__ = "known_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone_clean = Column(String(20), index=True, nullable=True) # Normalized 10-digit Indian phone
    phone_raw = Column(String(100), nullable=True)
    alt_phone_clean = Column(String(20), index=True, nullable=True)
    business_name = Column(String(255), nullable=False)
    normalized_name = Column(String(255), index=True, nullable=False)
    normalized_address = Column(String(500), nullable=True)
    city = Column(String(100), index=True, nullable=False)
    district = Column(String(100), nullable=True)
    category = Column(String(150), nullable=True)
    source = Column(String(100), default="upload") # "upload" | "harvest_job"
    source_file = Column(String(255), nullable=True)
    run_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Job(Base):
    """Background scraping job state and progress tracker."""
    __tablename__ = "jobs"

    id = Column(String(64), primary_key=True)
    status = Column(String(32), default="pending", index=True) # pending, running, paused, cancelled, completed, failed
    adapter_name = Column(String(32), default="mock") # mock | justdial
    cities_json = Column(Text, nullable=False) # JSON list of cities
    categories_json = Column(Text, nullable=False) # JSON list of categories
    remember_leads = Column(Boolean, default=True) # Add newly collected leads to KnownRecord
    
    total_found = Column(Integer, default=0)
    duplicates_skipped = Column(Integer, default=0)
    new_leads = Column(Integer, default=0)
    progress_pct = Column(Float, default=0.0)
    
    current_stage = Column(String(64), default="preparing")
    current_detail = Column(String(255), default="Initializing job...")
    current_city = Column(String(100), nullable=True)
    current_category = Column(String(150), nullable=True)
    
    error_message = Column(Text, nullable=True)
    verification_needed = Column(Boolean, default=False) # Verification/Captcha pause flag
    verification_message = Column(Text, nullable=True)
    
    excel_file = Column(String(255), nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class JobLead(Base):
    """Individual lead record collected during a job."""
    __tablename__ = "job_leads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(64), index=True, nullable=False)
    business_name = Column(String(255), nullable=False)
    category = Column(String(150), nullable=True)
    phone = Column(String(100), nullable=True)
    phone_clean = Column(String(20), nullable=True)
    alt_phone = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    area = Column(String(150), nullable=True)
    city = Column(String(100), nullable=False)
    district = Column(String(100), nullable=True)
    pincode = Column(String(20), nullable=True)
    rating = Column(String(20), nullable=True)
    review_count = Column(String(20), nullable=True)
    website = Column(String(500), nullable=True)
    listing_url = Column(String(500), nullable=True)
    source = Column(String(100), default="justdial")
    collected_at = Column(DateTime, default=datetime.utcnow)
    
    is_duplicate = Column(Boolean, default=False)
    duplicate_rule = Column(String(100), nullable=True) # "phone_exact", "name_city_exact", "fuzzy_name_address", "within_run"
    duplicate_source = Column(String(255), nullable=True) # Source file or previous run ID

class Preset(Base):
    """Saved city and category presets for one-click re-use."""
    __tablename__ = "presets"

    id = Column(String(64), primary_key=True)
    name = Column(String(150), nullable=False)
    cities_json = Column(Text, nullable=False)
    categories_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class UploadedFileAudit(Base):
    """Metadata and audit report for an uploaded deduplication file."""
    __tablename__ = "uploaded_file_audits"

    id = Column(String(64), primary_key=True)
    filename = Column(String(255), nullable=False)
    stored_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, default=0)
    total_rows = Column(Integer, default=0)
    valid_rows = Column(Integer, default=0)
    blank_rows = Column(Integer, default=0)
    invalid_phone_rows = Column(Integer, default=0)
    duplicate_rows = Column(Integer, default=0)
    column_mapping_json = Column(Text, nullable=True)
    detected_columns_json = Column(Text, nullable=True)
    status = Column(String(32), default="ready") # "ready" | "needs_attention" | "merged"
    uploaded_at = Column(DateTime, default=datetime.utcnow)
