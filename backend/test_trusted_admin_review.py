"""Sprint 5 / Step 3: trusted/admin review boundary and audit trail."""
import os
import tempfile
from pathlib import Path

fd, db_path = tempfile.mkstemp(prefix="ui-scanner-review-", suffix=".db")
os.close(fd)
os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

try:
    import main
    from fastapi import HTTPException
    from models import User, VerificationReviewAudit

    trusted = main.TrustedReviewContext(actor_id="reviewer-01", actor_role="trusted-reviewer")
    admin = main.TrustedReviewContext(actor_id="admin-01", actor_role="admin")

    with main.SessionLocal() as db:
        incomplete = User(name="Incomplete", email="incomplete@example.invalid", verification_status="pending")
        db.add(incomplete); db.commit(); db.refresh(incomplete)
        try:
            main._apply_trusted_review(db, incomplete.id, "approved", trusted)
            raise AssertionError("incomplete customer was approved")
        except HTTPException as exc:
            assert exc.status_code == 409

        user = User(
            name="Review Me", email="review@example.invalid", verification_status="pending",
            company_name="Example GmbH", company_domain="example.com",
            intended_use="Authorized security checks of company-owned web systems.",
            company_profile_submitted_at=main.datetime(2026, 9, 15, 9, 0, 0),
        )
        db.add(user); db.commit(); db.refresh(user)

        # Untrusted/local customer input cannot cross the review boundary.
        for bad in (
            main.TrustedReviewContext(actor_id="customer-1", actor_role="customer"),
            main.TrustedReviewContext(actor_id="", actor_role="admin"),
            main.TrustedReviewContext(actor_id="admin-1", actor_role="admin", source="customer-api"),
        ):
            try:
                main._apply_trusted_review(db, user.id, "approved", bad)
                raise AssertionError("unauthorized review succeeded")
            except HTTPException as exc:
                assert exc.status_code == 403

        result = main._apply_trusted_review(db, user.id, "approved", trusted)
        assert result["customer"]["verification_status"] == "approved"
        assert result["review"]["from_status"] == "pending"
        assert result["review"]["to_status"] == "approved"
        assert main._require_approved_customer(db, user.id).id == user.id

        # Same-state/direct invalid transitions fail closed.
        try:
            main._apply_trusted_review(db, user.id, "approved", admin)
            raise AssertionError("approved -> approved was allowed")
        except HTTPException as exc:
            assert exc.status_code == 409

        result = main._apply_trusted_review(db, user.id, "suspended", admin, "Security review required")
        assert result["customer"]["verification_status"] == "suspended"
        try:
            main._require_approved_customer(db, user.id)
            raise AssertionError("suspended customer could scan")
        except HTTPException as exc:
            assert exc.status_code == 403

        # Rejection always needs a controlled reason.
        try:
            main._apply_trusted_review(db, user.id, "rejected", trusted)
            raise AssertionError("reasonless rejection was allowed")
        except HTTPException as exc:
            assert exc.status_code == 400
        result = main._apply_trusted_review(db, user.id, "rejected", trusted, "Company authorization could not be verified")
        assert result["customer"]["verification_status"] == "rejected"

        # A trusted reviewer may approve after remediation/re-review.
        result = main._apply_trusted_review(db, user.id, "approved", trusted, "Verification completed")
        assert result["customer"]["verification_status"] == "approved"

        audits = db.query(VerificationReviewAudit).filter_by(user_id=user.id).order_by(VerificationReviewAudit.id).all()
        assert [(a.from_status, a.to_status) for a in audits] == [
            ("pending", "approved"), ("approved", "suspended"),
            ("suspended", "rejected"), ("rejected", "approved"),
        ]
        # Audit records contain review metadata only, never scan/target/finding payloads.
        audit_columns = {c.name for c in VerificationReviewAudit.__table__.columns}
        for forbidden in ("target", "scan", "finding", "raw_output", "verification_token"):
            assert forbidden not in audit_columns

    source = (Path(main.__file__).parent / "schemas" / "api.py").read_text(encoding="utf-8").lower()
    # Step 3 remains an internal trusted boundary: no customer-facing decision endpoint.
    for forbidden_route in (
        '@router.post("/api/users/{user_id}/approve")',
        '@router.post("/api/users/{user_id}/reject")',
        '@router.post("/api/users/{user_id}/suspend")',
        '@router.post("/api/admin', '@router.patch("/api/users/{user_id}")',
    ):
        assert forbidden_route not in source

    # Customer-editable request models still cannot carry review state/authority.
    customer_surface = source.split("class scanrequest", 1)[1].split("class trustedreviewcontext", 1)[0]
    for forbidden in ("actor_role", "actor_id", "verification_status", "approved", "rejected", "suspended"):
        assert forbidden not in customer_surface

    print("trusted/admin review tests: OK")
finally:
    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass
