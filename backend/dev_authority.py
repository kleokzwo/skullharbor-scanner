"""Development-only trusted authority bridge. Never package for production."""
from datetime import UTC, datetime, timedelta
import secrets
from fastapi import Depends, HTTPException
from database import get_db
from models import User
from schemas.api import TrustedReviewContext
from services.customer_service import _company_profile_complete, _apply_trusted_review
from services.entitlement_service import _issue_entitlement, _product_ux_status


def register_dev_authority(app):
    @app.get("/internal/development-authority/status")
    def dev_authority_status():
        return {"enabled": True, "mode": "development-only", "test_products": ["free", "monthly"]}

    def ensure_approved(db, user):
        if not _company_profile_complete(user):
            raise HTTPException(409, "Complete the organization profile before development approval")
        if user.verification_status != "approved":
            _apply_trusted_review(db, user.id, "approved", TrustedReviewContext(actor_id="local-development-reviewer", actor_role="admin", source="trusted-admin"), "Local development validation only")
        return db.get(User, user.id)

    @app.post("/internal/development-authority/users/{user_id}/access/{product_key}")
    def dev_set_test_access(user_id: int, product_key: str, db=Depends(get_db)):
        user = db.get(User, user_id)
        if not user: raise HTTPException(404, "Customer not found")
        product_key = (product_key or "").strip().lower()
        if product_key not in {"free", "monthly"}: raise HTTPException(400, "Development test access supports FREE or MONTHLY only")
        user = ensure_approved(db, user)
        now = datetime.now(UTC).replace(tzinfo=None)
        is_trial = product_key == "free"
        _issue_entitlement(db, user.id, product_key, TrustedReviewContext(actor_id="local-development-authority", actor_role="admin", source="entitlement-authority"), license_id=f"dev-{product_key}-{secrets.token_hex(8)}", seat_limit=1, valid_until=now + (timedelta(days=7) if is_trial else timedelta(days=30)), trial=is_trial)
        return _product_ux_status(db, db.get(User, user_id))

    @app.post("/internal/development-authority/users/{user_id}/approve-trial")
    def dev_approve_trial(user_id: int, db=Depends(get_db)):
        return dev_set_test_access(user_id, "free", db)
