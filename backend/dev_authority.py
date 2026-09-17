"""Development-only trusted authority bridge.

Loaded only when the repository marker `.skullharbor-development` exists.
Production packaging must omit both the marker and this module.  The bridge
uses the same trusted review/entitlement primitives as the real authority; it
never weakens /api/scan or accepts scan/target/finding data.
"""
from datetime import UTC, datetime, timedelta
import secrets
from fastapi import HTTPException


def register_dev_authority(app, main):
    @app.get("/internal/development-authority/status")
    def dev_authority_status():
        return {"enabled": True, "mode": "development-only", "test_products": ["free", "monthly"]}

    def ensure_approved(db, user):
        if not main._company_profile_complete(user):
            raise HTTPException(409, "Complete the organization profile before development approval")
        if user.verification_status != "approved":
            main._apply_trusted_review(
                db, user.id, "approved",
                main.TrustedReviewContext(actor_id="local-development-reviewer", actor_role="admin", source="trusted-admin"),
                "Local development validation only",
            )
        return db.get(main.User, user.id)

    @app.post("/internal/development-authority/users/{user_id}/access/{product_key}")
    def dev_set_test_access(user_id: int, product_key: str, db=main.Depends(main.get_db)):
        user = db.get(main.User, user_id)
        if not user:
            raise HTTPException(404, "Customer not found")
        product_key = (product_key or "").strip().lower()
        if product_key not in {"free", "monthly"}:
            raise HTTPException(400, "Development test access supports FREE or MONTHLY only")
        user = ensure_approved(db, user)
        now = datetime.now(UTC).replace(tzinfo=None)
        # FREE deliberately exercises the real bounded trial rule. MONTHLY is
        # an ACTIVE development subscription so its monthly scan policy is used.
        is_trial = product_key == "free"
        valid_until = now + (timedelta(days=7) if is_trial else timedelta(days=30))
        main._issue_entitlement(
            db, user.id, product_key,
            main.TrustedReviewContext(actor_id="local-development-authority", actor_role="admin", source="entitlement-authority"),
            license_id=f"dev-{product_key}-{secrets.token_hex(8)}",
            seat_limit=1,
            valid_until=valid_until,
            trial=is_trial,
        )
        return main._product_ux_status(db, db.get(main.User, user_id))

    # Compatibility for development databases/UI from Fix8/9/10.
    @app.post("/internal/development-authority/users/{user_id}/approve-trial")
    def dev_approve_trial(user_id: int, db=main.Depends(main.get_db)):
        return dev_set_test_access(user_id, "free", db)
