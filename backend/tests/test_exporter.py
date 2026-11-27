import pytest
import openpyxl
from pathlib import Path
from app.services.exporter import generate_leads_excel

def test_generate_leads_excel_structure(tmp_path: Path):
    output_path = tmp_path / "test_leads.xlsx"
    
    leads = [
        {
            "business_name": "Utkal Digital Solutions",
            "category": "Digital Marketing",
            "phone": "+91 98610 11111",
            "alt_phone": None,
            "address": "Saheed Nagar, Bhubaneswar",
            "area": "Saheed Nagar",
            "city": "Bhubaneswar",
            "district": "Khordha",
            "pincode": "751007",
            "rating": "4.8",
            "review_count": "120",
            "website": "https://www.utkaldigital.in",
            "listing_url": "https://www.justdial.com/bhubaneswar/utkal-digital",
            "source": "MockAdapter",
            "collected_at": "2026-11-26 21:00:00"
        }
    ]

    skipped = [
        {
            "business_name": "Duplicate Cafe",
            "phone": "+91 94370 22222",
            "city": "Cuttack",
            "category": "Restaurants",
            "duplicate_rule": "Phone Match (Rule 1)",
            "duplicate_source": "old_leads.xlsx"
        }
    ]

    meta = {
        "run_timestamp": "2026-11-26 21:00:00 UTC",
        "duration": "1m 15s",
        "cities": ["Bhubaneswar", "Cuttack"],
        "categories": ["Digital Marketing", "Restaurants"],
        "total_found": 2,
        "adapter": "MockAdapter"
    }

    excel_file = generate_leads_excel(leads, skipped, meta, output_path)
    assert excel_file.exists()

    # Load workbook and inspect 3 sheets
    wb = openpyxl.load_workbook(excel_file)
    assert "Leads" in wb.sheetnames
    assert "Summary" in wb.sheetnames
    assert "Skipped Duplicates" in wb.sheetnames

    ws_leads = wb["Leads"]
    headers = [ws_leads.cell(row=1, column=c).value for c in range(1, ws_leads.max_column + 1)]
    assert headers[0] == "Business Name"
    assert "Has Website" in headers
    assert "Opportunity Score" in headers
    assert "WhatsApp Link" in headers
    assert ws_leads.cell(row=2, column=1).value == "Utkal Digital Solutions"
    # Check hyperlink on Website column dynamically
    website_col = headers.index("Website") + 1
    website_cell = ws_leads.cell(row=2, column=website_col)
    assert website_cell.hyperlink is not None

    ws_summary = wb["Summary"]
    assert "Odisha" in str(ws_summary.cell(row=5, column=2).value)

    ws_skipped = wb["Skipped Duplicates"]
    assert ws_skipped.cell(row=2, column=1).value == "Duplicate Cafe"
