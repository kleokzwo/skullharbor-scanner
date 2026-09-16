"""Development-only trusted authority bridge.

This module is deliberately NOT part of the customer trust surface. It is loaded
only when the repository marker `.skullharbor-development` exists. Production
packaging must omit both the marker and this module.
"""
from datetime import UTC, datetime, timedelta
import secrets
from fastapi import HTTPException


def register_dev_authority(app, main):
    @app.get("/internal/development-authority/status")
    def dev_authority_status():
        return {"enabled": True, "mode": "development-only"}

    @app.post("/internal/development-authority/users/{user_id}/approve-trial")
    def dev_approve_trial(user_id: int, db=main.Depends(main.get_db)):
        user = db.get(main.User, user_id)
        if not user:
            raise HTTPException(404, "Customer not found")
        if not main._company_profile_complete(user):
            raise HTTPException(409, "Complete the organization profile before development approval")

        if user.verification_status != "approved":
            main._apply_trusted_review(
                db, user.id, "approved",
                main.TrustedReviewContext(actor_id="local-development-reviewer", actor_role="admin", source="trusted-admin"),
                "Local development validation only",
            )

        user = db.get(main.User, user_id)
        ent = main._entitlement_record(db, user)
        if ent.get("status") not in {"ACTIVE", "TRIAL"}:
            now = datetime.now(UTC).replace(tzinfo=None)
            main._issue_entitlement(
                db, user.id, "free",
                main.TrustedReviewContext(actor_id="local-development-authority", actor_role="admin", source="entitlement-authority"),
                license_id=f"dev-{secrets.token_hex(8)}",
                seat_limit=1,
                valid_until=now + timedelta(days=7),
                trial=True,
            )
        return main._product_ux_status(db, db.get(main.User, user_id))
