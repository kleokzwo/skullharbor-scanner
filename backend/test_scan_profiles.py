"""Sprint 4.1 Step 1: server-owned product/scan-profile policy tests."""
from pathlib import Path

from scan_profiles import get_scan_profile, public_product_catalog, require_self_service_profile

free = get_scan_profile("free")
monthly = get_scan_profile("monthly")
annual = get_scan_profile("annual")

assert free.public_name == "SkullHarbor Quick Check"
assert free.self_service is True
assert free.adapter_slots == ("primary",)
assert free.primary_tuning == "12"

assert monthly.public_name == "SkullHarbor Advanced Check"
assert monthly.self_service is True
assert monthly.adapter_slots == ("primary", "secondary", "surface")
assert len(monthly.primary_tuning) == 5
assert "6" not in monthly.primary_tuning
assert monthly.primary_tuning != free.primary_tuning

assert annual.public_name == "SkullHarbor Managed Pentest"
assert annual.self_service is False
assert annual.adapter_slots == ()
assert annual.primary_tuning is None
try:
    require_self_service_profile("annual")
except ValueError:
    pass
else:
    raise AssertionError("annual must never execute as a self-service scan")

catalog = public_product_catalog()
assert [x["key"] for x in catalog] == ["free", "monthly", "annual"]
assert catalog[2]["contact"] == "hello@skullharbor.org"
assert catalog[2]["pentests_per_year"] == 2
serialized = repr(catalog).lower()
for private_term in ("nikto", "nuclei", "nmap", "tuning", "adapter", "1234b"):
    assert private_term not in serialized

# Customer scan API cannot ask for a stronger profile or raw scanner controls.
main_source = (Path(__file__).parent / "main.py").read_text()
request_block = main_source[main_source.index("class ScanRequest"):main_source.index("class UserRequest")]
for forbidden in ("profile", "tier", "scanner", "tuning", "arguments", "flags"):
    assert forbidden not in request_block.lower()
assert 'require_self_service_profile("free")' in main_source

print("scan profile policy tests: OK")
