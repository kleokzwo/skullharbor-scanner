"""Sprint 8 / Step 3: customer-first scan and finding experience."""
from pathlib import Path

root = Path(__file__).resolve().parent.parent
frontend = "\n".join(p.read_text(encoding="utf-8") for p in (root / "frontend" / "src").rglob("*.jsx"))
backend = "\n".join((root / "backend" / p).read_text(encoding="utf-8") for p in ("controllers/scan_controller.py", "services/verification_service.py"))

# Runtime stages are translated into customer language; raw engineering logs are
# no longer rendered in the normal product surface.
for text in ("Preparing check", "Confirming authorization", "Checking website", "Reviewing results", "Saving results"):
    assert text in frontend
assert "Technical scan log" not in frontend
assert "Preparing scanner..." not in frontend

# Result/finding UX explains the outcome without overclaiming security.
assert "No findings in this check" in frontend
assert "This is not a guarantee that the website has no vulnerabilities." in frontend
for heading in ("What did we find?", "Why does this matter?", "What should I do?", "Evidence & details"):
    assert heading in frontend

# Do not surface raw-adapter language or unfinished controls in the customer UI.
assert "Raw technical evidence" not in frontend
assert "finding.raw_output" not in frontend
assert "finding.rule_id" not in frontend
assert "Report as false positive" not in frontend
assert "Engine: SkullHarbor Web Check" not in frontend
for internal_name in ("Nikto", "Nuclei", "Nmap"):
    assert internal_name not in frontend

# Backend remains authoritative and raw output remains excluded from scan detail.
assert '@router.post("/api/scan")' in backend
assert '_scan_authorization' in backend
assert '# raw_output is retained internally for engineering diagnostics only.' in backend
assert '"raw_output": f.raw_output' not in backend

print("product UX step 3 tests: OK")
