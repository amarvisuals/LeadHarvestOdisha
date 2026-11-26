from typing import List, Dict, Any, Optional, Tuple, Set
from rapidfuzz import fuzz
from app.services.normalizer import clean_phone_number, normalize_text
from app.core.config import settings

class DeduplicationEngine:
    """
    High-performance 3-tier deduplication engine matching prompt rules:
    1. Normalised phone number match (strip spaces, +91, 0, compare last 10 digits).
    2. Normalised business name + city exact match.
    3. Fuzzy match (RapidFuzz token_sort_ratio >= 90) on name + address within same city.
    """

    def __init__(self, known_records: Optional[List[Dict[str, Any]]] = None):
        self.phone_index: Dict[str, Dict[str, Any]] = {}
        self.name_city_index: Dict[str, Dict[str, Any]] = {}
        self.city_address_index: Dict[str, List[Dict[str, Any]]] = {}
        
        if known_records:
            self.load_known_records(known_records)

    def load_known_records(self, records: List[Dict[str, Any]]):
        """Loads known records into memory indices for O(1) and filtered fuzzy lookups."""
        for rec in records:
            source_tag = rec.get("source_file") or rec.get("source") or "Known Records Index"
            
            # 1. Phone index
            phone_clean = rec.get("phone_clean")
            if not phone_clean and rec.get("phone"):
                phone_clean, _ = clean_phone_number(rec.get("phone"))
            if phone_clean:
                self.phone_index[phone_clean] = {"record": rec, "source": source_tag}
            
            alt_clean = rec.get("alt_phone_clean")
            if not alt_clean and rec.get("alt_phone"):
                alt_clean, _ = clean_phone_number(rec.get("alt_phone"))
            if alt_clean:
                self.phone_index[alt_clean] = {"record": rec, "source": source_tag}

            # 2. Name + City exact index
            name_norm = normalize_text(rec.get("business_name"))
            city_norm = normalize_text(rec.get("city"))
            if name_norm and city_norm:
                key = f"{name_norm}|{city_norm}"
                self.name_city_index[key] = {"record": rec, "source": source_tag}

            # 3. City-bucketed records for fuzzy comparison
            if city_norm and name_norm:
                addr_norm = normalize_text(rec.get("address"))
                if city_norm not in self.city_address_index:
                    self.city_address_index[city_norm] = []
                self.city_address_index[city_norm].append({
                    "name_norm": name_norm,
                    "addr_norm": addr_norm,
                    "record": rec,
                    "source": source_tag
                })

    def check_duplicate(self, candidate: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Evaluates candidate against indices in strict order.
        Returns:
            (is_duplicate: bool, rule_matched: Optional[str], match_source: Optional[str])
        """
        # Rule 1: Phone number match
        cand_phone = candidate.get("phone_clean")
        if not cand_phone and candidate.get("phone"):
            cand_phone, _ = clean_phone_number(candidate.get("phone"))
            
        if cand_phone and cand_phone in self.phone_index:
            match_meta = self.phone_index[cand_phone]
            return True, "Phone Number Match (Rule 1)", match_meta["source"]

        cand_alt = candidate.get("alt_phone_clean")
        if not cand_alt and candidate.get("alt_phone"):
            cand_alt, _ = clean_phone_number(candidate.get("alt_phone"))
        if cand_alt and cand_alt in self.phone_index:
            match_meta = self.phone_index[cand_alt]
            return True, "Alternate Phone Match (Rule 1)", match_meta["source"]

        # Rule 2: Normalised business name + city exact match
        name_norm = normalize_text(candidate.get("business_name"))
        city_norm = normalize_text(candidate.get("city"))

        if name_norm and city_norm:
            exact_key = f"{name_norm}|{city_norm}"
            if exact_key in self.name_city_index:
                match_meta = self.name_city_index[exact_key]
                return True, "Exact Business Name & City Match (Rule 2)", match_meta["source"]

        # Rule 3: Fuzzy match (token_sort_ratio >= 90) on name + address within same city
        if city_norm and name_norm and city_norm in self.city_address_index:
            cand_addr = normalize_text(candidate.get("address"))
            cand_composite = f"{name_norm} {cand_addr}".strip()
            
            for item in self.city_address_index[city_norm]:
                known_composite = f"{item['name_norm']} {item['addr_norm']}".strip()
                # Compare composite
                score = fuzz.token_sort_ratio(cand_composite, known_composite)
                if score >= settings.FUZZY_MATCH_THRESHOLD:
                    return True, f"Fuzzy Name & Address Match {score}% (Rule 3)", item["source"]

                # If candidate name is very long and match is near-identical
                name_score = fuzz.token_sort_ratio(name_norm, item["name_norm"])
                if name_score >= 95:
                    return True, f"Fuzzy Business Name Match {name_score}% (Rule 3)", item["source"]

        return False, None, None

    def register_new_lead(self, lead: Dict[str, Any], source_label: str = "Current Run"):
        """Adds a newly discovered lead to internal index to prevent intra-run duplicates."""
        cand_phone = lead.get("phone_clean")
        if not cand_phone and lead.get("phone"):
            cand_phone, _ = clean_phone_number(lead.get("phone"))
        if cand_phone:
            self.phone_index[cand_phone] = {"record": lead, "source": source_label}

        name_norm = normalize_text(lead.get("business_name"))
        city_norm = normalize_text(lead.get("city"))
        if name_norm and city_norm:
            key = f"{name_norm}|{city_norm}"
            self.name_city_index[key] = {"record": lead, "source": source_label}

            addr_norm = normalize_text(lead.get("address"))
            if city_norm not in self.city_address_index:
                self.city_address_index[city_norm] = []
            self.city_address_index[city_norm].append({
                "name_norm": name_norm,
                "addr_norm": addr_norm,
                "record": lead,
                "source": source_label
            })
