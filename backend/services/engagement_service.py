from datetime import UTC, datetime, timedelta
import base64, os, uuid, secrets
from pathlib import Path as _Path
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models import Engagement, EngagementAudit, EngagementScope, Entitlement, EntitlementInstallation, EntitlementLifecycleAudit, Finding, Scan, Target, User, VerificationReviewAudit
from schemas.api import TrustedReviewContext
from services.target_security import normalize_domain as _normalize_domain
from services.customer_service import _require_approved_customer
ENGAGEMENT_TRUSTED_ROLES = {"engagement-reviewer", "admin"}
ENGAGEMENT_TRUSTED_SOURCE = "engagement-authority"
ENGAGEMENT_STATES = {"approved", "revoked", "expired"}
def _validate_engagement_context(context: TrustedReviewContext) -> tuple[str, str]:
    actor_id = (context.actor_id or "").strip()
    actor_role = (context.actor_role or "").strip().lower()
    if not actor_id or len(actor_id) > 120 or actor_role not in ENGAGEMENT_TRUSTED_ROLES:
        raise HTTPException(403, "Trusted engagement authority is required")
    if context.source != ENGAGEMENT_TRUSTED_SOURCE:
        raise HTTPException(403, "Untrusted engagement source")
    return actor_id, actor_role


def _engagement_record(row: Engagement) -> dict:
    return {
        "id": row.id, "reference": row.reference, "customer_name": row.customer_name,
        "status": row.status, "valid_from": row.valid_from, "valid_until": row.valid_until,
        "scopes": sorted(scope.hostname for scope in row.scopes),
    }


def _approve_engagement(db: Session, user_id: int, reference: str, customer_name: str, hostnames: list[str],
                        valid_from: datetime, valid_until: datetime, context: TrustedReviewContext) -> dict:
    """Trusted engagement boundary. Exact hostnames only; no scan/result data is accepted."""
    actor_id, actor_role = _validate_engagement_context(context)
    user = _require_approved_customer(db, user_id)
    reference = (reference or "").strip()
    customer_name = (customer_name or "").strip()
    if not reference or len(reference) > 120 or len(customer_name) < 2 or len(customer_name) > 200:
        raise HTTPException(400, "Invalid engagement data")
    if db.query(Engagement).filter(Engagement.reference == reference).first():
        raise HTTPException(409, "Engagement reference already exists")
    if not hostnames or len(hostnames) > 100:
        raise HTTPException(400, "Engagement requires 1-100 exact hostnames")
    normalized = sorted({_normalize_domain(h) for h in hostnames})
    if len(normalized) != len(hostnames):
        raise HTTPException(400, "Duplicate engagement hostname")
    if valid_from.tzinfo is not None:
        valid_from = valid_from.astimezone(UTC).replace(tzinfo=None)
    if valid_until.tzinfo is not None:
        valid_until = valid_until.astimezone(UTC).replace(tzinfo=None)
    if valid_until <= valid_from or valid_until > valid_from + timedelta(days=366):
        raise HTTPException(400, "Invalid engagement validity")
    row = Engagement(user_id=user.id, reference=reference, customer_name=customer_name, status="approved",
                     valid_from=valid_from, valid_until=valid_until, approved_by=actor_id)
    db.add(row); db.flush()
    for hostname in normalized:
        db.add(EngagementScope(engagement_id=row.id, hostname=hostname))
    db.add(EngagementAudit(engagement_id=row.id, actor_id=actor_id, actor_role=actor_role, action="approved",
                           reference=reference, detail=f"{len(normalized)} exact host scope(s)"))
    db.commit(); db.refresh(row)
    return _engagement_record(row)


def _set_engagement_state(db: Session, engagement_id: int, state: str, context: TrustedReviewContext) -> dict:
    actor_id, actor_role = _validate_engagement_context(context)
    state = (state or "").strip().lower()
    if state not in {"revoked", "expired"}:
        raise HTTPException(400, "Invalid engagement state transition")
    row = db.get(Engagement, engagement_id)
    if not row:
        raise HTTPException(404, "Engagement not found")
    if row.status != "approved":
        raise HTTPException(409, "Engagement is already terminal")
    row.status = state
    db.add(EngagementAudit(engagement_id=row.id, actor_id=actor_id, actor_role=actor_role, action=state,
                           reference=row.reference))
    db.commit(); db.refresh(row)
    return _engagement_record(row)


def _authorized_engagement_for_scan(db: Session, hostname: str, user_id: int) -> Engagement | None:
    # Defense in depth: callers cannot use the engagement helper to bypass the
    # Sprint-5 customer gate, and matching always uses the canonical exact host.
    user = db.get(User, user_id)
    if not user or user.verification_status != "approved":
        return None
    try:
        hostname = _normalize_domain(hostname)
    except HTTPException:
        return None
    now = datetime.utcnow()
    return (db.query(Engagement).join(EngagementScope)
            .filter(Engagement.user_id == user_id, Engagement.status == "approved",
                    Engagement.valid_from <= now, Engagement.valid_until > now,
                    EngagementScope.hostname == hostname).first())

