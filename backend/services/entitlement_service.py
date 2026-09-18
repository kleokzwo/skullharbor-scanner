from datetime import UTC, datetime, timedelta
import base64, os, uuid, secrets
from pathlib import Path as _Path
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models import Engagement, EngagementAudit, EngagementScope, Entitlement, EntitlementInstallation, EntitlementLifecycleAudit, Finding, Scan, Target, User, VerificationReviewAudit
from schemas.api import TrustedReviewContext
from scan_profiles import require_self_service_profile
ENTITLEMENT_AUTHORITY_STATES = {"active", "trial", "expired", "no_seat", "blocked"}
ENTITLEMENT_PRODUCT_KEYS = {"free", "monthly", "annual"}
TRIAL_MAX_DAYS = 7
ENTITLEMENT_TRUSTED_ROLES = {"entitlement-admin", "admin"}
ENTITLEMENT_INSTALLATION_STATES = {"active", "released"}
def _signed_entitlement_payload(db: Session, user_id: int, installation_id: str) -> dict:
    """Build the minimal authority-signed grant for one already-bound installation."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Customer not found")
    resolved = _entitlement_record(db, user)
    if resolved["status"] not in {"ACTIVE", "TRIAL"}:
        raise HTTPException(403, "Active SkullHarbor entitlement is required")
    ent = db.query(Entitlement).filter(Entitlement.user_id == user_id).first()
    binding = db.query(EntitlementInstallation).filter(
        EntitlementInstallation.user_id == user_id,
        EntitlementInstallation.installation_id == installation_id,
        EntitlementInstallation.status == "active",
    ).first()
    if not ent or not binding:
        raise HTTPException(403, "Active installation binding is required")
    # Signed local grants are deliberately short-lived. This bounds replay after an
    # authority-side release/block while keeping scan data entirely local.
    grant_issued = datetime.now(UTC)
    authority_expiry = ent.valid_until.replace(tzinfo=UTC) if ent.valid_until else None
    grant_expiry = grant_issued + timedelta(hours=24)
    if authority_expiry is not None:
        grant_expiry = min(grant_expiry, authority_expiry)
    def wire(dt):
        return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")
    return {
        "schema": "skullharbor-entitlement-v1",
        "license_id": ent.license_id,
        "product_key": ent.product_key,
        "status": resolved["status"],
        "installation_id": installation_id,
        "seat_limit": ent.seat_limit,
        "issued_at": wire(grant_issued),
        "valid_until": wire(grant_expiry),
    }


def _validate_entitlement_context(context: TrustedReviewContext) -> tuple[str, str]:
    actor_id = (context.actor_id or "").strip()
    actor_role = (context.actor_role or "").strip().lower()
    if not actor_id or len(actor_id) > 120 or actor_role not in ENTITLEMENT_TRUSTED_ROLES:
        raise HTTPException(403, "Trusted entitlement authority is required")
    if context.source != "entitlement-authority":
        raise HTTPException(403, "Untrusted entitlement source")
    return actor_id, actor_role


def _entitlement_audit(db: Session, user_id: int, context: TrustedReviewContext, action: str, license_id=None, installation_id=None, detail=None):
    actor_id, actor_role = _validate_entitlement_context(context)
    row = EntitlementLifecycleAudit(user_id=user_id, actor_id=actor_id, actor_role=actor_role, action=action,
        license_id=license_id, installation_id=installation_id, detail=detail)
    db.add(row)
    return row


def _issue_entitlement(db: Session, user_id: int, product_key: str, context: TrustedReviewContext, *,
                       license_id: str, seat_limit: int = 1, valid_until=None, trial: bool = False) -> dict:
    """Trusted issuance boundary. It never accepts or stores scan/target/finding data."""
    _validate_entitlement_context(context)
    user = db.get(User, user_id)
    if not user or user.verification_status != "approved":
        raise HTTPException(403, "Approved customer is required for entitlement issuance")
    product_key = (product_key or "").strip().lower()
    license_id = (license_id or "").strip()
    if product_key not in ENTITLEMENT_PRODUCT_KEYS or not license_id or len(license_id) > 120:
        raise HTTPException(400, "Invalid entitlement issuance data")
    if not isinstance(seat_limit, int) or isinstance(seat_limit, bool) or seat_limit < 1 or seat_limit > 100:
        raise HTTPException(400, "Seat limit must be between 1 and 100")
    now = datetime.now(UTC).replace(tzinfo=None)
    if trial:
        if product_key != "free" or not valid_until or valid_until <= now or valid_until > now + timedelta(days=TRIAL_MAX_DAYS):
            raise HTTPException(400, "Trial must be FREE and expire within 7 days")
        status = "trial"
    else:
        status = "active"
    existing_license = db.query(Entitlement).filter(Entitlement.license_id == license_id, Entitlement.user_id != user.id).first()
    if existing_license:
        raise HTTPException(409, "License identifier is already assigned")
    row = db.query(Entitlement).filter(Entitlement.user_id == user.id).first()
    if not row:
        row = Entitlement(user_id=user.id, product_key=product_key, authority_status=status)
        db.add(row)
    active_installations = db.query(EntitlementInstallation).filter(EntitlementInstallation.user_id == user.id, EntitlementInstallation.status == "active").count()
    if active_installations > seat_limit:
        raise HTTPException(409, "Seat limit cannot be lower than active installations")
    row.product_key, row.authority_status, row.valid_until = product_key, status, valid_until
    row.license_id, row.seat_limit, row.issued_at = license_id, seat_limit, now
    row.source, row.updated_at = "entitlement-authority", now
    _entitlement_audit(db, user.id, context, "issued", license_id=license_id, detail=product_key)
    db.commit(); db.refresh(row)
    return _entitlement_record(db, user)


def _bind_installation(db: Session, user_id: int, installation_id: str, context: TrustedReviewContext) -> dict:
    _validate_entitlement_context(context)
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Customer not found")
    entitlement = db.query(Entitlement).filter(Entitlement.user_id == user.id).first()
    resolved = _entitlement_record(db, user)
    if resolved["status"] not in {"ACTIVE", "TRIAL"} or not entitlement:
        raise HTTPException(403, "Active SkullHarbor entitlement is required")
    installation_id = (installation_id or "").strip()
    if not installation_id or len(installation_id) > 120:
        raise HTTPException(400, "Invalid installation identifier")
    existing = db.query(EntitlementInstallation).filter(EntitlementInstallation.installation_id == installation_id).first()
    if existing:
        if existing.user_id != user.id:
            raise HTTPException(409, "Installation is already assigned")
        if existing.status == "active":
            return {"status": "ACTIVE", "installation_id": installation_id}
        active_count = db.query(EntitlementInstallation).filter(EntitlementInstallation.user_id == user.id, EntitlementInstallation.status == "active").count()
        if active_count >= entitlement.seat_limit:
            raise HTTPException(409, "No SkullHarbor seat is available")
        existing.status, existing.released_at, existing.bound_at = "active", None, datetime.utcnow()
    else:
        active_count = db.query(EntitlementInstallation).filter(EntitlementInstallation.user_id == user.id, EntitlementInstallation.status == "active").count()
        if active_count >= entitlement.seat_limit:
            raise HTTPException(409, "No SkullHarbor seat is available")
        existing = EntitlementInstallation(user_id=user.id, installation_id=installation_id, status="active")
        db.add(existing)
    _entitlement_audit(db, user.id, context, "installation-bound", license_id=entitlement.license_id, installation_id=installation_id)
    db.commit()
    return {"status": "ACTIVE", "installation_id": installation_id}


def _release_installation(db: Session, user_id: int, installation_id: str, context: TrustedReviewContext) -> dict:
    _validate_entitlement_context(context)
    row = db.query(EntitlementInstallation).filter(EntitlementInstallation.user_id == user_id, EntitlementInstallation.installation_id == installation_id).first()
    if not row or row.status != "active":
        raise HTTPException(409, "Active installation binding not found")
    ent = db.query(Entitlement).filter(Entitlement.user_id == user_id).first()
    _entitlement_audit(db, user_id, context, "installation-released", license_id=ent.license_id if ent else None, installation_id=installation_id)
    row.status, row.released_at = "released", datetime.utcnow()
    db.commit()
    return {"status": "RELEASED", "installation_id": installation_id}


def _set_entitlement_state(db: Session, user_id: int, state: str, context: TrustedReviewContext, detail: str | None = None) -> dict:
    _validate_entitlement_context(context)
    if state not in {"blocked", "expired"}:
        raise HTTPException(400, "Invalid lifecycle state")
    user = db.get(User, user_id); ent = db.query(Entitlement).filter(Entitlement.user_id == user_id).first() if user else None
    if not user or not ent:
        raise HTTPException(404, "Entitlement not found")
    _entitlement_audit(db, user_id, context, state, license_id=ent.license_id, detail=(detail or "")[:200] or None)
    ent.authority_status, ent.updated_at = state, datetime.now(UTC).replace(tzinfo=None)
    db.commit(); db.refresh(ent)
    return _entitlement_record(db, user)


def _entitlement_record(db: Session, user: User) -> dict:
    """Resolve the local cached authority decision without scan/target inputs."""
    entitlement = db.query(Entitlement).filter(Entitlement.user_id == user.id).first()
    if user.verification_status != "approved":
        return {"status": "BLOCKED", "product_key": None, "scan_profile": None}
    if not entitlement:
        return {"status": "BLOCKED", "product_key": None, "scan_profile": None}

    authority_status = (entitlement.authority_status or "blocked").strip().lower()
    product_key = (entitlement.product_key or "").strip().lower()
    if authority_status not in ENTITLEMENT_AUTHORITY_STATES or product_key not in ENTITLEMENT_PRODUCT_KEYS:
        return {"status": "BLOCKED", "product_key": None, "scan_profile": None}
    if entitlement.source != "entitlement-authority" or not entitlement.seat_limit or entitlement.seat_limit < 1:
        return {"status": "BLOCKED", "product_key": None, "scan_profile": None}

    # Entitlement timestamps are UTC-naive throughout the local cache.  Never
    # compare them with local wall-clock time: a host timezone offset could
    # otherwise keep an already-expired grant active (or expire it early).
    now_utc = datetime.now(UTC).replace(tzinfo=None)
    if authority_status in {"active", "trial"} and entitlement.valid_until and entitlement.valid_until <= now_utc:
        return {"status": "EXPIRED", "product_key": product_key, "scan_profile": None}

    # A SkullHarbor trial is intentionally short and bounded.  It must carry
    # an expiry and the authority may not issue more than seven days from the
    # cached issuance/update timestamp. Malformed/overlong trials fail closed.
    if authority_status == "trial":
        if not entitlement.valid_until or not entitlement.updated_at:
            return {"status": "BLOCKED", "product_key": product_key, "scan_profile": None}
        if entitlement.valid_until > entitlement.updated_at + timedelta(days=TRIAL_MAX_DAYS):
            return {"status": "BLOCKED", "product_key": product_key, "scan_profile": None}
    if authority_status == "expired":
        return {"status": "EXPIRED", "product_key": product_key, "scan_profile": None}
    if authority_status == "no_seat":
        return {"status": "NO_SEAT", "product_key": product_key, "scan_profile": None}
    if authority_status == "blocked":
        return {"status": "BLOCKED", "product_key": product_key, "scan_profile": None}

    # Trials are deliberately bounded to the FREE policy. A subscription can
    # map to its authority-selected product, while ANNUAL remains managed-only.
    scan_profile = "free" if authority_status == "trial" else product_key
    return {
        "status": "TRIAL" if authority_status == "trial" else "ACTIVE",
        "product_key": product_key,
        "scan_profile": scan_profile,
        "valid_until": entitlement.valid_until,
        "seat_limit": entitlement.seat_limit,
        "active_installations": db.query(EntitlementInstallation).filter(EntitlementInstallation.user_id == user.id, EntitlementInstallation.status == "active").count(),
    }


def _require_scan_entitlement(db: Session, user: User) -> dict:
    resolved = _entitlement_record(db, user)
    if resolved["status"] not in {"ACTIVE", "TRIAL"}:
        raise HTTPException(403, f"SkullHarbor entitlement is {resolved['status']}")
    try:
        require_self_service_profile(resolved["scan_profile"])
    except ValueError as exc:
        raise HTTPException(403, str(exc)) from exc
    return resolved


def _product_ux_status(db: Session, user: User) -> dict:
    """Customer-safe local readiness summary for Sprint 8 UX.

    This composes existing policy state only. It is not an authorization gate and
    never weakens the authoritative checks in /api/scan.
    """
    entitlement = _entitlement_record(db, user)
    from services.verification_service import _migrate_legacy_verified_targets
    _migrate_legacy_verified_targets(db)
    now = datetime.now(UTC).replace(tzinfo=None)
    verified_targets = db.query(Target).filter(Target.user_id == user.id, Target.status == "verified").count()
    active_engagements = db.query(Engagement).filter(
        Engagement.user_id == user.id,
        Engagement.status == "approved",
        Engagement.valid_from <= now,
        Engagement.valid_until > now,
    ).count()

    verification_ok = user.verification_status == "approved"
    entitlement_ok = entitlement.get("status") in {"ACTIVE", "TRIAL"} and entitlement.get("scan_profile") in {"free", "monthly"}
    scope_ok = verified_targets > 0 or active_engagements > 0

    if not verification_ok:
        next_action = "Complete customer verification before using Quick Check."
    elif not entitlement_ok:
        next_action = "A valid SkullHarbor product access is required."
    elif not scope_ok:
        next_action = "Verify a target or use an approved engagement scope."
    else:
        next_action = "Quick Check is ready for an authorized target."

    product_key = entitlement.get("product_key")
    product_name = {"free": "SkullHarbor Free", "monthly": "SkullHarbor Advanced", "annual": "SkullHarbor Managed Pentest"}.get(product_key)
    return {
        "verification": user.verification_status,
        "access": entitlement.get("status", "BLOCKED"),
        "product": product_name,
        "product_key": product_key,
        "valid_until": entitlement.get("valid_until"),
        "authorized_targets": verified_targets,
        "active_engagements": active_engagements,
        "ready_for_quick_check": bool(verification_ok and entitlement_ok and scope_ok),
        "next_action": next_action,
    }



