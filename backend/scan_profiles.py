"""Server-owned SkullHarbor scan product policies.

Customer requests never contain scanner names, raw CLI flags, tuning categories, or
adapter selections. Billing/entitlement resolution will be connected in Sprint 6.
"""
from dataclasses import dataclass
from services.plans import FREE_POLICY, ADVANCED_POLICY


@dataclass(frozen=True)
class ScanProfile:
    key: str
    public_name: str
    self_service: bool
    adapter_slots: tuple[str, ...]
    primary_tuning: str | None
    require_all_adapters: bool = True


_PROFILES = {
    "free": ScanProfile(
        key="free",
        public_name="SkullHarbor Quick Check",
        self_service=True,
        adapter_slots=FREE_POLICY.adapter_slots,
        primary_tuning=FREE_POLICY.primary_tuning,
        require_all_adapters=FREE_POLICY.require_all_adapters,
    ),
    "monthly": ScanProfile(
        key="monthly",
        public_name="SkullHarbor Advanced Check",
        self_service=True,
        adapter_slots=ADVANCED_POLICY.adapter_slots,
        # Controlled paid expansion; disruptive category 6 remains excluded.
        primary_tuning=ADVANCED_POLICY.primary_tuning,
        require_all_adapters=ADVANCED_POLICY.require_all_adapters,
    ),
    "annual": ScanProfile(
        key="annual",
        public_name="SkullHarbor Managed Pentest",
        self_service=False,
        adapter_slots=(),
        primary_tuning=None,
        require_all_adapters=True,
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
