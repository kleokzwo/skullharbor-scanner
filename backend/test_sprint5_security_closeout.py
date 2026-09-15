"""Sprint 5 / Step 4: security regression suite and closeout assertions."""
import os
import tempfile

from pydantic import ValidationError

fd, db_path = tempfile.mkstemp(prefix="ui-scanner-sprint5-closeout-", suffix=".db")
os.close(fd)
os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

try:
    import main
    from fastapi import HTTPException
    from models import User, VerificationReviewAudit

    # Customer request models fail closed on protected/unknown fields instead
    # of silently accepting attempted status/tier/scanner manipulation.
    hostile_requests = (
        (main.UserRequest, {"name": "Mallory", "email": "m@example.invalid", "verification_status": "approved"}),
        (main.CompanyProfileRequest, {
            "company_name": "Example GmbH", "company_domain": "example.com",
            "intended_use": "Authorized company security testing.", "actor_role": "admin",
        }),
        (main.ScanRequest, {"target": "https://example.com", "user_id": 1, "scan_profile": "monthly"}),
        (main.TargetRequest, {"domain": "example.com", "user_id": 1, "verification_status": "approved"}),
    )
    for model, payload in hostile_requests:
        try:
            model(**payload)
            raise AssertionError(f"{model.__name__} accepted a protected/unknown field")
        except ValidationError:
            pass

    with main.SessionLocal() as db:
        pending = User(name="Pending", email="pending-closeout@example.invalid", verification_status="pending")
        complete = User(
            name="Complete", email="complete-closeout@example.invalid", verification_status="pending",
            company_name="Example GmbH", company_domain="example.com",
            intended_use="Authorized company-owned web security checks.",
            company_profile_submitted_at=main.datetime(2026, 9, 15, 10, 0, 0),
        )
        db.add_all([pending, complete]); db.commit(); db.refresh(pending); db.refresh(complete)

        # The customer gate must run before target parsing/DNS resolution.
        original_validate = main.validate_target_url
        calls = []
        def should_not_run(_target):
            calls.append(_target)
            raise AssertionError("target validation ran before customer approval")
        main.validate_target_url = should_not_run
        try:
            try:
                main.scan(main.ScanRequest(target="https://example.com", user_id=pending.id), db)
                raise AssertionError("pending customer reached scan path")
            except HTTPException as exc:
                assert exc.status_code == 403
            assert calls == []
        finally:
            main.validate_target_url = original_validate

        trusted = main.TrustedReviewContext(actor_id="reviewer-closeout", actor_role="trusted-reviewer")
        before = db.query(VerificationReviewAudit).count()

        # Failed review attempts are fail-closed and create no audit decision.
        for decision, reason, expected in (
            ("approved", None, 409),  # incomplete company profile
            ("rejected", None, 400), # rejection reason required
            ("owner-approved", "x", 400), # unknown decision
        ):
            try:
                main._apply_trusted_review(db, pending.id, decision, trusted, reason)
                raise AssertionError(f"invalid review succeeded: {decision}")
            except HTTPException as exc:
                assert exc.status_code == expected
        assert db.query(VerificationReviewAudit).count() == before
        db.refresh(pending)
        assert pending.verification_status == "pending"

        # Reviewer identifiers are bounded before persistence.
        try:
            main._apply_trusted_review(
                db, complete.id, "approved",
                main.TrustedReviewContext(actor_id="r" * 121, actor_role="admin"),
            )
            raise AssertionError("oversized reviewer identity was accepted")
        except HTTPException as exc:
            assert exc.status_code == 400

        # Positive path still works and approval remains the scan eligibility gate.
        main._apply_trusted_review(db, complete.id, "approved", trusted, "Verification complete")
        assert main._require_approved_customer(db, complete.id).id == complete.id

        audit = db.query(VerificationReviewAudit).filter_by(user_id=complete.id).one()
        assert audit.from_status == "pending" and audit.to_status == "approved"
        audit_columns = {c.name for c in VerificationReviewAudit.__table__.columns}
        assert not ({"target", "scan", "finding", "raw_output", "verification_token"} & audit_columns)

    print("sprint 5 security closeout tests: OK")
finally:
    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass
