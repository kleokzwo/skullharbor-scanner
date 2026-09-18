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

@router.get("/api/health")
def health():
    return {"status": "ok", "engine": "web-security", "authorization_gates": ["customer-approval", "dns-txt"]}


@router.get("/api/products")
def products():
    return public_product_catalog()


@router.post("/api/activation")
def activate_installation(req: ActivationRequest, db: Session = Depends(get_db)):
    """Exchange a one-time Authority code and cache only signed/minimal access state."""
    installation_id = _installation_id()
    try:
        response = exchange_activation_code(req.activation_code, installation_id)
        grant = verify_entitlement(response["entitlement"], _activation_public_key(), installation_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc

    customer = response.get("customer")
    required = {"name", "email", "company_name", "company_domain", "verification_status"}
    if not isinstance(customer, dict) or set(customer) != required or customer.get("verification_status") != "approved":
        raise HTTPException(403, "Authority did not return an approved customer")
    email = str(customer.get("email") or "").strip().lower()
    if not email or len(email) > 255:
        raise HTTPException(400, "Invalid Authority customer")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(name=str(customer["name"])[:120], email=email)
        db.add(user); db.flush()
    user.name = str(customer["name"])[:120]
    user.company_name = str(customer["company_name"])[:200]
    user.company_domain = str(customer["company_domain"])[:253]
    user.verification_status = "approved"
    user.verification_updated_at = datetime.utcnow()

    ent = db.query(Entitlement).filter(Entitlement.user_id == user.id).first()
    if not ent:
        ent = Entitlement(user_id=user.id, product_key=grant["product_key"], authority_status="blocked")
        db.add(ent)
    ent.product_key = grant["product_key"]
    ent.authority_status = grant["status"].lower()
    ent.license_id = grant["license_id"]
    ent.seat_limit = grant["seat_limit"]
    ent.issued_at = datetime.fromisoformat(grant["issued_at"].replace("Z", "+00:00")).replace(tzinfo=None)
    ent.valid_until = datetime.fromisoformat(grant["valid_until"].replace("Z", "+00:00")).replace(tzinfo=None)
    ent.source = "entitlement-authority"
    ent.updated_at = datetime.utcnow()
    binding = db.query(EntitlementInstallation).filter(EntitlementInstallation.installation_id == installation_id).first()
    if binding and binding.user_id != user.id:
        raise HTTPException(409, "This installation is already assigned to another customer")
    if not binding:
        db.add(EntitlementInstallation(user_id=user.id, installation_id=installation_id, status="active"))
    else:
        binding.status, binding.released_at = "active", None
    db.commit(); db.refresh(user)
    return {"customer": _customer_record(user), "product_status": _entitlement_record(db, user)}


