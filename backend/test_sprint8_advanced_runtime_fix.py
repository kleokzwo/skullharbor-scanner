"""Regression for Advanced real-scan timeout and failed-result UX."""
from pathlib import Path
from services.plans.advanced import POLICY

scanner = Path("scanner.py").read_text(encoding="utf-8")
ui = Path("../frontend/src/pages/DashboardPage.jsx").read_text(encoding="utf-8")
assert POLICY.secondary_automatic_scan is False
assert "cve" not in POLICY.secondary_include_tags.split(",")
assert 'cmd.append("-as")' in scanner
for flag in ('"-timeout"', '"-retries"', '"-mhe"', '"-duc"'):
    assert flag in scanner
assert 'selected&&selected.status==="completed"' in ui
assert "No result published" in ui
assert "did not publish a partial security result" in ui
print("advanced runtime fix tests: OK")
