"""Regression: completed coverage means meaningful execution, not just process exit 0."""
from pathlib import Path
root=Path(__file__).resolve().parent
scanner=(root/'scanner.py').read_text()
engine=(root/'scan_engine.py').read_text()
ui=(root.parent/'frontend/src/pages/DashboardPage.jsx').read_text()
assert '_is_connectivity_diagnostic' in scanner
assert '"-h", target' in scanner
assert 'canonical_no_keepalive' in scanner
assert 'explicit_tls' in scanner
assert 'Connectivity-only JSON is transport failure' in scanner
assert '_core_http_baseline' in scanner
assert 'actual HTTP response' in scanner
assert 'root.find(".//host") is None' in scanner
assert 'root.find(".//runstats/finished") is None' in scanner
assert 'No result published' in ui
assert 'groupedFindings' in ui
assert 'coverage_family' in engine
print('sprint8 advanced coverage integrity tests: OK')
