"""Server-owned SkullHarbor scan product policies.

Customer requests never contain scanner names, raw CLI flags, tuning categories, or
adapter selections. Billing/entitlement resolution will be connected in Sprint 6.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ScanProfile:
    key: str
    public_name: str
    self_service: bool
    adapter_slots: tuple[str, ...]
    primary_tuning: str | None


_PROFILES = {
    "free": ScanProfile(
        key="free",
        public_name="SkullHarbor Quick Check",
        self_service=True,
        adapter_slots=("primary",),
        primary_tuning="12",
    ),
    "monthly": ScanProfile(
        key="monthly",
        public_name="SkullHarbor Advanced Check",
        self_service=True,
        adapter_slots=("primary", "secondary", "surface"),
        # Controlled paid expansion: includes SQL-injection checks (9); DoS category 6 is excluded.
        primary_tuning="12349b",
    ),
    "annual": ScanProfile(
        key="annual",
        public_name="SkullHarbor Managed Pentest",
        self_service=False,
        adapter_slots=(),
        primary_tuning=None,
    ),
}


def get_scan_profile(key: str) -> ScanProfile:
    normalized = (key or "").strip().lower()
    try:
        return _PROFILES[normalized]
    except KeyError as exc:
        raise ValueError("Unknown SkullHarbor scan profile") from exc


def require_self_service_profile(key: str) -> ScanProfile:
    profile = get_scan_profile(key)
    if not profile.self_service:
        raise ValueError("This product is a managed pentest and cannot be started as a self-service scan")
    return profile


def public_product_catalog() -> list[dict]:
    """Customer-safe product metadata only; no adapter/tuning implementation details."""
    return [
        {"key": "free", "name": "SkullHarbor Quick Check", "delivery": "self-service"},
        {"key": "monthly", "name": "SkullHarbor Advanced Check", "delivery": "self-service"},
        {
            "key": "annual",
            "name": "SkullHarbor Managed Pentest",
            "delivery": "managed",
            "contact": "hello@skullharbor.org",
            "pentests_per_year": 2,
        },
    ]
