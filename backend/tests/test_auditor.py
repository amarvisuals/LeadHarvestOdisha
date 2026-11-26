import pytest
import pandas as pd
from pathlib import Path
from app.services.auditor import auto_detect_columns, audit_file

def test_auto_detect_columns_messy():
    cols = ["Mobile Number", "Shop Name / Firm", "Office Address", "Town", "Service Niche"]
    mapping = auto_detect_columns(cols)
    assert mapping.get("phone") == "Mobile Number"
    assert mapping.get("business_name") == "Shop Name / Firm"
    assert mapping.get("address") == "Office Address"
    assert mapping.get("city") == "Town"
    assert mapping.get("category") == "Service Niche"

def test_audit_file_csv(tmp_path: Path):
    test_csv = tmp_path / "test_leads.csv"
    data = {
        "Company": ["Utkal Traders", "Kalinga Spas", "Blank Row", "Utkal Traders", ""],
        "Contact No": ["9861011111", "09437222222", "12345", "9861011111", ""],
        "City": ["Bhubaneswar", "Cuttack", "Puri", "Bhubaneswar", ""],
        "Address": ["Saheed Nagar", "CDA Sector 9", "Beach Road", "Saheed Nagar", ""]
    }
    pd.DataFrame(data).to_csv(test_csv, index=False)

    report = audit_file(test_csv)
    assert report["total_rows"] == 5
    assert report["blank_rows"] == 1
    assert report["invalid_phone_rows"] == 1 # "12345" is invalid
    assert report["duplicate_rows"] == 1 # Second "Utkal Traders" with same phone
    assert report["status"] == "ready"
