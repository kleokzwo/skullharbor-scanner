"""Sprint 6 / Step 1: entitlement authority resolution and scan-policy gate."""
import os
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

fd, db_path = tempfile.mkstemp(prefix="ui-scanner-entitlement-", suffix=".db")
os.close(fd)
os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

try:
    import main
    from fastapi import HTTPException
    from models import Entitlement, User

    def utc_now():
        return datetime.now(UTC).replace(tzinfo=None)

    def customer(db, email, verification="approved"):
        row = User(name="Entitlement Test", email=email, verification_status=verification)
        db.add(row); db.commit(); db.refresh(row)
        return row

    def grant(db, user, product, status, valid_until=None, source="entitlement-authority"):
        row = Entitlement(user_id=user.id, product_key=product, authority_status=status,
                          valid_until=valid_until, source=source)
        db.add(row); db.commit(); db.refresh(row)
        return row

    with main.SessionLocal() as db:
        no_grant = customer(db, "none@example.invalid")
        assert main._entitlement_record(db, no_grant)["status"] == "BLOCKED"

        pending = customer(db, "pending@example.invalid", "pending")
        grant(db, pending, "monthly", "active")
        assert main._entitlement_record(db, pending)["status"] == "BLOCKED"

        trial = customer(db, "trial@example.invalid")
        grant(db, trial, "monthly", "trial", utc_now() + timedelta(days=7))
        resolved = main._require_scan_entitlement(db, trial)
        assert resolved["status"] == "TRIAL"
        assert resolved["scan_profile"] == "free"

        # Trial policy is exactly seven days maximum and requires an expiry.
        trial_without_expiry = customer(db, "trial-no-expiry@example.invalid")
        grant(db, trial_without_expiry, "free", "trial")
        assert main._entitlement_record(db, trial_without_expiry)["status"] == "BLOCKED"

        overlong_trial = customer(db, "trial-overlong@example.invalid")
        grant(db, overlong_trial, "free", "trial", utc_now() + timedelta(days=8))
        assert main._entitlement_record(db, overlong_trial)["status"] == "BLOCKED"

        monthly = customer(db, "monthly@example.invalid")
        grant(db, monthly, "monthly", "active", utc_now() + timedelta(days=30))
        resolved = main._require_scan_entitlement(db, monthly)
        assert resolved["status"] == "ACTIVE"
        assert resolved["scan_profile"] == "monthly"

        expired = customer(db, "expired@example.invalid")
        grant(db, expired, "monthly", "active", utc_now() - timedelta(seconds=1))
        assert main._entitlement_record(db, expired)["status"] == "EXPIRED"

        no_seat = customer(db, "seat@example.invalid")
        grant(db, no_seat, "monthly", "no_seat")
        assert main._entitlement_record(db, no_seat)["status"] == "NO_SEAT"

        blocked = customer(db, "blocked@example.invalid")
        grant(db, blocked, "monthly", "blocked")
        try:
            main._require_scan_entitlement(db, blocked)
            raise AssertionError("blocked entitlement was allowed")
        except HTTPException as exc:
            assert exc.status_code == 403

        managed = customer(db, "annual@example.invalid")
        grant(db, managed, "annual", "active")
        try:
            main._require_scan_entitlement(db, managed)
            raise AssertionError("managed annual entitlement reached self-service")
        except HTTPException as exc:
            assert exc.status_code == 403

        untrusted = customer(db, "untrusted@example.invalid")
        grant(db, untrusted, "monthly", "active", source="local-customer")
        assert main._entitlement_record(db, untrusted)["status"] == "BLOCKED"

    source = (Path(main.__file__).parent / "schemas" / "api.py").read_text(encoding="utf-8").lower()
    request_block = source.split("class scanrequest", 1)[1].split("class userrequest", 1)[0]
    for forbidden in ("entitlement", "license", "subscription", "tier", "profile", "authority_status"):
        assert forbidden not in request_block
    assert '@app.post("/api/users/{user_id}/entitlement")' not in source
    assert '@app.put("/api/users/{user_id}/entitlement")' not in source

    columns = {c.name for c in Entitlement.__table__.columns}
    assert not ({"target", "scan", "finding", "raw_output", "verification_token"} & columns)

    print("entitlement authority step 1 tests: OK")
finally:
    try: os.unlink(db_path)
    except FileNotFoundError: pass
