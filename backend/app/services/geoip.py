"""
Home State GeoIP Detection, VPN/Proxy Checking, and Canonical Indian State Resolution.
Never stores raw IPs; only returns/logs state, country code, and salted IP hashes.
"""
from __future__ import annotations

import ipaddress
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from fastapi import Request, Response

from app.core.config import settings
from app.services.auth import sign_token, unsign_token

logger = logging.getLogger("leadharvest.geoip")

COOKIE_GUEST_STATE = "lh_guest_state"
COOKIE_TEST_GEO = "lh_test_geo"  # Test-mode only simulation override

# Canonical 28 states & 8 UTs loaded from india_locations.json
_STATES_CACHE: Optional[List[str]] = None

STATE_ALIASES: Dict[str, str] = {
    "orissa": "Odisha",
    "nct of delhi": "Delhi (NCT)",
    "new delhi": "Delhi (NCT)",
    "delhi": "Delhi (NCT)",
    "delhi (nct)": "Delhi (NCT)",
    "jammu and kashmir": "Jammu & Kashmir",
    "jammu & kashmir": "Jammu & Kashmir",
    "andaman and nicobar islands": "Andaman & Nicobar Islands",
    "dadra and nagar haveli and daman and diu": "Dadra & Nagar Haveli and Daman & Diu",
    "pondicherry": "Puducherry",
    "uttaranchal": "Uttarakhand",
}

# Configurable known VPN/proxy/datacenter CIDR ranges (example cloud & exit ranges)
DEFAULT_VPN_DATACENTER_CIDRS = [
    "198.51.100.0/24",  # TEST-NET-2 used for VPN simulation
    "192.0.2.0/24",     # TEST-NET-1
    "45.33.0.0/16",     # Linode datacenter
    "104.248.0.0/16",   # DigitalOcean datacenter
    "185.220.100.0/22", # Tor exit nodes
]

# Offline local IP-prefix map for fast zero-dependency GeoIP resolution & testing
# (Production deployments can point GEOIP_DB_PATH to MaxMind GeoLite2-City.mmdb)
LOCAL_INDIAN_PREFIXES: List[Tuple[str, str]] = [
    ("103.21.124.0/22", "Odisha"),
    ("117.200.0.0/16", "Odisha"),
    ("49.36.0.0/16", "Maharashtra"),
    ("103.5.132.0/22", "Maharashtra"),
    ("106.51.0.0/16", "Karnataka"),
    ("122.166.0.0/16", "Karnataka"),
    ("182.72.0.0/16", "Delhi (NCT)"),
    ("103.27.8.0/22", "Tamil Nadu"),
    ("115.96.0.0/16", "Telangana"),
    ("117.198.0.0/16", "West Bengal"),
    ("103.4.220.0/22", "Gujarat"),
    ("157.32.0.0/16", "Uttar Pradesh"),
    ("157.48.0.0/16", "Rajasthan"),
    ("117.211.0.0/16", "Kerala"),
    ("103.15.64.0/22", "Madhya Pradesh"),
    ("103.24.84.0/22", "Punjab"),
]


def get_canonical_states() -> List[str]:
    global _STATES_CACHE
    if _STATES_CACHE is not None:
        return _STATES_CACHE
    path = settings.CONFIG_DIR / "india_locations.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            items = data if isinstance(data, list) else data.get("states", [])
            _STATES_CACHE = [s["name"] for s in items if isinstance(s, dict) and "name" in s]
            return _STATES_CACHE
    _STATES_CACHE = ["Odisha", "Maharashtra", "Karnataka", "Delhi", "Tamil Nadu"]
    return _STATES_CACHE


def resolve_canonical_state(raw_name: Optional[str]) -> Optional[str]:
    if not raw_name:
        return None
    cleaned = raw_name.strip()
    if cleaned.lower() in STATE_ALIASES:
        cleaned = STATE_ALIASES[cleaned.lower()]
    canonical = get_canonical_states()
    for st in canonical:
        if st.lower() == cleaned.lower():
            return st
    return None


@dataclass
class GeoLookupResult:
    state: Optional[str]
    country_code: Optional[str]
    is_vpn_or_proxy: bool
    confidence: str  # high | medium | low | none
    provider: str
    requires_manual_choice: bool


class BaseGeoIPProvider(ABC):
    name: str = "base"

    @abstractmethod
    def lookup(self, ip: str, vpn_cidrs: Optional[List[str]] = None) -> GeoLookupResult:
        ...


def is_ip_in_cidrs(ip: str, cidrs: List[str]) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip)
    except ValueError:
        return False
    for cidr in cidrs:
        try:
            if ip_obj in ipaddress.ip_network(cidr.strip(), strict=False):
                return True
        except ValueError:
            continue
    return False


class LocalPrefixGeoIPProvider(BaseGeoIPProvider):
    name = "local_prefix"

    def lookup(self, ip: str, vpn_cidrs: Optional[List[str]] = None) -> GeoLookupResult:
        cidrs = vpn_cidrs or DEFAULT_VPN_DATACENTER_CIDRS
        if is_ip_in_cidrs(ip, cidrs):
            return GeoLookupResult(
                state=None,
                country_code="IN",
                is_vpn_or_proxy=True,
                confidence="low",
                provider=self.name,
                requires_manual_choice=True,
            )

        # Outside India simulation IP range (203.0.113.0/24 TEST-NET-3)
        if is_ip_in_cidrs(ip, ["203.0.113.0/24"]):
            return GeoLookupResult(
                state=None,
                country_code="US",
                is_vpn_or_proxy=False,
                confidence="high",
                provider=self.name,
                requires_manual_choice=True,
            )

        for prefix, st_name in LOCAL_INDIAN_PREFIXES:
            if is_ip_in_cidrs(ip, [prefix]):
                return GeoLookupResult(
                    state=resolve_canonical_state(st_name),
                    country_code="IN",
                    is_vpn_or_proxy=False,
                    confidence="high",
                    provider=self.name,
                    requires_manual_choice=False,
                )

        # Private/loopback IPs: in local dev/test default to Odisha so local testing works;
        # in production, require manual choice.
        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private or ip_obj.is_loopback:
                if settings.ENVIRONMENT != "production":
                    return GeoLookupResult(
                        state="Odisha",
                        country_code="IN",
                        is_vpn_or_proxy=False,
                        confidence="medium",
                        provider=self.name,
                        requires_manual_choice=False,
                    )
                return GeoLookupResult(
                    state=None,
                    country_code="IN",
                    is_vpn_or_proxy=False,
                    confidence="none",
                    provider=self.name,
                    requires_manual_choice=True,
                )
        except ValueError:
            pass

        return GeoLookupResult(
            state=None,
            country_code=None,
            is_vpn_or_proxy=False,
            confidence="none",
            provider=self.name,
            requires_manual_choice=True,
        )


class MaxMindGeoLite2Provider(BaseGeoIPProvider):
    name = "maxmind_geolite2"

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._fallback = LocalPrefixGeoIPProvider()

    def lookup(self, ip: str, vpn_cidrs: Optional[List[str]] = None) -> GeoLookupResult:
        cidrs = vpn_cidrs or DEFAULT_VPN_DATACENTER_CIDRS
        if is_ip_in_cidrs(ip, cidrs):
            return GeoLookupResult(
                state=None,
                country_code="IN",
                is_vpn_or_proxy=True,
                confidence="low",
                provider=self.name,
                requires_manual_choice=True,
            )
        try:
            import geoip2.database  # type: ignore

            with geoip2.database.Reader(self.db_path) as reader:
                resp = reader.city(ip)
                cc = resp.country.iso_code
                subdiv = resp.subdivisions.most_specific.name if resp.subdivisions else None
                if cc != "IN":
                    return GeoLookupResult(
                        state=None,
                        country_code=cc,
                        is_vpn_or_proxy=False,
                        confidence="high",
                        provider=self.name,
                        requires_manual_choice=True,
                    )
                resolved = resolve_canonical_state(subdiv)
                return GeoLookupResult(
                    state=resolved,
                    country_code="IN",
                    is_vpn_or_proxy=False,
                    confidence="high" if resolved else "none",
                    provider=self.name,
                    requires_manual_choice=resolved is None,
                )
        except Exception:
            return self._fallback.lookup(ip, vpn_cidrs=cidrs)


def get_geoip_provider(provider_name: Optional[str] = None, db_path: Optional[str] = None) -> BaseGeoIPProvider:
    name = (provider_name or settings.GEOIP_PROVIDER or "local").lower()
    path = db_path or settings.GEOIP_DB_PATH
    if name == "maxmind" and path:
        return MaxMindGeoLite2Provider(path)
    return LocalPrefixGeoIPProvider()


def detect_geo_for_request(
    request: Request,
    raw_ip: str,
    provider_name: Optional[str] = None,
    db_path: Optional[str] = None,
    test_mode_enabled: bool = False,
) -> GeoLookupResult:
    """
    Detects state from IP (or Test Mode simulation cookie when test_mode_enabled=True).
    """
    if test_mode_enabled:
        sim_cookie = request.cookies.get(COOKIE_TEST_GEO)
        if sim_cookie:
            sim_data = unsign_token(sim_cookie)
            if sim_data:
                mode = sim_data.get("mode")
                if mode == "vpn":
                    return GeoLookupResult(None, "IN", True, "low", "test_simulator", True)
                if mode == "outside_india":
                    return GeoLookupResult(None, "US", False, "high", "test_simulator", True)
                if mode == "state":
                    st = resolve_canonical_state(sim_data.get("state"))
                    return GeoLookupResult(st, "IN", False, "high" if st else "none", "test_simulator", st is None)

    provider = get_geoip_provider(provider_name, db_path)
    return provider.lookup(raw_ip)


def set_guest_state_cookie(response: Response, state_name: str) -> None:
    token = sign_token({"home_state": state_name})
    response.set_cookie(
        COOKIE_GUEST_STATE,
        token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=86400 * 365,
    )


def read_guest_state_cookie(request: Request) -> Optional[str]:
    raw = request.cookies.get(COOKIE_GUEST_STATE)
    if not raw:
        return None
    data = unsign_token(raw)
    if not data:
        return None
    return resolve_canonical_state(data.get("home_state"))
