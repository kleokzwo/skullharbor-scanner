"""Sprint 6 / Step 2: trusted issuance, seat and installation lifecycle."""
import os, tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
fd, db_path = tempfile.mkstemp(prefix="ui-scanner-lifecycle-", suffix=".db"); os.close(fd)
os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
try:
    import main
    from fastapi import HTTPException
    from models import Entitlement, EntitlementInstallation, EntitlementLifecycleAudit, User
    now = lambda: datetime.now(UTC).replace(tzinfo=None)
    trusted = main.TrustedReviewContext(actor_id="authority-1", actor_role="entitlement-admin", source="entitlement-authority")
    admin = main.TrustedReviewContext(actor_id="admin-1", actor_role="admin", source="entitlement-authority")
    untrusted = main.TrustedReviewContext(actor_id="customer", actor_role="customer", source="entitlement-authority")
    with main.SessionLocal() as db:
        user = User(name="Lifecycle", email="life@example.invalid", verification_status="approved")
        db.add(user); db.commit(); db.refresh(user)
        r = main._issue_entitlement(db, user.id, "monthly", trusted, license_id="lic-001", seat_limit=1, valid_until=now()+timedelta(days=30))
        assert r["status"] == "ACTIVE" and r["seat_limit"] == 1 and r["active_installations"] == 0
        assert main._bind_installation(db, user.id, "install-A", trusted)["status"] == "ACTIVE"
        assert main._entitlement_record(db, user)["active_installations"] == 1
        try:
            main._bind_installation(db, user.id, "install-A", untrusted); raise AssertionError("idempotent bind bypassed authority")
        except HTTPException as exc: assert exc.status_code == 403
        try:
            main._bind_installation(db, user.id, "install-B", trusted); raise AssertionError("seat limit bypassed")
        except HTTPException as exc: assert exc.status_code == 409
        assert main._release_installation(db, user.id, "install-A", admin)["status"] == "RELEASED"
        assert main._bind_installation(db, user.id, "install-B", trusted)["status"] == "ACTIVE"
        try:
            main._issue_entitlement(db, user.id, "monthly", untrusted, license_id="lic-002")
            raise AssertionError("untrusted issuance allowed")
        except HTTPException as exc: assert exc.status_code == 403
        blocked = main._set_entitlement_state(db, user.id, "blocked", trusted, "subscription ended")
        assert blocked["status"] == "BLOCKED"
        try:
            main._bind_installation(db, user.id, "install-C", trusted); raise AssertionError("blocked license bound installation")
        except HTTPException as exc: assert exc.status_code == 403
        pending = User(name="Pending", email="pending-life@example.invalid", verification_status="pending")
        db.add(pending); db.commit(); db.refresh(pending)
        try:
            main._issue_entitlement(db, pending.id, "monthly", trusted, license_id="lic-pending")
            raise AssertionError("unapproved customer received license")
        except HTTPException as exc: assert exc.status_code == 403
        trial_user = User(name="Trial", email="trial-life@example.invalid", verification_status="approved")
        db.add(trial_user); db.commit(); db.refresh(trial_user)
        tr = main._issue_entitlement(db, trial_user.id, "free", trusted, license_id="trial-001", valid_until=now()+timedelta(days=7), trial=True)
        assert tr["status"] == "TRIAL" and tr["scan_profile"] == "free"
        try:
            main._issue_entitlement(db, trial_user.id, "free", trusted, license_id="trial-bad", valid_until=now()+timedelta(days=8), trial=True)
            raise AssertionError("overlong trial issued")
        except HTTPException as exc: assert exc.status_code == 400
        assert db.query(EntitlementLifecycleAudit).filter(EntitlementLifecycleAudit.user_id == user.id).count() == 5
        cols = {c.name for c in EntitlementLifecycleAudit.__table__.columns} | {c.name for c in EntitlementInstallation.__table__.columns}
        assert not ({"target", "scan", "finding", "raw_output", "verification_token"} & cols)
    source = Path(main.__file__).read_text(encoding="utf-8").lower()
    for method in ("post", "put", "patch", "delete"):
        assert f'@app.{method}("/api/users/{{user_id}}/entitlement' not in source
    print("entitlement lifecycle step 2 tests: OK")
finally:
    try: os.unlink(db_path)
    except FileNotFoundError: pass
