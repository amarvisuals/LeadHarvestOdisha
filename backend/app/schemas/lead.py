from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class LocationItem(BaseModel):
    id: str
    name: str
    district: str
    tier: str
    pincode_prefix: str

class CategoryItem(BaseModel):
    id: str
    name: str
    keywords: List[str]

class PresetItem(BaseModel):
    id: str
    name: str
    cities: List[str]
    categories: List[str]
    created_at: datetime

class PresetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    cities: List[str]
    categories: List[str]

class CreateJobRequest(BaseModel):
    cities: List[str] = Field(..., min_length=1, description="Selected Odisha city names or IDs")
    categories: List[str] = Field(..., min_length=1, description="Selected business categories")
    adapter: str = Field(default="mock", description="'mock' for instant reliable demo/testing, 'justdial' for live")
    remember_leads: bool = Field(default=True, description="Save collected leads to persistent Known Records")
    custom_categories: Optional[List[str]] = Field(default=None, description="Custom categories added by client")
    max_scrolls: int = Field(default=4, ge=1, le=10)

class JobStatusResponse(BaseModel):
    id: str
    status: str # pending, running, paused, cancelled, completed, failed
    adapter_name: str
    total_found: int
    duplicates_skipped: int
    new_leads: int
    progress_pct: float
    current_stage: str # preparing, searching, collecting, filtering, creating_file, almost_done, success, paused, cancelled, failed
    current_detail: str
    current_city: Optional[str] = None
    current_category: Optional[str] = None
    verification_needed: bool = False
    verification_message: Optional[str] = None
    error_message: Optional[str] = None
    excel_file: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    elapsed_seconds: Optional[int] = 0
    estimated_remaining_seconds: Optional[int] = 0

class LeadRecord(BaseModel):
    id: Optional[int] = None
    business_name: str
    category: Optional[str] = None
    phone: Optional[str] = None
    alt_phone: Optional[str] = None
    address: Optional[str] = None
    area: Optional[str] = None
    city: str
    district: Optional[str] = None
    pincode: Optional[str] = None
    rating: Optional[str] = None
    review_count: Optional[str] = None
    website: Optional[str] = None
    listing_url: Optional[str] = None
    source: str = "justdial"
    collected_at: Optional[datetime] = None
    is_duplicate: bool = False
    duplicate_rule: Optional[str] = None
    duplicate_source: Optional[str] = None

class FileAuditCard(BaseModel):
    id: str
    filename: str
    file_size_bytes: int
    total_rows: int
    valid_rows: int
    blank_rows: int
    invalid_phone_rows: int
    duplicate_rows: int
    column_mapping: Dict[str, str] # e.g. {"phone": "Mobile", "business_name": "Company"}
    detected_columns: List[str]
    sample_rows: List[Dict[str, Any]]
    status: str # "ready" | "needs_attention"
    uploaded_at: datetime

class ColumnMappingUpdate(BaseModel):
    audit_id: str
    column_mapping: Dict[str, str]

class KnownRecordsStats(BaseModel):
    total_records: int
    by_city: Dict[str, int]
    by_source: Dict[str, int]
    last_updated: Optional[datetime] = None

class ConfirmationPreview(BaseModel):
    cities_count: int
    categories_count: int
    known_records_to_skip: int
    selected_cities: List[str]
    selected_categories: List[str]
