import ipaddress
import secrets
import socket
from datetime import datetime
from urllib.parse import urlparse

import dns.resolver
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine, get_db
from models import Finding, Scan, Target, User
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

app = FastAPI(title="SkullHarbor UI-Scanner", version="0.4.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_scan_engine = None  # initialized after target validation helpers are defined

class ScanRequest(BaseModel):
    target: str
    user_id: int | None = None


class UserRequest(BaseModel):
    name: str
    email: str


class TargetRequest(BaseModel):
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
    return {"status": "ok", "engine": "web-security", "authorization_gate": "dns-txt"}


@app.get("/api/products")
def products():
    return public_product_catalog()


@app.get("/api/users")
def users(db: Session = Depends(get_db)):
    return [{"id": u.id, "name": u.name, "email": u.email} for u in db.query(User).order_by(User.name).all()]


@app.post("/api/users")
def create_user(req: UserRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(409, "Email already exists")
    user = User(name=req.name.strip(), email=req.email.strip())
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "name": user.name, "email": user.email}


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
    target, hostname, ips = validate_target_url(req.target)
    if req.user_id is not None and not db.get(User, req.user_id):
        raise HTTPException(400, "Unknown user_id")

    verified_target = _authorized_target_for_scan(db, hostname, req.user_id)

    # Sprint 4.1: until Sprint 6 supplies authenticated entitlements, every
    # customer self-service request resolves server-side to FREE. The request
    # model deliberately has no profile/tuning/scanner fields.
    policy = require_self_service_profile("free")

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
