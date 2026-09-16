"""Sprint 7 / Step 3: scope/engagement security closeout."""
import os
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

fd, db_path = tempfile.mkstemp(prefix="ui-scanner-s7-closeout-", suffix=".db")
os.close(fd)
os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

try:
    import main
    from fastapi import HTTPException
    from models import EngagementAudit, Target, User

    trusted = main.TrustedReviewContext(actor_id="reviewer-closeout", actor_role="engagement-reviewer", source="engagement-authority")
    now = datetime.now(UTC)

    with main.SessionLocal() as db:
        owner = User(name="Owner", email="owner-s7@example.invalid", verification_status="approved")
        other = User(name="Other", email="other-s7@example.invalid", verification_status="approved")
        db.add_all([owner, other]); db.commit(); db.refresh(owner); db.refresh(other)

        eng = main._approve_engagement(db, owner.id, "ENG-CLOSE", "Closeout Customer", ["scope.example.com"], now - timedelta(minutes=1), now + timedelta(days=1), trusted)

        # Cross-customer scope reuse fails closed.
        assert main._authorized_engagement_for_scan(db, "scope.example.com", other.id) is None
        try:
            main._scan_authorization(db, "scope.example.com", other.id)
            raise AssertionError("cross-customer engagement reuse was accepted")
        except HTTPException as exc:
            assert exc.status_code == 403

        # The decision returns the exact engagement used for local provenance.
        target, engagement = main._scan_authorization(db, "SCOPE.EXAMPLE.COM.", owner.id)
        assert target is None and engagement is not None
        assert engagement.id == eng["id"]

        # Verified ownership takes precedence and never attaches engagement provenance.
        owned = Target(domain="scope.example.com", verification_token="local-test-token", status="verified", user_id=owner.id)
        db.add(owned); db.commit(); db.refresh(owned)
        target, engagement = main._scan_authorization(db, "scope.example.com", owner.id)
        assert target.id == owned.id and engagement is None

        # Revocation immediately removes the engagement path once ownership is absent.
        db.delete(owned); db.commit()
        main._set_engagement_state(db, eng["id"], "revoked", trusted)
        try:
            main._scan_authorization(db, "scope.example.com", owner.id)
            raise AssertionError("revoked engagement authorized a scan")
        except HTTPException as exc:
            assert exc.status_code == 403

        # Authority audit remains trust metadata only.
        forbidden = {"scan_id", "target", "finding", "raw_output", "scanner", "verification_token"}
        assert not ({c.name.lower() for c in EngagementAudit.__table__.columns} & forbidden)

    source = Path(main.__file__).read_text(encoding="utf-8")
    scan_block = source[source.index('@app.post("/api/scan")'):]
    assert "verified_target, engagement = _scan_authorization" in scan_block
    assert "_authorized_target_for_scan(db, hostname, req.user_id)" not in scan_block

    print("sprint 7 security closeout tests: OK")
finally:
    try: os.unlink(db_path)
    except FileNotFoundError: pass
