from datetime import UTC, datetime, timedelta
import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Engagement, Entitlement, EntitlementInstallation, Finding, Scan, Target, User
from schemas.api import ActivationRequest, CompanyProfileRequest, ScanRequest, TargetRequest, UserRequest
from services.customer_service import _company_profile_complete, _apply_trusted_review, _customer_record, _require_approved_customer
from services.workspace_service import _installation_id, _bound_workspace_user, _require_workspace_customer, _activation_public_key
from services.engagement_service import _engagement_record, _authorized_engagement_for_scan
from services.entitlement_service import _entitlement_record, _require_scan_entitlement, _product_ux_status, _issue_entitlement
from services.verification_service import _migrate_legacy_verified_targets, _verification_record, _txt_values, _scan_authorization, _authorized_target_for_scan
from services.target_security import normalize_domain as _normalize_domain, resolve_public_ips as _resolve_public_ips, validate_target_url
from scan_profiles import public_product_catalog, require_self_service_profile
from activation_gateway import exchange_activation_code
from entitlement_signing import verify_entitlement
from core.runtime import scan_engine as _scan_engine
from core.config import DEV_AUTHORITY_ENABLED as _DEV_AUTHORITY_ENABLED
router = APIRouter()

@router.get("/api/users")
def users(db: Session = Depends(get_db)):
    # Production is a single-customer installation. Historical/local rows are
    # never exposed as selectable identities after activation. Development keeps
    # the explicit multi-customer list solely for isolation testing.
    if not _DEV_AUTHORITY_ENABLED:
        bound = _bound_workspace_user(db)
        return [_customer_record(bound)] if bound else []
    return [_customer_record(u) for u in db.query(User).order_by(User.name).all()]


@router.post("/api/users")
def create_user(req: UserRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(409, "Email already exists")
    user = User(name=req.name.strip(), email=req.email.strip(), verification_status="pending")
    db.add(user)
    db.commit()
    db.refresh(user)
    return _customer_record(user)


@router.put("/api/users/{user_id}/company-profile")
def update_company_profile(user_id: int, req: CompanyProfileRequest, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Customer not found")

    company_name = (req.company_name or "").strip()
    intended_use = (req.intended_use or "").strip()
    if len(company_name) < 2 or len(company_name) > 200:
        raise HTTPException(400, "Enter a valid company name")
    if len(intended_use) < 10 or len(intended_use) > 500:
        raise HTTPException(400, "Briefly describe the authorized business use")

    # Reuse the strict public-domain parser, but do not claim ownership here.
    # Exact target authorization remains the separate DNS-TXT gate.
    company_domain = _normalize_domain(req.company_domain)

    user.company_name = company_name
    user.company_domain = company_domain
    user.intended_use = intended_use
    user.company_profile_submitted_at = datetime.utcnow()

    # Customer-supplied profile data is informational only. It never grants or
    # changes approval. Existing rejected/suspended decisions also stay intact.
    db.commit()
    db.refresh(user)
    return _customer_record(user)


@router.get("/api/users/{user_id}/product-status")
def customer_product_status(user_id: int, db: Session = Depends(get_db)):
    user = _require_workspace_customer(db, user_id)
    return _product_ux_status(db, user)


@router.get("/api/product-readiness")
def product_readiness(target: str | None = None, user_id: int | None = None, db: Session = Depends(get_db)):
    """Target-aware local UX status without inventing customer approval.

    Ownership is a property of the already-verified local target and is therefore
    reported independently from customer/product setup.  Scan authorization is
    still re-evaluated authoritatively by /api/scan.
    """
    _migrate_legacy_verified_targets(db)
    if user_id is not None:
        user = _require_workspace_customer(db, user_id)
    else:
        user = None if _DEV_AUTHORITY_ENABLED else _bound_workspace_user(db)
    status = _product_ux_status(db, user) if user else {
        "verification": "missing", "access": "BLOCKED", "product": None,
        "product_key": None, "valid_until": None, "authorized_targets": 0,
        "active_engagements": 0, "ready_for_quick_check": False,
        "next_action": "Set up your SkullHarbor customer profile to continue.",
    }

    hostname = None
    ownership_verified = False
    target_user_id = None
    if target:
        # Readiness is a passive UX endpoint. Partially typed/invalid input must
        # never become a server error and must never grant authorization.
        try:
            hostname = _normalize_domain(target)
        except HTTPException:
            hostname = None
        if hostname:
            row = db.query(Target).filter(Target.domain == hostname, Target.status == "verified").first()
            if row:
                target_user_id = row.user_id
                # Ownership is customer-scoped. A verified domain owned by a
                # different customer must NEVER make this workspace scan-ready.
                ownership_verified = bool(user is not None and row.user_id == user.id)

    # A target can truthfully remain ownership-verified even before the new
    # customer/entitlement model is configured. Do not tell the user to repeat DNS.
    status = dict(status)
    status["target"] = hostname
    status["ownership_verified"] = ownership_verified
    status["target_user_id"] = target_user_id
    status["customer_configured"] = user is not None
    status["ready_for_quick_check"] = bool(
        user is not None
        and status.get("verification") == "approved"
        and status.get("access") in {"ACTIVE", "TRIAL"}
        and (ownership_verified or status.get("active_engagements", 0) > 0)
    )
    if ownership_verified and user is None:
        status["next_action"] = "Website ownership is verified. Set up your customer profile and product access to scan."
    elif ownership_verified and status.get("verification") != "approved":
        status["next_action"] = "Website ownership is verified. Customer verification is still required."
    elif ownership_verified and status.get("access") not in {"ACTIVE", "TRIAL"}:
        status["next_action"] = "Website ownership is verified. Activate SkullHarbor product access to scan."
    return status


@router.get("/api/users/{user_id}/entitlement")
def customer_entitlement(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Customer not found")
    return _entitlement_record(db, user)


@router.get("/api/users/{user_id}/engagements")
def customer_engagements(user_id: int, db: Session = Depends(get_db)):
    if not db.get(User, user_id):
        raise HTTPException(404, "Customer not found")
    rows = db.query(Engagement).filter(Engagement.user_id == user_id).order_by(Engagement.id.desc()).all()
    return [_engagement_record(row) for row in rows]


