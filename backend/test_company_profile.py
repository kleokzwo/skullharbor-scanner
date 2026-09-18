"""Sprint 5 / Step 2: minimal company review data without approval escalation."""
import os
import tempfile
from pathlib import Path

fd, db_path = tempfile.mkstemp(prefix="ui-scanner-company-", suffix=".db")
os.close(fd)
os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

try:
    import main
    from models import User

    with main.SessionLocal() as db:
        user = User(name="Pending", email="pending-company@example.invalid", verification_status="pending")
        db.add(user)
        db.commit()
        db.refresh(user)

        req = main.CompanyProfileRequest(
            company_name="Example GmbH",
            company_domain="https://example.com/about",
            intended_use="Authorized security checks of company-owned web systems.",
        )
        result = main.update_company_profile(user.id, req, db)
        assert result["company_name"] == "Example GmbH"
        assert result["company_domain"] == "example.com"
        assert result["intended_use"].startswith("Authorized security")
        assert result["company_profile_submitted_at"] is not None
        assert result["verification_status"] == "pending"

        db.refresh(user)
        assert user.verification_status == "pending"

        # Updating profile data must not undo an enforcement decision.
        user.verification_status = "suspended"
        db.commit()
        result = main.update_company_profile(user.id, req, db)
        assert result["verification_status"] == "suspended"

    source = (Path(main.__file__).parent / "schemas" / "api.py").read_text(encoding="utf-8").lower()
    request_src = source.split("class companyprofilerequest", 1)[1].split("class trustedreviewcontext", 1)[0]
    for forbidden in ("verification_status", "approved", "rejected", "suspended", "scan_profile", "tier", "license"):
        assert forbidden not in request_src, f"company profile request can influence protected state: {forbidden}"

    controller_source = (Path(main.__file__).parent / "controllers" / "customer_controller.py").read_text(encoding="utf-8").lower()
    endpoint_src = controller_source.split("def update_company_profile", 1)[1].split('@router.get("/api/users/{user_id}/product-status")', 1)[0]
    assert "verification_status =" not in endpoint_src
    assert "_resolve_public_ips" not in endpoint_src  # company identity is not target authorization
    assert "_authorized_target_for_scan" not in endpoint_src

    print("company verification data tests: OK")
finally:
    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass
