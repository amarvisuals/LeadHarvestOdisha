from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class LocationItem(BaseModel):
    id: str
    name: str
    district: str
    tier: str
    pincode_prefix: Optional[str] = None


class StateItem(BaseModel):
    id: str
    name: str
    type: str
    cities: List[LocationItem]


class CategoryItem(BaseModel):
    id: str
    name: str
    group: Optional[str] = "General"
    keywords: List[str]


class SmartFilters(BaseModel):
    no_website: bool = False
    has_website: bool = False
    mobile_only: bool = False
    has_email: bool = False
    verified_only: bool = False
    has_social_only: bool = False
    exclude_chains: bool = False
    min_rating: Optional[float] = Field(default=None, ge=0.0, le=5.0)
    max_rating: Optional[float] = Field(default=None, ge=0.0, le=5.0)
    min_reviews: Optional[int] = Field(default=None, ge=0)
    max_reviews: Optional[int] = Field(default=None, ge=0)
    min_opportunity_score: Optional[int] = Field(default=None, ge=0, le=100)


class PresetItem(BaseModel):
    id: str
    name: str
    states: List[str] = ["Odisha"]
    cities: List[str]
    categories: List[str]
    filters: Optional[Dict[str, Any]] = None
    created_at: datetime


class PresetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    states: List[str] = ["Odisha"]
    cities: List[str]
    categories: List[str]
    filters: Optional[SmartFilters] = None


class CreateJobRequest(BaseModel):
    states: List[str] = Field(default=["Odisha"], min_length=1)
    cities: List[str] = Field(..., min_length=1, description="Selected Indian city names")
    categories: List[str] = Field(..., min_length=1, description="Selected business categories")
    adapter: str = Field(default="mock", description="'mock' for instant demo/testing, 'justdial' for live")
    remember_leads: bool = Field(default=True, description="Save collected leads to persistent per-user Known Records")
    custom_categories: Optional[List[str]] = None
    filters: Optional[SmartFilters] = None
    enable_enrichment: bool = False
    max_scrolls: int = Field(default=4, ge=1, le=10)


class JobStatusResponse(BaseModel):
    id: str
    status: str
    adapter_name: str
    total_found: int
    filtered_out_count: int = 0
    duplicates_skipped: int
    new_leads: int
    progress_pct: float
    current_stage: str
    current_detail: str
    current_city: Optional[str] = None
    current_category: Optional[str] = None
    verification_needed: bool = False
    verification_message: Optional[str] = None
    error_message: Optional[str] = None
    excel_file: Optional[str] = None
    csv_file: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    elapsed_seconds: Optional[int] = 0
    estimated_remaining_seconds: Optional[int] = 0


class FileAuditCard(BaseModel):
    id: str
    filename: str
    file_size_bytes: int
    total_rows: int
    valid_rows: int
    blank_rows: int
    invalid_phone_rows: int
    duplicate_rows: int
    column_mapping: Dict[str, str]
    detected_columns: List[str]
    sample_rows: List[Dict[str, Any]]
    status: str
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
    states_count: int
    cities_count: int
    categories_count: int
    total_searches: int
    known_records_to_skip: int
    selected_states: List[str]
    selected_cities: List[str]
    selected_categories: List[str]
