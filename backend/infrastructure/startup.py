from sqlalchemy import inspect, text
from database import Base, SessionLocal, engine
from models import Scan

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
        if "engagement_id" not in scan_cols:
            conn.execute(text("ALTER TABLE scans ADD COLUMN engagement_id INTEGER"))
        if "coverage_summary" not in scan_cols:
            conn.execute(text("ALTER TABLE scans ADD COLUMN coverage_summary TEXT"))
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
        if "coverage_family" not in finding_cols:
            conn.execute(text("ALTER TABLE findings ADD COLUMN coverage_family VARCHAR(120)"))
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

def initialize_database():
    return None
