import re
from typing import Optional, Tuple

DISCARD_PHONE_NUMBERS = {
    "09980655076", "9980655076", "08888888888", "8888888888",
    "0000000000", "1111111111", "1234567890", "9999999999"
}

def clean_phone_number(raw_phone: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Cleans, validates, and normalizes Indian phone numbers according to prompt specification.
    
    Returns:
        (clean_10_digit, formatted_display)
        e.g. ("9861012345", "+91 98610 12345") or (None, None) if invalid.
    """
    if not raw_phone:
        return None, None
    
    # Strip spaces, brackets, hyphens, dots, plus signs
    digits = re.sub(r"[^\d]", "", str(raw_phone))
    if not digits:
        return None, None

    # Strip leading zeroes
    digits = digits.lstrip("0")

    # If starts with country code 91 and has 12 digits:
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) > 10 and digits.startswith("91"):
        digits = digits[-10:]

    # Take last 10 digits if longer
    if len(digits) > 10:
        digits = digits[-10:]

    # Must be exactly 10 digits and start with 6, 7, 8, or 9 (standard Indian mobile/telecom series)
    if len(digits) == 10 and digits[0] in "6789" and digits not in DISCARD_PHONE_NUMBERS:
        formatted = f"+91 {digits[:5]} {digits[5:]}"
        return digits, formatted

    return None, None

def normalize_text(text: Optional[str]) -> str:
    """Normalizes string for comparison: lowercase, single spaces, strip punctuation."""
    if not text:
        return ""
    cleaned = re.sub(r"[^\w\s]", " ", str(text).lower())
    return " ".join(cleaned.split())

def title_case_name(name: Optional[str]) -> str:
    """Format business name in clean title case with preserved acronyms."""
    if not name:
        return ""
    words = str(name).strip().split()
    formatted = []
    acronyms = {"CA", "IIT", "NEET", "GST", "IT", "ATM", "ICICI", "HDFC", "SBI", "LIC", "VIP", "TV", "AC", "LED"}
    for w in words:
        upper = w.upper()
        if upper in acronyms:
            formatted.append(upper)
        else:
            formatted.append(w.capitalize())
    return " ".join(formatted)

def clean_pincode(raw: Optional[str]) -> Optional[str]:
    """Extracts valid 6-digit Indian pincode."""
    if not raw:
        return None
    match = re.search(r"\b(7[5-7]\d{4})\b", str(raw)) # Odisha pincodes start with 75, 76, 77
    if match:
        return match.group(1)
    # Generic 6-digit fallback
    generic = re.search(r"\b(\d{6})\b", str(raw))
    return generic.group(1) if generic else None
