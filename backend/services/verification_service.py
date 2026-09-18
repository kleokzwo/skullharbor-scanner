from datetime import UTC, datetime, timedelta
import base64, os, uuid, secrets
from pathlib import Path as _Path
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models import Engagement, EngagementAudit, EngagementScope, Entitlement, EntitlementInstallation, EntitlementLifecycleAudit, Finding, Scan, Target, User, VerificationReviewAudit
from schemas.api import TrustedReviewContext
import dns.resolver
import dns.exception
from services.target_security import normalize_domain as _normalize_domain
from services.entitlement_service import _entitlement_record
from services.engagement_service import _authorized_engagement_for_scan
def _migrate_legacy_verified_targets(db: Session) -> int:
    """Attach pre-customer-bound verified targets to a deterministic local customer.

    Sprint 2 allowed ownership verification before customer scoping existed.  Those
    rows legitimately have user_id=NULL.  Prefer historical local scan provenance;
    otherwise migrate only when exactly one local customer exists.  Ambiguous data
    remains unassigned (fail closed).
    """
    changed = 0
    legacy = db.query(Target).filter(Target.status == "verified", Target.user_id.is_(None)).all()
    if not legacy:
        return 0
    all_users = db.query(User).all()
    sole_user_id = all_users[0].id if len(all_users) == 1 else None

    # A legacy database can contain several development/customer rows even though
    # only one of them is actually allowed to use Quick Check.  That was the
    # missing case in the earlier Sprint-8 migration.  Treat exactly one approved
    # customer with usable self-service entitlement as deterministic provenance.
    # This does not grant approval or a license; it only attaches an ownership
    # proof that already succeeded before customer scoping existed.
    eligible_user_ids = []
    for candidate in all_users:
        if candidate.verification_status != "approved":
            continue
        resolved = _entitlement_record(db, candidate)
        if resolved.get("status") in {"ACTIVE", "TRIAL"} and resolved.get("scan_profile") in {"free", "monthly"}:
            eligible_user_ids.append(candidate.id)
    sole_eligible_user_id = eligible_user_ids[0] if len(eligible_user_ids) == 1 else None

    for target in legacy:
        scan_user_ids = {row[0] for row in db.query(Scan.user_id).filter(
            Scan.target_id == target.id, Scan.user_id.isnot(None)
        ).distinct().all()}
        # Older scans may predate target_id provenance. Match the canonical host as
        # a secondary local-only migration signal.
        if not scan_user_ids:
            for scan in db.query(Scan).filter(Scan.user_id.isnot(None)).all():
                try:
                    host = _normalize_domain(scan.target)
                except Exception:
                    continue
                if host == target.domain:
                    scan_user_ids.add(scan.user_id)
        # Prefer strongest local provenance: historical scan owner, then exact
        # company-domain match, then a single usable local product identity, and
        # finally the old single-user fallback.  Any ambiguity remains fail-closed.
        company_user_ids = []
        for candidate in all_users:
            if not candidate.company_domain:
                continue
            try:
                if _normalize_domain(candidate.company_domain) == target.domain:
                    company_user_ids.append(candidate.id)
            except HTTPException:
                continue

        if len(scan_user_ids) == 1:
            owner_id = next(iter(scan_user_ids))
        elif scan_user_ids:
            owner_id = None
        elif len(company_user_ids) == 1:
            owner_id = company_user_ids[0]
        elif len(company_user_ids) > 1:
            owner_id = None
        elif sole_eligible_user_id is not None:
            owner_id = sole_eligible_user_id
        else:
            owner_id = sole_user_id

        if owner_id is not None:
            target.user_id = owner_id
            changed += 1
    if changed:
        db.commit()
    return changed


def _verification_record(target: Target) -> dict:
    return {
        "id": target.id,
        "domain": target.domain,
        "status": target.status,
        "verification_name": f"_skullharbor-verification.{target.domain}",
        "verification_value": f"sh-verification={target.verification_token}",
        "verified_at": target.verified_at,
        "created_at": target.created_at,
        "user_id": target.user_id,
    }


def _txt_values(name: str) -> list[str]:
    resolver = dns.resolver.Resolver()
    resolver.timeout = 3.0
    resolver.lifetime = 5.0
    try:
        answers = resolver.resolve(name, "TXT")
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        return []
    except dns.exception.DNSException as exc:
        raise HTTPException(503, f"DNS verification lookup failed: {exc.__class__.__name__}")

    values = []
    for answer in answers:
        if hasattr(answer, "strings"):
            raw = b"".join(answer.strings).decode("utf-8", errors="replace")
        else:
            raw = str(answer).strip('"').replace('" "', "")
        values.append(raw)
    return values


def _scan_authorization(db: Session, hostname: str, user_id: int | None) -> tuple[Target | None, Engagement | None]:
    """Resolve one local authorization decision without a split engagement check.

    Verified ownership has precedence. Otherwise the exact-host engagement row
    returned here is the same row retained as local scan provenance.
    """
    query = db.query(Target).filter(Target.domain == hostname, Target.status == "verified")
    if user_id is not None:
        query = query.filter(Target.user_id == user_id)
    else:
        query = query.filter(Target.user_id.is_(None))
    target = query.first()
    if target:
        return target, None
    engagement = _authorized_engagement_for_scan(db, hostname, user_id) if user_id is not None else None
    if engagement:
        return None, engagement
    raise HTTPException(403, "Target requires verified ownership or an approved exact-host engagement scope.")


def _authorized_target_for_scan(db: Session, hostname: str, user_id: int | None) -> Target | None:
    # Compatibility helper used by existing policy tests/callers. The scan route
    # itself uses _scan_authorization so authorization and provenance are atomic
    # at the policy-decision level.
    target, _engagement = _scan_authorization(db, hostname, user_id)
    return target



