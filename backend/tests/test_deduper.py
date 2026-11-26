import pytest
from app.services.deduper import DeduplicationEngine

@pytest.fixture
def sample_known_records():
    return [
        {
            "phone_clean": "9861012345",
            "business_name": "Utkal Sweets & Bakery",
            "address": "Plot 12, Saheed Nagar, Bhubaneswar",
            "city": "Bhubaneswar",
            "source_file": "existing_clients.xlsx"
        },
        {
            "phone_clean": "9437099888",
            "business_name": "Kalinga Hospital Clinic",
            "address": "CDA Sector 9, Cuttack",
            "city": "Cuttack",
            "source_file": "past_database"
        }
    ]

def test_deduper_rule_1_phone_match(sample_known_records):
    engine = DeduplicationEngine(sample_known_records)
    # Candidate with different name but identical phone
    candidate = {
        "phone": "+91 98610 12345",
        "business_name": "Utkal Confectionery",
        "city": "Bhubaneswar",
        "address": "Near Station, Bhubaneswar"
    }
    is_dupe, rule, source = engine.check_duplicate(candidate)
    assert is_dupe is True
    assert "Rule 1" in rule
    assert "existing_clients.xlsx" in source

def test_deduper_rule_2_name_city_exact_match(sample_known_records):
    engine = DeduplicationEngine(sample_known_records)
    # Different phone, but exact business name and city
    candidate = {
        "phone": "+91 70081 23456",
        "business_name": "Utkal Sweets & Bakery",
        "city": "Bhubaneswar",
        "address": "Some other branch address"
    }
    is_dupe, rule, source = engine.check_duplicate(candidate)
    assert is_dupe is True
    assert "Rule 2" in rule

def test_deduper_rule_3_fuzzy_name_address_match(sample_known_records):
    engine = DeduplicationEngine(sample_known_records)
    # Slightly altered spelling and composite address
    candidate = {
        "phone": "+91 82499 99999", # Different phone
        "business_name": "Kalinga Hospital & Clinics",
        "city": "Cuttack",
        "address": "CDA Sector 9 Cuttack Odisha"
    }
    is_dupe, rule, source = engine.check_duplicate(candidate)
    assert is_dupe is True
    assert "Rule 3" in rule

def test_deduper_non_duplicate(sample_known_records):
    engine = DeduplicationEngine(sample_known_records)
    candidate = {
        "phone": "+91 99370 11223",
        "business_name": "Konark Solar Enterprises",
        "city": "Rourkela",
        "address": "Civil Township, Rourkela"
    }
    is_dupe, rule, source = engine.check_duplicate(candidate)
    assert is_dupe is False
    assert rule is None
