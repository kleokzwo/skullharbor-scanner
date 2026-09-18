"""Regression: Advanced secondary coverage stays bounded and findings remain itemized."""
from pathlib import Path
from services.plans.advanced import POLICY

scanner = Path("scanner.py").read_text(encoding="utf-8")
engine = Path("scan_engine.py").read_text(encoding="utf-8")
ui = Path("../frontend/src/pages/DashboardPage.jsx").read_text(encoding="utf-8")

assert POLICY.secondary_automatic_scan is False
assert "cve" not in POLICY.secondary_include_tags.split(",")
assert POLICY.secondary_include_tags == ""
assert '"-t", str(NUCLEI_QUICKCHECK_TEMPLATE_DIR)' in scanner
assert 'if NUCLEI_AUTOMATIC_SCAN:' in scanner and 'cmd.append("-as")' in scanner
assert '"Vulnerability & exposure checks"' in engine
assert 'const groupedFindings' in ui
assert 'group.items.map' in ui
assert 'openFinding(f)' in ui
assert 'View <Icon' in ui
print("advanced runtime hotfix5 tests: OK")
