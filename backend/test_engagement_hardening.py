"""Sprint 7 / Step 2: engagement authorization hardening and local provenance."""
import os
import tempfile
from datetime import UTC, datetime, timedelta

fd, db_path = tempfile.mkstemp(prefix="ui-scanner-engagement-hardening-", suffix=".db")
os.close(fd)
os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

try:
    import main
    from fastapi import HTTPException
    from models import Engagement, EngagementAudit, Scan, User

    trusted = main.TrustedReviewContext(actor_id="reviewer-2", actor_role="engagement-reviewer", source="engagement-authority")
    now = datetime.now(UTC)

    with main.SessionLocal() as db:
        user = User(name="Pentester", email="hardening@example.invalid", verification_status="approved")
        db.add(user); db.commit(); db.refresh(user)
        main._approve_engagement(db, user.id, "ENG-HARD", "Example Customer", ["API.Example.COM."], now - timedelta(minutes=1), now + timedelta(days=2), trusted)
        eng = db.query(Engagement).filter(Engagement.reference == "ENG-HARD").one()

        # Matching is canonical but remains exact-host only.
        assert main._authorized_engagement_for_scan(db, "api.example.com", user.id).id == eng.id
        assert main._authorized_engagement_for_scan(db, "API.EXAMPLE.COM.", user.id).id == eng.id
        assert main._authorized_engagement_for_scan(db, "child.api.example.com", user.id) is None
        assert main._authorized_engagement_for_scan(db, "not a host", user.id) is None

        # Defense in depth: suspension immediately invalidates the engagement helper itself.
        user.verification_status = "suspended"; db.commit()
        assert main._authorized_engagement_for_scan(db, "api.example.com", user.id) is None
        user.verification_status = "approved"; db.commit()

        # Failed lifecycle attempts are non-mutating and do not create audit decisions.
        before = db.query(EngagementAudit).filter(EngagementAudit.engagement_id == eng.id).count()
        try:
            main._set_engagement_state(db, eng.id, "approved", trusted)
            raise AssertionError("invalid transition was accepted")
        except HTTPException as exc:
            assert exc.status_code == 400
        db.refresh(eng)
        assert eng.status == "approved"
        assert db.query(EngagementAudit).filter(EngagementAudit.engagement_id == eng.id).count() == before

        # Local scan provenance has a dedicated engagement FK; authority audit still has no scan linkage.
        assert "engagement_id" in {c.name for c in Scan.__table__.columns}
        audit_cols = {c.name.lower() for c in EngagementAudit.__table__.columns}
        assert "scan_id" not in audit_cols and "target" not in audit_cols and "finding" not in audit_cols

    print("engagement hardening step 2 tests: OK")
finally:
    try: os.unlink(db_path)
    except FileNotFoundError: pass
