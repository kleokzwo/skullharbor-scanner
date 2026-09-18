"""Sprint 8 / Step 2: safe, simple target ownership onboarding UX."""
from pathlib import Path

root = Path(__file__).resolve().parent.parent
frontend = "\n".join(x.read_text(encoding="utf-8") for x in (root / "frontend" / "src").rglob("*.jsx"))
backend = (root / "backend" / "application.py").read_text(encoding="utf-8")

# The product explains ownership verification in customer language.
assert "Verify ownership." in frontend
assert "This protects your organization and helps prevent unauthorized use." in frontend
assert "Add this TXT record to your DNS" in frontend
assert "Verify ownership" in frontend
assert "Customer systems can instead be authorized through a trusted SkullHarbor engagement." in frontend

# The UI keeps the two legitimate Sprint-7 authorization paths distinct.
assert "Only verify systems you own." in frontend
assert "trusted SkullHarbor engagement" in frontend

# Customer target lists are scoped to the selected local customer profile.
assert 'targets.filter(t=>!userId || String(t.user_id)===String(userId))' in frontend

# UX does not weaken the backend ownership proof: a unique SkullHarbor TXT
# token is still generated and the authoritative verify endpoint remains.
assert 'verification_token=secrets.token_urlsafe(24)' in backend
assert '@app.post("/api/targets/{target_id}/verify")' in backend
assert 'expected = f"sh-verification={target.verification_token}"' in backend
assert '_resolve_public_ips(target.domain)' in backend

# Scanner identities remain absent from the target onboarding UI.
for internal_name in ("Nikto", "Nuclei", "Nmap"):
    assert internal_name not in frontend

print("product UX step 2 tests: OK")

# A verified website must not falsely promise scan readiness when customer or
# entitlement setup is still missing. The verified target continues to the
# dashboard, where the authoritative readiness prerequisites are shown.
assert "Ownership is verified. Product access is checked before scanning." in frontend
assert '>Continue <Icon name="arrow-right"' in frontend
assert "Finish setup to continue" not in frontend
assert "Website verified" in frontend
assert "Activation required" in frontend

# Customer-facing shell uses SkullHarbor branding only; repository name stays internal.
assert '/ UI-SCANNER' not in frontend


# Security regression: selecting/typing a target must NEVER switch customer
# identity based on another customer's ownership record. Customer context is
# fixed first; targets and scan history are then loaded only for that customer.
assert 'const owned=targets.find(t=>t.status==="verified"' not in frontend
assert 'fetch(`${API}/api/scans?user_id=${encodeURIComponent(effectiveId)}`)' in frontend
assert 'fetch(`${API}/api/targets?user_id=${encodeURIComponent(effectiveId)}`)' in frontend


# Legacy verified targets from before customer scoping are migrated without a
# second DNS challenge, but only with deterministic local ownership provenance.
assert "def _migrate_legacy_verified_targets" in backend
assert 'Target.status == "verified", Target.user_id.is_(None)' in backend
assert "len(scan_user_ids) == 1" in backend
assert "len(all_users) == 1" in backend
assert "target.user_id = owner_id" in backend

# Fix5 regression: legacy projects can contain several local customer rows. If
# exactly one is approved AND has usable self-service access, an already verified
# pre-scoping target is deterministically attached to that customer. This is the
# real upgrade path that the previous single-user-only migration missed.
assert 'eligible_user_ids = []' in backend
assert 'sole_eligible_user_id = eligible_user_ids[0] if len(eligible_user_ids) == 1 else None' in backend
assert 'elif sole_eligible_user_id is not None:' in backend
assert 'owner_id = sole_eligible_user_id' in backend
