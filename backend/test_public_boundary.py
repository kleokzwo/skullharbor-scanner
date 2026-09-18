"""Sprint 4 closeout: guard customer-facing source/API against adapter leakage."""
from pathlib import Path
from scanner import _customer_safe_text

root = Path(__file__).resolve().parents[1]
frontend_root = root / "frontend"
public_frontend_files = [frontend_root / "index.html"]
public_frontend_files += [
    p for p in (frontend_root / "src").rglob("*")
    if p.is_file() and p.suffix.lower() in {".js", ".jsx", ".ts", ".tsx", ".css", ".html"}
]
frontend = "\n".join(p.read_text(errors="ignore") for p in public_frontend_files if p.exists())
main = (root / "backend" / "application.py").read_text()

for vendor in ("nikto", "nuclei", "nmap"):
    assert vendor not in frontend.lower(), f"internal adapter name leaked into frontend: {vendor}"
    sanitized = _customer_safe_text(f"{vendor} detected an observation")
    assert vendor not in sanitized.lower()

# Finding raw_output is intentionally stored internally but must not be serialized by scan_detail.
scan_detail = main[main.index("def scan_detail"):main.index('@app.get("/api/scans/{scan_id}/status")')]
assert '"raw_output"' not in scan_detail
assert '"scanner": f.scanner' in scan_detail  # public value is the neutral engine id

print("customer boundary tests: OK")
