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

@router.get("/api/targets")
def targets(user_id: int | None = None, db: Session = Depends(get_db)):
    _migrate_legacy_verified_targets(db)
    user = _require_workspace_customer(db, user_id)
    query = db.query(Target).filter(Target.user_id == user.id)
    return [_verification_record(t) for t in query.order_by(Target.id.desc()).all()]


@router.post("/api/targets")
def create_target(req: TargetRequest, db: Session = Depends(get_db)):
    domain = _normalize_domain(req.domain)
    _resolve_public_ips(domain)
    # Target enrollment is customer-scoped and plan-gated. A FREE trial may
    # authorize exactly one website; additional self-service websites require
    # Advanced. This gate is backend-authoritative, not a UI convention.
    user = _require_workspace_customer(db, req.user_id)
    entitlement = _require_scan_entitlement(db, user)
    if entitlement.get("scan_profile") == "free":
        existing_count = db.query(Target).filter(Target.user_id == user.id).count()
        if existing_count >= 1:
            raise HTTPException(403, "Free Trial supports one authorized website. Upgrade to Advanced to add another website.")
    existing = db.query(Target).filter(Target.domain == domain).first()
    if existing:
        if req.user_id is not None and existing.user_id not in {None, req.user_id}:
            raise HTTPException(409, "This domain is already registered to another SkullHarbor customer. If you believe this domain belongs to your organization, please contact support at hello@skullharbor.org.")
        return _verification_record(existing)
    target = Target(
        domain=domain,
        verification_token=secrets.token_urlsafe(24),
        status="pending",
        user_id=req.user_id,
    )
    db.add(target)
    db.commit()
    db.refresh(target)
    return _verification_record(target)


@router.post("/api/targets/{target_id}/verify")
def verify_target(target_id: int, user_id: int, db: Session = Depends(get_db)):
    _require_workspace_customer(db, user_id)
    target = db.query(Target).filter(Target.id == target_id, Target.user_id == user_id).first()

    if not target:
        # Do not disclose whether the id belongs to another customer.
        raise HTTPException(404, "Target not found")

    # Domain must still resolve only to public IP addresses.
    _resolve_public_ips(target.domain)

    expected = f"sh-verification={target.verification_token}"

    verification_names = [
        f"_skullharbor-verification.{target.domain}",
        target.domain,
    ]

    observed = {}
    verified = False

    for name in verification_names:
        values = _txt_values(name)
        observed[name] = values

        if expected in values:
            verified = True
            break

    if not verified:
        raise HTTPException(
            409,
            {
                "message": "Verification TXT record was not found yet",
                "verification_names": verification_names,
                "verification_value": expected,
                "observed_txt": observed,
            },
        )

    target.status = "verified"
    target.verified_at = datetime.utcnow()

    db.commit()
    db.refresh(target)

    return _verification_record(target)


