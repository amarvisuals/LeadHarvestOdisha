import pytest
from app.services.normalizer import clean_phone_number, normalize_text, title_case_name, clean_pincode

def test_clean_phone_number_standard():
    clean, fmt = clean_phone_number("+91 98610 12345")
    assert clean == "9861012345"
    assert fmt == "+91 98610 12345"

def test_clean_phone_number_with_prefix_and_dashes():
    clean, fmt = clean_phone_number("09437-123456")
    assert clean == "9437123456"
    assert fmt == "+91 94371 23456"

def test_clean_phone_number_with_brackets_and_spaces():
    clean, fmt = clean_phone_number("(+91) 7008 998 877")
    assert clean == "7008998877"
    assert fmt == "+91 70089 98877"

def test_clean_phone_number_invalid_discard():
    # Discard numbers (e.g. Justdial helpline or all zeroes)
    clean, fmt = clean_phone_number("08888888888")
    assert clean is None
    assert fmt is None

    # Invalid starting digit (must start with 6, 7, 8, or 9 in India)
    clean, fmt = clean_phone_number("1234567890")
    assert clean is None
    assert fmt is None

def test_normalize_text():
    raw = "  M/s Kalinga   Foods & Spices, Pvt. Ltd.!  "
    norm = normalize_text(raw)
    assert norm == "m s kalinga foods spices pvt ltd"

def test_title_case_name():
    raw = "utkal CA services & IIT neet academy"
    formatted = title_case_name(raw)
    assert "CA" in formatted
    assert "IIT" in formatted
    assert "Utkal" in formatted

def test_clean_pincode():
    assert clean_pincode("Near Master Canteen, Bhubaneswar - 751001, Odisha") == "751001"
    assert clean_pincode("Badambadi, Cuttack 753012") == "753012"
    assert clean_pincode("No pincode mentioned") is None
