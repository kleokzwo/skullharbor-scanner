import ipaddress
import secrets
import socket
from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse

import dns.resolver
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine, get_db
from models import Entitlement, EntitlementInstallation, EntitlementLifecycleAudit, Finding, Scan, Target, User, VerificationReviewAudit
from scan_engine import ScanEngine
from scan_profiles import public_product_catalog, require_self_service_profile

Base.metadata.create_all(bind=engine)


def _migrate_sqlite_mvp():
    """Small compatibility migrations for local v0.1.x SQLite databases."""
    if not str(engine.url).startswith("sqlite"):
        return
    inspector = inspect(engine)
    with engine.begin() as conn:
        scan_cols = {c["name"] for c in inspector.get_columns("scans")}
        finding_cols = {c["name"] for c in inspector.get_columns("findings")}
        user_cols = {c["name"] for c in inspector.get_columns("users")}
        if "scan_profile" not in scan_cols:
            conn.execute(text("ALTER TABLE scans ADD COLUMN scan_profile VARCHAR(30) NOT NULL DEFAULT 'free'"))
        if "target_id" not in scan_cols:
            conn.execute(text("ALTER TABLE scans ADD COLUMN target_id INTEGER"))
        if "impact" not in finding_cols:
            conn.execute(text("ALTER TABLE findings ADD COLUMN impact TEXT"))
        if "recommendation" not in finding_cols:
            conn.execute(text("ALTER TABLE findings ADD COLUMN recommendation TEXT"))
        if "rule_id" not in finding_cols:
            conn.execute(text("ALTER TABLE findings ADD COLUMN rule_id VARCHAR(120)"))
        if "category" not in finding_cols:
            conn.execute(text("ALTER TABLE findings ADD COLUMN category VARCHAR(120)"))
        if "raw_output" not in finding_cols:
            conn.execute(text("ALTER TABLE findings ADD COLUMN raw_output TEXT"))
        if "verification_status" not in user_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN verification_status VARCHAR(30) NOT NULL DEFAULT 'pending'"))
        if "verification_updated_at" not in user_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN verification_updated_at DATETIME"))
        if "company_name" not in user_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN company_name VARCHAR(200)"))
        if "company_domain" not in user_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN company_domain VARCHAR(253)"))
        if "intended_use" not in user_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN intended_use VARCHAR(500)"))
        if "company_profile_submitted_at" not in user_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN company_profile_submitted_at DATETIME"))
        entitlement_cols = {c["name"] for c in inspector.get_columns("entitlements")} if inspector.has_table("entitlements") else set()
        if entitlement_cols and "license_id" not in entitlement_cols:
            conn.execute(text("ALTER TABLE entitlements ADD COLUMN license_id VARCHAR(120)"))
        if entitlement_cols and "seat_limit" not in entitlement_cols:
            conn.execute(text("ALTER TABLE entitlements ADD COLUMN seat_limit INTEGER NOT NULL DEFAULT 1"))
        if entitlement_cols and "issued_at" not in entitlement_cols:
            conn.execute(text("ALTER TABLE entitlements ADD COLUMN issued_at DATETIME"))

        # v0.3.0 public naming migration: existing customer-visible rows should
        # no longer expose the concrete backend adapter.
        conn.execute(text("UPDATE scans SET scanner = 'web-security' WHERE scanner = 'nikto'"))
        conn.execute(text("UPDATE findings SET scanner = 'web-security' WHERE lower(scanner) = 'nikto'"))

        # v0.3.2: sanitize legacy customer-facing placeholder rows created by
        # older development builds. Concrete adapter names stay internal.
        conn.execute(text("""
            UPDATE findings
            SET title = 'SkullHarbor web security observation'
            WHERE lower(trim(title)) = 'nikto finding'
        """))
        conn.execute(text("""
            UPDATE findings
            SET description = 'SkullHarbor Web Check returned a technical observation for this target.'
            WHERE lower(trim(description)) = 'nikto finding'
        """))
        conn.execute(text("""
            UPDATE findings
            SET impact = 'This observation may contain useful technical information and should be reviewed in context.'
            WHERE impact IS NOT NULL AND lower(impact) LIKE '%nikto%'
        """))
        conn.execute(text("""
            UPDATE findings
            SET recommendation = 'Review the affected URL and SkullHarbor technical evidence. Confirm the result before making a production change.'
            WHERE recommendation IS NOT NULL AND lower(recommendation) LIKE '%nikto%'
        """))
        conn.execute(text("""
            UPDATE findings
            SET evidence = 'Legacy SkullHarbor web security observation'
            WHERE evidence IS NOT NULL AND lower(evidence) LIKE '%nikto%'
        """))
        conn.execute(text("""
            UPDATE findings
            SET raw_output = 'Legacy SkullHarbor web security observation'
            WHERE raw_output IS NOT NULL AND lower(raw_output) LIKE '%nikto%'
        """))


_migrate_sqlite_mvp()

# A process restart means in-memory worker threads are gone. Never leave old rows
# looking RUNNING forever after uvicorn --reload or a backend restart.
with SessionLocal() as _startup_db:
    stale = _startup_db.query(Scan).filter(Scan.status.in_(["queued", "running"])).all()
    for row in stale:
        row.status = "failed"
        row.error = "Scan interrupted because the backend restarted"
    if stale:
        _startup_db.commit()

app = FastAPI(title="SkullHarbor UI-Scanner", version="0.6.0-dev")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_scan_engine = None  # initialized after target validation helpers are defined

class CustomerRequestModel(BaseModel):
    # Fail closed on unknown customer-supplied fields. This prevents protected
    # review/tier/scanner controls from being silently accepted as no-ops.
    model_config = ConfigDict(extra="forbid")


class ScanRequest(CustomerRequestModel):
    target: str
    user_id: int | None = None


class UserRequest(CustomerRequestModel):
    name: str
    email: str


class CompanyProfileRequest(CustomerRequestModel):
    company_name: str
    company_domain: str
    intended_use: str


class TrustedReviewContext(BaseModel):
    actor_id: str
    actor_role: str
    source: str = "trusted-admin"


class TargetRequest(CustomerRequestModel):
    domain: str
    user_id: int | None = None


def _normalize_domain(value: str) -> str:
    value = (value or "").strip().lower().rstrip(".")
    if "://" in value:
        parsed = urlparse(value)
        value = (parsed.hostname or "").lower().rstrip(".")
    if not value or len(value) > 253 or "." not in value:
        raise HTTPException(400, "Enter a valid public domain name")
    try:
        value = value.encode("idna").decode("ascii")
    except UnicodeError:
        raise HTTPException(400, "Invalid domain name")
    labels = value.split(".")
    if any(not label or len(label) > 63 for label in labels):
        raise HTTPException(400, "Invalid domain name")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-")
    if any(label[0] == "-" or label[-1] == "-" or any(ch not in allowed for ch in label) for label in labels):
        raise HTTPException(400, "Invalid domain name")
    return value


def _resolve_public_ips(hostname: str) -> list[str]:
    try:
        infos = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        raise HTTPException(400, "Target hostname could not be resolved")

    ips = sorted({info[4][0] for info in infos})
    if not ips:
        raise HTTPException(400, "Target hostname did not resolve to an IP address")

    for raw in ips:
        ip = ipaddress.ip_address(raw)
        if not ip.is_global:
            raise HTTPException(400, "Target resolves to a non-public IP address and cannot be scanned")
    return ips


def validate_target_url(target: str) -> tuple[str, str, list[str]]:
    parsed = urlparse((target or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(400, "Target must be a valid http:// or https:// URL")
    if parsed.username or parsed.password:
        raise HTTPException(400, "Credentials in target URLs are not allowed")
    hostname = _normalize_domain(parsed.hostname)
    ips = _resolve_public_ips(hostname)
    return target.strip(), hostname, ips


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


def _authorized_target_for_scan(db: Session, hostname: str, user_id: int | None) -> Target:
    query = db.query(Target).filter(Target.domain == hostname, Target.status == "verified")
    if user_id is not None:
        query = query.filter(Target.user_id == user_id)
    else:
        query = query.filter(Target.user_id.is_(None))
    target = query.first()
    if not target:
        raise HTTPException(403, "Target is not verified. Add and verify this exact hostname before scanning.")
    return target



_scan_engine = ScanEngine(validate_target_url)


@app.get("/api/health")
def health():
    return {"status": "ok", "engine": "web-security", "authorization_gates": ["customer-approval", "dns-txt"]}


@app.get("/api/products")
def products():
    return public_product_catalog()


@app.get("/api/users")
def users(db: Session = Depends(get_db)):
    return [_customer_record(u) for u in db.query(User).order_by(User.name).all()]


@app.post("/api/users")
def create_user(req: UserRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(409, "Email already exists")
    user = User(name=req.name.strip(), email=req.email.strip(), verification_status="pending")
    db.add(user)
    db.commit()
    db.refresh(user)
    return _customer_record(user)


@app.put("/api/users/{user_id}/company-profile")
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


@app.get("/api/users/{user_id}/entitlement")
def customer_entitlement(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Customer not found")
    return _entitlement_record(db, user)


@app.get("/api/targets")
def targets(user_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Target)
    if user_id is not None:
        query = query.filter(Target.user_id == user_id)
    return [_verification_record(t) for t in query.order_by(Target.id.desc()).all()]


@app.post("/api/targets")
def create_target(req: TargetRequest, db: Session = Depends(get_db)):
    domain = _normalize_domain(req.domain)
    _resolve_public_ips(domain)
    if req.user_id is not None and not db.get(User, req.user_id):
        raise HTTPException(400, "Unknown user_id")
    existing = db.query(Target).filter(Target.domain == domain).first()
    if existing:
        if req.user_id is not None and existing.user_id not in {None, req.user_id}:
            raise HTTPException(409, "Target already belongs to another customer")
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


@app.post("/api/targets/{target_id}/verify")
def verify_target(target_id: int, db: Session = Depends(get_db)):
    target = db.get(Target, target_id)

    if not target:
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


@app.get("/api/scans")
def scans(db: Session = Depends(get_db)):
    rows = db.query(Scan).order_by(Scan.id.desc()).limit(50).all()
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
    } for s in rows]


@app.get("/api/scans/{scan_id}")
def scan_detail(scan_id: int, db: Session = Depends(get_db)):
    s = db.get(Scan, scan_id)
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
        "user": s.user.name if s.user else None,
        "findings": [{
            "id": f.id,
            "scanner": f.scanner,
            "rule_id": f.rule_id,
            "category": f.category,
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


@app.get("/api/scans/{scan_id}/status")
def scan_status(scan_id: int, db: Session = Depends(get_db)):
    snap = _scan_engine.snapshot(scan_id)
    if snap:
        return snap
    s = db.get(Scan, scan_id)
    if not s:
        raise HTTPException(404, "Scan not found")
    return {
        "scan_id": scan_id,
        "status": s.status,
        "stage": s.status,
        "progress": 100 if s.status == "completed" else 0,
        "logs": [],
        "elapsed_seconds": 0,
        "error": s.error,
    }


@app.post("/api/scans/{scan_id}/stop")
def stop_scan(scan_id: int):
    if not _scan_engine.stop(scan_id):
        raise HTTPException(404, "Active scan not found")
    return {"status": "stopping"}


@app.post("/api/scan")
def scan(req: ScanRequest, db: Session = Depends(get_db)):
    # Fail closed before any target parsing/DNS work. Unapproved customers must
    # not reach the protected scan authorization path at all.
    user = _require_approved_customer(db, req.user_id)
    entitlement = _require_scan_entitlement(db, user)
    target, hostname, ips = validate_target_url(req.target)

    verified_target = _authorized_target_for_scan(db, hostname, req.user_id)

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
        target_id=verified_target.id,
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
        "target_id": verified_target.id,
    }
