"""Sprint 5 / Step 1: customer approval state and local enforcement."""
import os
import tempfile
from pathlib import Path

fd, db_path = tempfile.mkstemp(prefix="ui-scanner-customer-", suffix=".db")
os.close(fd)
os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

try:
    import main
    from fastapi import HTTPException
    from models import User

    with main.SessionLocal() as db:
        states = ("pending", "rejected", "suspended")
        for i, state in enumerate(states):
            user = User(name=f"Blocked {state}", email=f"{state}{i}@example.invalid", verification_status=state)
            db.add(user)
            db.commit()
            db.refresh(user)
            try:
                main._require_approved_customer(db, user.id)
                raise AssertionError(f"{state} customer was allowed")
            except HTTPException as exc:
                assert exc.status_code == 403

        approved = User(name="Approved", email="approved@example.invalid", verification_status="approved")
        db.add(approved)
        db.commit()
        db.refresh(approved)
        assert main._require_approved_customer(db, approved.id).id == approved.id

        try:
            main._require_approved_customer(db, None)
            raise AssertionError("anonymous scan eligibility was allowed")
        except HTTPException as exc:
            assert exc.status_code == 403

    # The customer request surface must not contain an approval/status setter.
    schema_source = (Path(main.__file__).parent / "schemas" / "api.py").read_text(encoding="utf-8").lower()
    scan_req = schema_source.split("class scanrequest", 1)[1].split("class userrequest", 1)[0]
    source = (Path(main.__file__).parent / "controllers" / "customer_controller.py").read_text(encoding="utf-8").lower()
    for forbidden in ("verification_status", "approved", "suspended", "rejected"):
        assert forbidden not in scan_req

    # Step 1 intentionally has no public approval mutation endpoint.
    assert '@router.post("/api/users/{user_id}/approve")' not in source
    assert '@router.patch("/api/users/{user_id}")' not in source

    # New accounts are explicitly pending.
    create_user_src = source.split("def create_user", 1)[1].split('@router.get("/api/users/{user_id}/product-status")', 1)[0]
    assert 'verification_status="pending"' in create_user_src

    print("customer verification gate tests: OK")
finally:
    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass
