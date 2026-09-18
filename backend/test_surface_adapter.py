"""Sprint 4.1 Step 2: bounded surface-discovery policy and normalization tests."""
from pathlib import Path
import scanner
from scan_profiles import get_scan_profile

monthly = get_scan_profile("monthly")
free = get_scan_profile("free")
assert "surface" in monthly.adapter_slots
assert "surface" not in free.adapter_slots
assert 80 not in scanner.SURFACE_ALLOWED_PORTS and 443 not in scanner.SURFACE_ALLOWED_PORTS
assert {21,22,445,3306,3389,5432,6379,8080,8443,27017}.issubset(set(scanner.SURFACE_ALLOWED_PORTS))
assert scanner.SURFACE_ADAPTER_TIMEOUT_SECONDS <= 90

sample = """<?xml version='1.0'?>
<nmaprun><host><ports>
<port protocol='tcp' portid='80'><state state='open'/></port>
<port protocol='tcp' portid='8080'><state state='open'/></port>
<port protocol='tcp' portid='8443'><state state='open'/></port>
<port protocol='tcp' portid='22'><state state='open'/></port>
</ports></host></nmaprun>"""
findings = scanner.normalize_surface_xml(sample, "https://example.com")
assert len(findings) == 3
assert {f["rule_id"] for f in findings} == {
    "surface.external-service.22",
    "surface.external-service.8080",
    "surface.external-service.8443",
}
assert all(f["scanner"] == "web-security" for f in findings)
assert all("nmap" not in repr(f).lower() for f in findings)

# The adapter command is fixed backend policy: no scripts, UDP, OS detection,
# version detection, arbitrary port ranges or customer-provided flags.
source = (Path(__file__).parent / "scanner.py").read_text()
block = source[source.index("def run_surface_discovery_streaming"):]
for forbidden in ('"-sC"', '"-sU"', '"-O"', '"-sV"', '"--script"'):
    assert forbidden not in block
assert 'SURFACE_ALLOWED_PORTS' in block
assert '"-sT"' in block
assert '"-T2"' in block

print("surface adapter policy tests: OK")
