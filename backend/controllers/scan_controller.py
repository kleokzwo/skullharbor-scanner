from datetime import UTC, datetime, timedelta
import json
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

def _coverage_payload(scan):
    if not scan.coverage_summary:
        return None
    try:
        value = json.loads(scan.coverage_summary)
        return value if isinstance(value, dict) else None
    except (TypeError, ValueError, json.JSONDecodeError):
        return None


@router.get("/api/scans")
def scans(user_id: int, db: Session = Depends(get_db)):
    _require_workspace_customer(db, user_id)
    rows = db.query(Scan).filter(Scan.user_id == user_id).order_by(Scan.id.desc()).limit(50).all()
    return [{
        "id": s.id,
        "target": s.target,
        "scanner": s.scanner,
        "status": s.status,
        "created_at": s.created_at,
        "user_id": s.user_id,
        "user": s.user.name if s.user else None,
        "target_id": s.target_id,
        "finding_count": len(s.findings),
        "scan_profile": s.scan_profile,
        "coverage": _coverage_payload(s),
    } for s in rows]


@router.get("/api/scans/{scan_id}")
def scan_detail(scan_id: int, user_id: int, db: Session = Depends(get_db)):
    _require_workspace_customer(db, user_id)
    s = db.query(Scan).filter(Scan.id == scan_id, Scan.user_id == user_id).first()
    if not s:
        raise HTTPException(404, "Scan not found")
    return {
        "id": s.id,
        "target": s.target,
        "status": s.status,
        "error": s.error,
        "scan_profile": s.scan_profile,
        "created_at": s.created_at,
        "target_id": s.target_id,
        "coverage": _coverage_payload(s),
        "user": s.user.name if s.user else None,
        "findings": [{
            "id": f.id,
            "scanner": f.scanner,
            "rule_id": f.rule_id,
            "category": f.category,
            "coverage_family": f.coverage_family or "Core web security",
            "severity": f.severity,
            "title": f.title,
            "url": f.url,
            "description": f.description,
            "impact": f.impact,
            "recommendation": f.recommendation,
            "evidence": f.evidence,
            "reference": f.reference,
            # raw_output is retained internally for engineering diagnostics only.
            # Customer APIs expose normalized evidence, never raw adapter output.
        } for f in s.findings],
    }


@router.get("/api/scans/{scan_id}/status")
def scan_status(scan_id: int, user_id: int, db: Session = Depends(get_db)):
    _require_workspace_customer(db, user_id)
    s = db.query(Scan).filter(Scan.id == scan_id, Scan.user_id == user_id).first()
    if not s:
        raise HTTPException(404, "Scan not found")
    snap = _scan_engine.snapshot(scan_id)
    if snap:
        return snap
    return {
        "scan_id": scan_id,
        "status": s.status,
        "stage": s.status,
        "progress": 100 if s.status == "completed" else 0,
        "logs": [],
        "elapsed_seconds": 0,
        "error": s.error,
        "coverage": _coverage_payload(s),
    }


@router.post("/api/scans/{scan_id}/stop")
def stop_scan(scan_id: int, user_id: int, db: Session = Depends(get_db)):
    _require_workspace_customer(db, user_id)
    if not db.query(Scan).filter(Scan.id == scan_id, Scan.user_id == user_id).first():
        raise HTTPException(404, "Active scan not found")
    if not _scan_engine.stop(scan_id):
        raise HTTPException(404, "Active scan not found")
    return {"status": "stopping"}


@router.post("/api/scan")
def scan(req: ScanRequest, db: Session = Depends(get_db)):
    # Fail closed before any target parsing/DNS work. Unapproved customers must
    # not reach the protected scan authorization path at all.
    user = _require_workspace_customer(db, req.user_id)
    entitlement = _require_scan_entitlement(db, user)
    target, hostname, ips = validate_target_url(req.target)

    # Resolve authorization once. This avoids a split check where an engagement
    # could cease to authorize between the gate and local provenance lookup.
    verified_target, engagement = _scan_authorization(db, hostname, req.user_id)

    # Sprint 6: the customer cannot choose a profile. The trusted entitlement
    # decision maps to a server-owned policy before any local scan starts.
    # Trial intentionally uses require_self_service_profile("free").
    policy = require_self_service_profile(entitlement["scan_profile"])

    record = Scan(
        target=target,
        scanner="web-security",
        status="queued",
        scan_profile=policy.key,
        user_id=req.user_id,
        target_id=verified_target.id if verified_target else None,
        engagement_id=engagement.id if engagement else None,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    _scan_engine.enqueue(
        record.id, target, record.scan_profile, hostname, ips
    )

    return {
        "scan_id": record.id,
        "status": "queued",
        "scan_profile": record.scan_profile,
        "target_id": verified_target.id if verified_target else None,
        "authorization": "verified-ownership" if verified_target else "approved-engagement",
        "engagement_reference": engagement.reference if engagement else None,
    }


