from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, Index
)
from app.core.database import Base


# ---------------------------------------------------------------------------
# Users, Sessions, Guests
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True)
    name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # Null for OAuth-only users
    phone = Column(String(32), nullable=True)
    business_type = Column(String(100), nullable=True)
    role = Column(String(32), default="user", nullable=False)  # user | admin | support
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String(128), nullable=True, index=True)
    reset_token = Column(String(128), nullable=True, index=True)
    reset_token_expires = Column(DateTime, nullable=True)
    google_id = Column(String(128), nullable=True, unique=True)
    totp_secret = Column(String(64), nullable=True)
    totp_enabled = Column(Boolean, default=False, nullable=False)
    is_suspended = Column(Boolean, default=False, nullable=False)
    marketing_unsubscribed = Column(Boolean, default=False, nullable=False)
    terms_accepted_at = Column(DateTime, nullable=True)
    gstin = Column(String(32), nullable=True)
    home_state = Column(String(100), nullable=True, index=True)
    home_state_source = Column(String(32), nullable=True)  # auto_detected | chosen | corrected | admin_set | migrated
    home_state_locked_at = Column(DateTime, nullable=True)
    home_state_corrected = Column(Boolean, default=False, nullable=False)
    location_unverified = Column(Boolean, default=False, nullable=False)
    detection_confidence = Column(String(32), nullable=True)  # high | medium | low | none
    last_change_request_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_active_at = Column(DateTime, default=datetime.utcnow)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    refresh_token_hash = Column(String(128), nullable=False)
    user_agent_hash = Column(String(128), nullable=True)
    ip_hash = Column(String(128), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Guest(Base):
    __tablename__ = "guests"

    id = Column(String(64), primary_key=True)
    fingerprint_hash = Column(String(128), index=True, nullable=False)
    ip_hash = Column(String(128), index=True, nullable=False)
    ua_hash = Column(String(128), nullable=True)
    runs_used = Column(Integer, default=0, nullable=False)
    migrated_to_user_id = Column(String(64), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    home_state = Column(String(100), nullable=True, index=True)
    home_state_source = Column(String(32), nullable=True)
    home_state_locked_at = Column(DateTime, nullable=True)
    location_unverified = Column(Boolean, default=False, nullable=False)
    detection_confidence = Column(String(32), nullable=True)
    country_code = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ---------------------------------------------------------------------------
# Plans, Subscriptions, Payments, Invoices, Coupons, Webhooks
# ---------------------------------------------------------------------------
class Plan(Base):
    __tablename__ = "plans"

    id = Column(String(32), primary_key=True)  # free | starter | pro | agency
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    price_monthly_inr = Column(Integer, default=0, nullable=False)
    price_yearly_inr = Column(Integer, default=0, nullable=False)
    max_states = Column(Integer, default=1, nullable=False)  # 1 = Odisha only; 36 = All India
    max_runs_per_day = Column(Integer, default=2, nullable=False)
    max_leads_per_run = Column(Integer, default=100, nullable=False)
    max_leads_per_month = Column(Integer, default=300, nullable=False)
    retention_days = Column(Integer, default=30, nullable=False)
    allow_advanced_filters = Column(Boolean, default=False, nullable=False)
    allow_all_filters = Column(Boolean, default=False, nullable=False)
    allow_presets = Column(Boolean, default=False, nullable=False)
    allow_csv_export = Column(Boolean, default=False, nullable=False)
    allow_webhook_export = Column(Boolean, default=False, nullable=False)
    team_seats = Column(Integer, default=1, nullable=False)
    priority_queue = Column(Integer, default=1, nullable=False)  # higher = faster priority
    is_popular = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    plan_id = Column(String(32), ForeignKey("plans.id"), nullable=False, default="free")
    billing_cycle = Column(String(16), default="monthly", nullable=False)  # monthly | yearly
    status = Column(String(32), default="active", index=True, nullable=False)  # active | past_due | cancelled | paused
    provider = Column(String(32), default="simulated", nullable=False)  # razorpay | simulated | manual
    provider_subscription_id = Column(String(128), nullable=True, index=True)
    current_period_start = Column(DateTime, default=datetime.utcnow)
    current_period_end = Column(DateTime, nullable=True)
    grace_until = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, default=False, nullable=False)
    comp_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    subscription_id = Column(String(64), ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True)
    plan_id = Column(String(32), nullable=True)
    amount_inr = Column(Integer, nullable=False)
    gst_amount_inr = Column(Integer, default=0, nullable=False)
    discount_inr = Column(Integer, default=0, nullable=False)
    coupon_code = Column(String(64), nullable=True)
    currency = Column(String(10), default="INR", nullable=False)
    status = Column(String(32), default="captured", index=True, nullable=False)  # captured | failed | refunded
    provider = Column(String(32), default="simulated", nullable=False)
    provider_payment_id = Column(String(128), nullable=True, index=True)
    failure_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String(64), primary_key=True)
    invoice_number = Column(String(64), unique=True, nullable=False)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    payment_id = Column(String(64), ForeignKey("payments.id", ondelete="SET NULL"), nullable=True)
    plan_name = Column(String(100), nullable=False)
    subtotal_inr = Column(Integer, nullable=False)
    gst_amount_inr = Column(Integer, default=0, nullable=False)
    total_inr = Column(Integer, nullable=False)
    customer_name = Column(String(150), nullable=False)
    customer_email = Column(String(255), nullable=False)
    customer_gstin = Column(String(32), nullable=True)
    pdf_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(String(64), primary_key=True)
    code = Column(String(64), unique=True, index=True, nullable=False)
    discount_type = Column(String(16), default="percent", nullable=False)  # percent | flat
    discount_value = Column(Integer, nullable=False)
    max_uses = Column(Integer, default=100, nullable=False)
    uses_count = Column(Integer, default=0, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(String(64), primary_key=True)
    provider = Column(String(32), nullable=False)
    event_id = Column(String(128), unique=True, index=True, nullable=False)
    event_type = Column(String(64), nullable=False)
    payload_json = Column(Text, nullable=False)
    status = Column(String(32), default="processed", nullable=False)  # processed | failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


# ---------------------------------------------------------------------------
# Core Lead Harvesting Entities (Multi-tenant scoped by user_id / guest_id)
# ---------------------------------------------------------------------------
class KnownRecord(Base):
    """Index of already collected or uploaded leads for persistent per-user deduplication."""
    __tablename__ = "known_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True)
    guest_id = Column(String(64), index=True, nullable=True)
    phone_clean = Column(String(20), index=True, nullable=True)
    phone_raw = Column(String(100), nullable=True)
    alt_phone_clean = Column(String(20), index=True, nullable=True)
    business_name = Column(String(255), nullable=False)
    normalized_name = Column(String(255), index=True, nullable=False)
    normalized_address = Column(String(500), nullable=True)
    city = Column(String(100), index=True, nullable=False)
    state = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    category = Column(String(150), nullable=True)
    source = Column(String(100), default="upload")
    source_file = Column(String(255), nullable=True)
    run_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class Job(Base):
    """Background scraping job state and progress tracker."""
    __tablename__ = "jobs"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True)
    guest_id = Column(String(64), index=True, nullable=True)
    status = Column(String(32), default="pending", index=True)
    adapter_name = Column(String(32), default="mock")
    states_json = Column(Text, nullable=True)  # JSON list of Indian states
    cities_json = Column(Text, nullable=False)
    categories_json = Column(Text, nullable=False)
    filters_json = Column(Text, nullable=True)  # Smart Lead Filters JSON
    remember_leads = Column(Boolean, default=True)
    priority = Column(Integer, default=1)
    max_leads_cap = Column(Integer, default=100)

    total_found = Column(Integer, default=0)
    filtered_out_count = Column(Integer, default=0)
    duplicates_skipped = Column(Integer, default=0)
    new_leads = Column(Integer, default=0)
    progress_pct = Column(Float, default=0.0)

    current_stage = Column(String(64), default="preparing")
    current_detail = Column(String(255), default="Initializing job...")
    current_city = Column(String(100), nullable=True)
    current_category = Column(String(150), nullable=True)

    error_message = Column(Text, nullable=True)
    verification_needed = Column(Boolean, default=False)
    verification_message = Column(Text, nullable=True)

    excel_file = Column(String(255), nullable=True)
    csv_file = Column(String(255), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, default=0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
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
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    area = Column(String(150), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    pincode = Column(String(20), nullable=True)
    rating = Column(String(20), nullable=True)
    review_count = Column(String(20), nullable=True)
    website = Column(String(500), nullable=True)
    has_website = Column(Boolean, default=False)
    mobile_available = Column(Boolean, default=False)
    has_social_only = Column(Boolean, default=False)
    social_url = Column(String(500), nullable=True)
    is_verified_listing = Column(Boolean, default=False)
    is_chain = Column(Boolean, default=False)
    opportunity_score = Column(Integer, default=0)
    lead_tag = Column(String(100), nullable=True)
    whatsapp_link = Column(String(500), nullable=True)
    listing_url = Column(String(500), nullable=True)
    source = Column(String(100), default="justdial")
    collected_at = Column(DateTime, default=datetime.utcnow)

    is_duplicate = Column(Boolean, default=False)
    duplicate_rule = Column(String(100), nullable=True)
    duplicate_source = Column(String(255), nullable=True)


class Preset(Base):
    """Saved city, category, and smart filter presets."""
    __tablename__ = "presets"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True)
    name = Column(String(150), nullable=False)
    states_json = Column(Text, nullable=True)
    cities_json = Column(Text, nullable=False)
    categories_json = Column(Text, nullable=False)
    filters_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class UploadedFileAudit(Base):
    """Metadata and audit report for an uploaded deduplication file."""
    __tablename__ = "uploaded_file_audits"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True)
    guest_id = Column(String(64), index=True, nullable=True)
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
    status = Column(String(32), default="ready")
    uploaded_at = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# First-Party Analytics, Audit Logs, Feature Flags, CMS Settings
# ---------------------------------------------------------------------------
class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), index=True, nullable=True)
    user_id = Column(String(64), index=True, nullable=True)
    guest_id = Column(String(64), index=True, nullable=True)
    event_name = Column(String(64), index=True, nullable=False)
    properties_json = Column(Text, nullable=True)
    ip_hash = Column(String(128), nullable=True)
    country = Column(String(64), default="India")
    state = Column(String(64), nullable=True)
    device_type = Column(String(32), default="desktop")
    referrer = Column(String(500), nullable=True)
    utm_source = Column(String(100), nullable=True)
    utm_medium = Column(String(100), nullable=True)
    utm_campaign = Column(String(100), nullable=True)
    consent_given = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class PageView(Base):
    __tablename__ = "page_views"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), index=True, nullable=True)
    user_id = Column(String(64), index=True, nullable=True)
    guest_id = Column(String(64), index=True, nullable=True)
    path = Column(String(255), index=True, nullable=False)
    referrer = Column(String(500), nullable=True)
    utm_source = Column(String(100), nullable=True)
    device_type = Column(String(32), default="desktop")
    ip_hash = Column(String(128), nullable=True)
    consent_given = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    actor_user_id = Column(String(64), index=True, nullable=True)
    actor_email = Column(String(255), nullable=True)
    action = Column(String(100), index=True, nullable=False)
    target_type = Column(String(64), nullable=True)
    target_id = Column(String(64), nullable=True)
    details_json = Column(Text, nullable=True)
    ip_hash = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class FeatureFlag(Base):
    __tablename__ = "feature_flags"

    key = Column(String(64), primary_key=True)
    enabled = Column(Boolean, default=True, nullable=False)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AppSetting(Base):
    __tablename__ = "app_settings"

    key = Column(String(64), primary_key=True)
    value = Column(Text, nullable=False)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ---------------------------------------------------------------------------
# Blog & SEO Management
# ---------------------------------------------------------------------------
class BlogPost(Base):
    __tablename__ = "blog_posts"

    id = Column(String(64), primary_key=True)
    slug = Column(String(200), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(String(400), nullable=True)
    canonical_url = Column(String(500), nullable=True)
    og_image = Column(String(500), nullable=True)
    focus_keyword = Column(String(150), nullable=True)
    category = Column(String(100), default="Lead Generation", index=True)
    tags_json = Column(Text, nullable=True)
    excerpt = Column(Text, nullable=True)
    content_md = Column(Text, nullable=False)
    faqs_json = Column(Text, nullable=True)
    author_name = Column(String(120), default="Amarjeet S.")
    author_bio = Column(String(400), default="Founder of LeadHarvest India & B2B Web Systems Architect.")
    status = Column(String(32), default="published", index=True)  # draft | scheduled | published
    published_at = Column(DateTime, default=datetime.utcnow, index=True)
    scheduled_for = Column(DateTime, nullable=True)
    views_count = Column(Integer, default=0)
    cta_clicks_count = Column(Integer, default=0)
    signups_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SeoKeywordTrack(Base):
    __tablename__ = "seo_keyword_tracks"

    id = Column(String(64), primary_key=True)
    keyword = Column(String(200), nullable=False)
    target_url = Column(String(300), nullable=False)
    current_position = Column(Float, default=0.0)
    previous_position = Column(Float, default=0.0)
    clicks = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    ctr = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SiteAuditRun(Base):
    __tablename__ = "site_audit_runs"

    id = Column(String(64), primary_key=True)
    health_score = Column(Integer, default=100)
    pages_scanned = Column(Integer, default=0)
    issues_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# Hot Leads CRM & Buying-Signal Pipeline
# ---------------------------------------------------------------------------
class HotLead(Base):
    __tablename__ = "hot_leads"

    id = Column(String(64), primary_key=True)
    source_type = Column(String(32), index=True, nullable=False)  # inbound | public_request | signal
    source_name = Column(String(100), index=True, nullable=False)  # website_quote_form | whatsapp_cta | google_ads_webhook | csv_import | rss_feed | leadharvest_signal
    source_url = Column(String(500), nullable=True)
    terms_note = Column(String(500), nullable=True)

    name = Column(String(150), nullable=True)
    business_name = Column(String(255), index=True, nullable=False)
    phone = Column(String(50), nullable=True)
    phone_clean = Column(String(20), index=True, nullable=True)
    email = Column(String(255), index=True, nullable=True)
    business_type = Column(String(150), index=True, nullable=True)
    city = Column(String(100), index=True, nullable=True)
    state = Column(String(100), index=True, nullable=True)
    website = Column(String(500), nullable=True)
    budget_range = Column(String(100), nullable=True)
    timeline = Column(String(100), nullable=True)
    notes_summary = Column(Text, nullable=True)

    # UTM & Attribution
    utm_source = Column(String(100), nullable=True)
    utm_medium = Column(String(100), nullable=True)
    utm_campaign = Column(String(150), nullable=True)
    utm_term = Column(String(150), nullable=True)
    utm_content = Column(String(150), nullable=True)
    landing_page = Column(String(300), nullable=True)

    # Scoring & Signals
    score = Column(Integer, default=0, index=True, nullable=False)
    temperature = Column(String(16), default="Cold", index=True, nullable=False)  # Hot | Warm | Cold
    score_breakdown_json = Column(Text, nullable=True)
    signals_json = Column(Text, nullable=True)
    website_health_json = Column(Text, nullable=True)
    rating = Column(Float, nullable=True)
    review_count = Column(Integer, nullable=True)

    # Pipeline & Reminders
    stage = Column(String(32), default="New", index=True, nullable=False)  # New | Contacted | Meeting booked | Proposal sent | Negotiation | Won | Lost
    deal_value_inr = Column(Integer, default=0, nullable=False)
    expected_close_date = Column(DateTime, nullable=True)
    lost_reason = Column(String(255), nullable=True)
    owner_name = Column(String(120), default="Amar (Owner)", nullable=False)
    next_followup_at = Column(DateTime, nullable=True, index=True)
    first_contacted_at = Column(DateTime, nullable=True)

    # Compliance & Safety
    consent_given = Column(Boolean, default=False, nullable=False)
    consent_record = Column(Text, nullable=True)
    do_not_contact = Column(Boolean, default=False, index=True, nullable=False)
    dnc_reason = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class HotLeadActivity(Base):
    __tablename__ = "hot_lead_activities"

    id = Column(String(64), primary_key=True)
    lead_id = Column(String(64), ForeignKey("hot_leads.id", ondelete="CASCADE"), index=True, nullable=False)
    activity_type = Column(String(32), nullable=False)  # note | task | stage_change | health_check | email | whatsapp | proposal | system
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=True)
    due_at = Column(DateTime, nullable=True, index=True)
    completed = Column(Boolean, default=False, nullable=False)
    actor_email = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class HotLeadAttachment(Base):
    __tablename__ = "hot_lead_attachments"

    id = Column(String(64), primary_key=True)
    lead_id = Column(String(64), ForeignKey("hot_leads.id", ondelete="CASCADE"), index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=True)
    size_bytes = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class IntentSourceConfig(Base):
    __tablename__ = "intent_sources"

    id = Column(String(64), primary_key=True)
    name = Column(String(150), nullable=False)
    source_kind = Column(String(32), nullable=False)  # rss | official_api | email_alert | manual
    endpoint_or_query = Column(String(500), nullable=True)
    terms_note = Column(String(500), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_synced_at = Column(DateTime, nullable=True)
    leads_imported = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class DoNotContactEntry(Base):
    __tablename__ = "do_not_contact_list"

    id = Column(String(64), primary_key=True)
    phone_clean = Column(String(20), index=True, nullable=True)
    email = Column(String(255), index=True, nullable=True)
    reason = Column(String(255), nullable=False)
    source = Column(String(64), default="admin", nullable=False)  # opt_out | dnd | admin
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


# ---------------------------------------------------------------------------
# Home State Free Access Model
# ---------------------------------------------------------------------------
class StateChangeRequest(Base):
    __tablename__ = "state_change_requests"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    from_state = Column(String(100), nullable=True)
    to_state = Column(String(100), nullable=False)
    reason = Column(String(500), nullable=False)
    status = Column(String(32), default="pending", index=True, nullable=False)  # pending | approved | rejected
    auto_approved = Column(Boolean, default=False, nullable=False)
    reviewed_by = Column(String(255), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class UserExtraState(Base):
    __tablename__ = "user_extra_states"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    state_name = Column(String(100), nullable=False)
    granted_by = Column(String(32), default="starter_choice", nullable=False)  # starter_choice | admin_grant
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GeoDetectionLog(Base):
    """Stores only hashed IP, detected state/country, and timestamp — never raw IP."""
    __tablename__ = "geo_detection_log"

    id = Column(String(64), primary_key=True)
    actor_type = Column(String(16), nullable=False)  # guest | user
    actor_id = Column(String(64), index=True, nullable=False)
    ip_hash = Column(String(128), index=True, nullable=False)
    detected_state = Column(String(100), nullable=True)
    country_code = Column(String(10), nullable=True)
    is_vpn_or_proxy = Column(Boolean, default=False, nullable=False)
    provider = Column(String(64), nullable=False)
    confidence = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


# ---------------------------------------------------------------------------
# State-Wise SEO Rollout, Quality Gate, Inventory & A/B Tests
# ---------------------------------------------------------------------------
class StateSeoSetting(Base):
    __tablename__ = "state_seo_settings"

    state_slug = Column(String(100), primary_key=True)
    state_name = Column(String(100), nullable=False)
    rollout_wave = Column(Integer, default=1, nullable=False)  # 1 | 2 | 3 | 4
    is_published = Column(Boolean, default=True, nullable=False)
    daily_publish_cap = Column(Integer, default=50, nullable=False)
    min_word_count = Column(Integer, default=600, nullable=False)
    min_data_volume = Column(Integer, default=20, nullable=False)
    translation_reviewed_hi = Column(Boolean, default=False, nullable=False)
    translation_reviewed_or = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StateAbExperiment(Base):
    __tablename__ = "state_ab_experiments"

    id = Column(String(64), primary_key=True)
    state_slug = Column(String(100), index=True, nullable=False)
    variant = Column(String(16), nullable=False)  # A | B
    headline = Column(String(255), nullable=False)
    cta_text = Column(String(100), nullable=False)
    views = Column(Integer, default=0, nullable=False)
    conversions = Column(Integer, default=0, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
