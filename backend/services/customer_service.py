from datetime import UTC, datetime, timedelta
import base64, os, uuid, secrets
from pathlib import Path as _Path
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models import Engagement, EngagementAudit, EngagementScope, Entitlement, EntitlementInstallation, EntitlementLifecycleAudit, Finding, Scan, Target, User, VerificationReviewAudit
from schemas.api import TrustedReviewContext

CUSTOMER_VERIFICATION_STATES = {"pending", "approved", "rejected", "suspended"}
TRUSTED_REVIEW_ROLES = {"trusted-reviewer", "admin"}
TRUSTED_REVIEW_DECISIONS = {"approved", "rejected", "suspended"}
TRUSTED_REVIEW_TRANSITIONS = {
    "pending": {"approved", "rejected"},
    "approved": {"suspended"},
    "rejected": {"approved"},
    "suspended": {"approved", "rejected"},
}


def _company_profile_complete(user: User) -> bool:
    return bool(
        user.company_profile_submitted_at
        and (user.company_name or "").strip()
        and (user.company_domain or "").strip()
        and len((user.intended_use or "").strip()) >= 10
    )


def _apply_trusted_review(
    db: Session,
    user_id: int,
    decision: str,
    context: TrustedReviewContext,
    reason: str | None = None,
) -> dict:
    """Internal trust boundary. Never expose this as a customer mutation API.

    The future signed/remote entitlement authority may call an equivalent
    trusted adapter, but targets, scans, findings and raw scanner data are not
    inputs to this decision.
    """
    actor_id = (context.actor_id or "").strip()
    actor_role = (context.actor_role or "").strip().lower()
    source = (context.source or "").strip()
    decision = (decision or "").strip().lower()
    clean_reason = (reason or "").strip() or None

    if actor_role not in TRUSTED_REVIEW_ROLES or not actor_id:
        raise HTTPException(403, "Trusted reviewer authorization is required")
    if len(actor_id) > 120:
        raise HTTPException(400, "Reviewer identity is too long")
    if source != "trusted-admin":
        raise HTTPException(403, "Untrusted review source")
    if decision not in TRUSTED_REVIEW_DECISIONS:
        raise HTTPException(400, "Invalid review decision")
    if clean_reason and len(clean_reason) > 500:
        raise HTTPException(400, "Review reason is too long")
    if decision == "rejected" and not clean_reason:
        raise HTTPException(400, "A rejection reason is required")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Customer not found")
    if decision == "approved" and not _company_profile_complete(user):
        raise HTTPException(409, "Complete customer/company verification data is required before approval")

    current = (user.verification_status or "pending").strip().lower()
    if current not in CUSTOMER_VERIFICATION_STATES:
        raise HTTPException(409, "Customer verification state is invalid")
    if decision not in TRUSTED_REVIEW_TRANSITIONS[current]:
        raise HTTPException(409, f"Review transition {current} -> {decision} is not allowed")

    now = datetime.utcnow()
    audit = VerificationReviewAudit(
        user_id=user.id,
        actor_id=actor_id,
        actor_role=actor_role,
        source=source,
        from_status=current,
        to_status=decision,
        reason=clean_reason,
        created_at=now,
    )
    user.verification_status = decision
    user.verification_updated_at = now
    db.add(audit)
    db.commit()
    db.refresh(user)
    db.refresh(audit)
    return {
        "customer": _customer_record(user),
        "review": {
            "id": audit.id,
            "from_status": audit.from_status,
            "to_status": audit.to_status,
            "reason": audit.reason,
            "reviewed_at": audit.created_at,
        },
    }


def _customer_record(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "verification_status": user.verification_status,
        "verification_updated_at": user.verification_updated_at,
        "company_name": user.company_name,
        "company_domain": user.company_domain,
        "intended_use": user.intended_use,
        "company_profile_submitted_at": user.company_profile_submitted_at,
        "created_at": user.created_at,
    }


def _require_approved_customer(db: Session, user_id: int | None) -> User:
    # Downloaded/local architecture: this is the local enforcement point.
    # Step 1 deliberately provides no customer-facing way to change approval.
    # A later trusted entitlement/approval source may populate the cached state.
    if user_id is None:
        raise HTTPException(403, "An approved SkullHarbor customer is required before scanning")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(400, "Unknown user_id")
    if user.verification_status != "approved":
        raise HTTPException(403, "Customer verification is required before scanning")
    return user


ENTITLEMENT_AUTHORITY_STATES = {"active", "trial", "expired", "no_seat", "blocked"}
ENTITLEMENT_PRODUCT_KEYS = {"free", "monthly", "annual"}
TRIAL_MAX_DAYS = 7
ENTITLEMENT_TRUSTED_ROLES = {"entitlement-admin", "admin"}
ENTITLEMENT_INSTALLATION_STATES = {"active", "released"}


