import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
from app.services.normalizer import clean_phone_number, normalize_text

COLUMN_SYNONYMS = {
    "phone": [
        "phone", "mobile", "contact", "cell", "telephone", "contact no", "contact_no", 
        "mobile number", "mobile_no", "phone number", "phone_no", "whatsapp", "primary phone",
        "ph no", "ph_number", "mob", "phone1", "contact1"
    ],
    "alt_phone": [
        "alt phone", "alternate", "secondary phone", "secondary_contact", "alt_contact",
        "other phone", "landline", "phone2", "mobile2", "alt_no"
    ],
    "business_name": [
        "business name", "business_name", "business", "company", "company name", "company_name",
        "firm", "firm name", "shop", "shop name", "store", "name", "title", "establishment",
        "organisation", "organization", "agency", "hospital", "hotel", "restaurant"
    ],
    "address": [
        "address", "location", "locality", "street", "area", "full address", "office address",
        "address line", "street address", "addr"
    ],
    "city": [
        "city", "town", "district", "place", "location_city", "metro"
    ],
    "category": [
        "category", "business category", "niche", "type", "industry", "segment", "service"
    ],
    "pincode": [
        "pincode", "pin", "pin code", "postal code", "zip", "zip code"
    ]
}

def auto_detect_columns(columns: List[str]) -> Dict[str, str]:
    """
    Intelligently maps arbitrary column names to standard fields.
    Returns mapping: standard_field -> original_column_name
    """
    mapping = {}
    normalized_cols = {col: re.sub(r"[^\w\s]", "", str(col).lower()).strip() for col in columns}

    for std_field, synonyms in COLUMN_SYNONYMS.items():
        matched_col = None
        # Exact match on normalized synonyms
        for col_orig, col_norm in normalized_cols.items():
            if col_norm in synonyms:
                matched_col = col_orig
                break
        
        # Substring match if no exact match
        if not matched_col:
            for col_orig, col_norm in normalized_cols.items():
                if any(syn in col_norm for syn in synonyms):
                    matched_col = col_orig
                    break
                    
        if matched_col and matched_col not in mapping.values():
            mapping[std_field] = matched_col

    return mapping

def audit_file(file_path: Path) -> Dict[str, Any]:
    """
    Parses and audits an uploaded Excel/CSV file.
    Identifies rows, detects columns, audits phone validity, checks internal duplicates.
    """
    suffix = file_path.suffix.lower()
    
    try:
        if suffix == ".csv":
            df = pd.read_csv(file_path, dtype=str)
        elif suffix in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path, dtype=str)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")
    except Exception as e:
        raise ValueError(f"Failed to read spreadsheet: {str(e)}")

    total_rows = len(df)
    columns = [str(c) for c in df.columns]
    mapping = auto_detect_columns(columns)

    # Detect blank rows
    blank_mask = df.isna().all(axis=1) | (df.apply(lambda row: "".join(row.dropna().astype(str)).strip() == "", axis=1))
    blank_rows = int(blank_mask.sum())
    
    valid_df = df[~blank_mask].copy()

    # Phone audit
    invalid_phone_count = 0
    phone_col = mapping.get("phone")
    if phone_col and phone_col in valid_df.columns:
        for val in valid_df[phone_col]:
            clean, _ = clean_phone_number(str(val) if pd.notna(val) else None)
            if not clean:
                invalid_phone_count += 1
    else:
        # If no phone column detected, all rows lack valid phone
        invalid_phone_count = len(valid_df)

    # Internal duplicate detection
    internal_dupe_count = 0
    seen_phones = set()
    seen_names_cities = set()
    name_col = mapping.get("business_name")
    city_col = mapping.get("city")

    for _, row in valid_df.iterrows():
        is_dupe = False
        if phone_col and pd.notna(row.get(phone_col)):
            p_clean, _ = clean_phone_number(str(row.get(phone_col)))
            if p_clean:
                if p_clean in seen_phones:
                    is_dupe = True
                else:
                    seen_phones.add(p_clean)

        if not is_dupe and name_col and pd.notna(row.get(name_col)):
            n_norm = normalize_text(str(row.get(name_col)))
            c_norm = normalize_text(str(row.get(city_col))) if city_col and pd.notna(row.get(city_col)) else ""
            key = f"{n_norm}|{c_norm}"
            if n_norm:
                if key in seen_names_cities:
                    is_dupe = True
                else:
                    seen_names_cities.add(key)
        
        if is_dupe:
            internal_dupe_count += 1

    valid_rows = len(valid_df) - internal_dupe_count
    
    # Determine Status Badge
    # Ready if we have business name and either phone or address, and at least 1 valid row
    is_ready = bool(mapping.get("business_name") and (mapping.get("phone") or mapping.get("address")) and valid_rows > 0)
    status = "ready" if is_ready else "needs_attention"

    # Sample rows for preview
    sample_rows = []
    sample_df = valid_df.head(5).fillna("")
    for _, r in sample_df.iterrows():
        sample_rows.append({k: str(v) for k, v in r.items()})

    return {
        "filename": file_path.name,
        "file_size_bytes": file_path.stat().st_size,
        "total_rows": total_rows,
        "valid_rows": max(0, valid_rows),
        "blank_rows": blank_rows,
        "invalid_phone_rows": invalid_phone_count,
        "duplicate_rows": internal_dupe_count,
        "column_mapping": mapping,
        "detected_columns": columns,
        "sample_rows": sample_rows,
        "status": status
    }
