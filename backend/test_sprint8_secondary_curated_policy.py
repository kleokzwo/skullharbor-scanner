from pathlib import Path
from services.plans.advanced import POLICY

root = Path(__file__).resolve().parent
scanner = (root / "scanner.py").read_text()
templates = list((root / "resources" / "secondary_quickcheck").glob("*.yaml"))
assert POLICY.secondary_include_tags == ""
assert len(templates) == 6
assert '"-t", str(NUCLEI_QUICKCHECK_TEMPLATE_DIR)' in scanner
assert '"-tags", NUCLEI_INCLUDE_TAGS' not in scanner
for p in templates:
    text = p.read_text().lower()
    assert "http:" in text
    assert "method: get" in text
    for forbidden in ("headless:", "javascript:", "code:", "network:"):
        assert forbidden not in text
print("sprint8 curated secondary quickcheck policy tests: OK")
