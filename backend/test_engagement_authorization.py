"""Sprint 7 / Step 1: trusted exact-host engagement authorization."""
import os
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

fd, db_path = tempfile.mkstemp(prefix="ui-scanner-engagement-", suffix=".db")
os.close(fd)
os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

try:
    import main
    from fastapi import HTTPException
    from models import Engagement, EngagementAudit, EngagementScope, User

    trusted = main.TrustedReviewContext(actor_id="reviewer-1", actor_role="engagement-reviewer", source="engagement-authority")
    untrusted = main.TrustedReviewContext(actor_id="customer", actor_role="engagement-reviewer", source="local-client")
    now = datetime.now(UTC).replace(tzinfo=None)

    with main.SessionLocal() as db:
        user = User(name="Pentester", email="pentester@example.invalid", verification_status="approved")
        pending = User(name="Pending", email="pending-eng@example.invalid", verification_status="pending")
        db.add_all([user, pending]); db.commit(); db.refresh(user); db.refresh(pending)

        # Customer/local software cannot self-approve an engagement.
        try:
            main._approve_engagement(db, user.id, "ENG-1", "Example Customer", ["app.example.com"], now, now + timedelta(days=7), untrusted)
            raise AssertionError("untrusted engagement approval was allowed")
        except HTTPException as exc:
            assert exc.status_code == 403

        # Customer verification remains an independent prerequisite.
        try:
            main._approve_engagement(db, pending.id, "ENG-2", "Example Customer", ["app.example.com"], now, now + timedelta(days=7), trusted)
            raise AssertionError("pending customer received an engagement")
        except HTTPException as exc:
            assert exc.status_code == 403

        record = main._approve_engagement(db, user.id, "ENG-3", "Example Customer", ["api.example.com", "www.example.com"], now - timedelta(minutes=1), now + timedelta(days=7), trusted)
        assert record["status"] == "approved"
        assert record["scopes"] == ["api.example.com", "www.example.com"]
        assert main._authorized_engagement_for_scan(db, "api.example.com", user.id) is not None
        assert main._authorized_engagement_for_scan(db, "example.com", user.id) is None
        assert main._authorized_engagement_for_scan(db, "other.example.com", user.id) is None

        # Engagement authorization is an alternative to DNS ownership, not a wildcard.
        assert main._authorized_target_for_scan(db, "api.example.com", user.id) is None
        try:
            main._authorized_target_for_scan(db, "outside.example.com", user.id)
            raise AssertionError("out-of-scope hostname was allowed")
        except HTTPException as exc:
            assert exc.status_code == 403

        # Revocation is terminal and immediately removes engagement authorization.
        engagement = db.query(Engagement).filter(Engagement.reference == "ENG-3").one()
        main._set_engagement_state(db, engagement.id, "revoked", trusted)
        assert main._authorized_engagement_for_scan(db, "api.example.com", user.id) is None
        try:
            main._set_engagement_state(db, engagement.id, "expired", trusted)
            raise AssertionError("terminal engagement was transitioned twice")
        except HTTPException as exc:
            assert exc.status_code == 409

        # Expired time windows never authorize even if the stored state says approved.
        old = main._approve_engagement(db, user.id, "ENG-OLD", "Old Customer", ["old.example.com"], now - timedelta(days=3), now - timedelta(days=1), trusted)
        assert old["status"] == "approved"
        assert main._authorized_engagement_for_scan(db, "old.example.com", user.id) is None

        # Data minimization: engagement trust storage has no scan/result/secret fields.
        forbidden = {"target", "scan", "finding", "raw_output", "verification_token", "scanner"}
        for model in (Engagement, EngagementScope, EngagementAudit):
            cols = {c.name.lower() for c in model.__table__.columns}
            assert not (cols & forbidden), (model.__name__, cols & forbidden)

    source = (Path(main.__file__).parent / "controllers" / "customer_controller.py").read_text(encoding="utf-8").lower()
    # Public surface is read-only for engagements; trusted decisions remain internal.
    assert '@router.get("/api/users/{user_id}/engagements")' in source
    for method in ("post", "put", "patch", "delete"):
        assert f'@router.{method}("/api/users/{{user_id}}/engagements' not in source

    print("engagement authorization step 1 tests: OK")
finally:
    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass
