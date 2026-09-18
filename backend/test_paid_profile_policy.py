"""Paid profile refinement: SQL injection coverage without DoS self-service exposure."""
from pathlib import Path
from scan_profiles import get_scan_profile, public_product_catalog

free = get_scan_profile("free")
monthly = get_scan_profile("monthly")
annual = get_scan_profile("annual")

assert free.primary_tuning == "12"
assert monthly.primary_tuning == "12349b"
assert "9" in monthly.primary_tuning
assert "6" not in monthly.primary_tuning
assert monthly.adapter_slots == ("primary", "secondary", "surface")
assert annual.self_service is False
assert annual.primary_tuning is None

# Customer-safe catalog must not reveal private implementation details.
public = repr(public_product_catalog()).lower()
for private in ("nikto", "nuclei", "nmap", "tuning", "12349b", "adapter"):
    assert private not in public

# Secondary automatic checks remain bounded away from risky classes.
scanner_source = (Path(__file__).parent / "scanner.py").read_text().lower()
assert 'nuclei_excluded_tags = advanced_policy.secondary_excluded_tags' in scanner_source
assert 'nuclei_include_tags = advanced_policy.secondary_include_tags' in scanner_source

print("paid profile policy refinement tests: OK")
