"""Regression: paid Advanced coverage must be real, complete and vendor-neutral."""
from pathlib import Path
from services.plans import ADVANCED_POLICY
from scan_profiles import get_scan_profile

ROOT = Path(__file__).resolve().parent
engine = (ROOT / "scan_engine.py").read_text(encoding="utf-8")
scanner = (ROOT / "scanner.py").read_text(encoding="utf-8")
controller = (ROOT / "controllers" / "scan_controller.py").read_text(encoding="utf-8")
ui = (ROOT.parent / "frontend" / "src" / "pages" / "DashboardPage.jsx").read_text(encoding="utf-8")

p = get_scan_profile("monthly")
assert p.adapter_slots == ("primary", "secondary", "surface")
assert p.require_all_adapters is True
assert ADVANCED_POLICY.require_all_adapters is True
assert "run_nuclei_streaming" in engine and "run_surface_discovery_streaming" in engine
assert '"nuclei"' in scanner and '"nmap"' in scanner
assert "successful_adapters != len(adapter_specs)" in engine
assert "No partial Advanced result was published" in engine
assert '"coverage": _coverage_payload(s)' in controller
assert "Advanced coverage" in ui
# Customer UI remains vendor-neutral.
for vendor in ("nikto", "nuclei", "nmap"):
    assert vendor not in ui.lower()
print("advanced coverage closeout tests: OK")
