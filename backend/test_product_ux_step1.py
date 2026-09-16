"""Sprint 8 / Step 1: customer-safe product readiness UX."""
import os
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

fd, db_path = tempfile.mkstemp(prefix="ui-scanner-s8-step1-", suffix=".db")
os.close(fd)
os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

try:
    import main
    from models import Entitlement, Engagement, EngagementScope, Target, User

    now = datetime.now(UTC).replace(tzinfo=None)
    with main.SessionLocal() as db:
        pending = User(name="Pending", email="pending-s8@example.invalid", verification_status="pending")
        ready = User(name="Ready", email="ready-s8@example.invalid", verification_status="approved")
        db.add_all([pending, ready]); db.commit(); db.refresh(pending); db.refresh(ready)

        blocked = main._product_ux_status(db, pending)
        assert blocked["ready_for_quick_check"] is False
        assert blocked["verification"] == "pending"
        assert blocked["access"] == "BLOCKED"

        db.add(Entitlement(user_id=ready.id, product_key="monthly", authority_status="active",
                           valid_until=now + timedelta(days=30), license_id="LIC-S8-READY", seat_limit=1,
                           source="entitlement-authority", updated_at=now))
        db.commit()
        no_scope = main._product_ux_status(db, ready)
        assert no_scope["product"] == "SkullHarbor Advanced"
        assert no_scope["access"] == "ACTIVE"
        assert no_scope["ready_for_quick_check"] is False
        assert no_scope["authorized_targets"] == 0 and no_scope["active_engagements"] == 0

        db.add(Target(domain="owned-s8.example.com", verification_token="token", status="verified", user_id=ready.id))
        db.commit()
        owned = main._product_ux_status(db, ready)
        assert owned["ready_for_quick_check"] is True
        assert owned["authorized_targets"] == 1

        # An active exact-host engagement also counts as available scope, but the
        # UX summary exposes only a count -- never hostnames, scan IDs or findings.
        target = db.query(Target).filter(Target.user_id == ready.id).first(); db.delete(target); db.commit()
        eng = Engagement(user_id=ready.id, reference="ENG-S8", customer_name="Client", status="approved",
                         valid_from=now - timedelta(minutes=1), valid_until=now + timedelta(days=1), approved_by="reviewer")
        db.add(eng); db.flush(); db.add(EngagementScope(engagement_id=eng.id, hostname="client-s8.example.com")); db.commit()
        engaged = main._product_ux_status(db, ready)
        assert engaged["ready_for_quick_check"] is True and engaged["active_engagements"] == 1
        forbidden = {"target", "hostname", "scan_id", "finding", "raw_output", "scanner", "verification_token"}
        assert not (set(engaged) & forbidden)

    source = Path(main.__file__).read_text(encoding="utf-8")
    assert '@app.get("/api/users/{user_id}/product-status")' in source
    frontend = (Path(main.__file__).parent.parent / "frontend" / "src" / "main.jsx").read_text(encoding="utf-8")
    assert "ready_for_quick_check" in frontend
    assert "Your access and scope are checked again by SkullHarbor when the scan starts." in frontend

    print("product UX step 1 tests: OK")
finally:
    try: os.unlink(db_path)
    except FileNotFoundError: pass
