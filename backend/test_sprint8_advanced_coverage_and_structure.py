"""Architecture + paid coverage regression for Sprint 8 hardening."""
from pathlib import Path
from scan_profiles import get_scan_profile
from services.plans import FREE_POLICY, ADVANCED_POLICY

root = Path(__file__).resolve().parents[1]
free = get_scan_profile("free")
advanced = get_scan_profile("monthly")
assert free.adapter_slots == ("primary",)
assert advanced.adapter_slots == ("primary", "secondary", "surface")
assert FREE_POLICY.primary_tuning == "12"
assert ADVANCED_POLICY.primary_tuning == "12349b"
assert ADVANCED_POLICY.secondary_include_tags == ""
assert ADVANCED_POLICY.secondary_automatic_scan is False
assert {"dos", "fuzz", "bruteforce", "intrusive"}.issubset(set(ADVANCED_POLICY.secondary_excluded_tags.split(",")))
assert 80 not in ADVANCED_POLICY.surface_ports and 443 not in ADVANCED_POLICY.surface_ports
assert set((21,22,445,3306,3389,5432,6379,27017)).issubset(set(ADVANCED_POLICY.surface_ports))
assert 8080 not in ADVANCED_POLICY.surface_ports and 8443 not in ADVANCED_POLICY.surface_ports
for page in ("DashboardPage.jsx","ScansPage.jsx","TargetsPage.jsx","SettingsPage.jsx","FindingPage.jsx"):
    assert (root / "frontend" / "src" / "pages" / page).exists()
print("advanced coverage and structure tests: OK")
