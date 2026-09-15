"""Sprint 4 closeout: guard customer-facing source/API against adapter leakage."""
from pathlib import Path
from scanner import _customer_safe_text

root = Path(__file__).resolve().parents[1]
frontend = "\n".join(p.read_text(errors="ignore") for p in (root / "frontend").rglob("*") if p.is_file())
main = (root / "backend" / "main.py").read_text()

for vendor in ("nikto", "nuclei"):
    assert vendor not in frontend.lower(), f"internal adapter name leaked into frontend: {vendor}"
    sanitized = _customer_safe_text(f"{vendor} detected an observation")
    assert vendor not in sanitized.lower()

# Finding raw_output is intentionally stored internally but must not be serialized by scan_detail.
scan_detail = main[main.index("def scan_detail"):main.index('@app.get("/api/scans/{scan_id}/status")')]
assert '"raw_output"' not in scan_detail
assert '"scanner": f.scanner' in scan_detail  # public value is the neutral engine id

print("customer boundary tests: OK")
