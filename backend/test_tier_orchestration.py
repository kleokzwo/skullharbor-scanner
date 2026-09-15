"""Sprint 4.1 closeout: complete server-owned tier orchestration policy."""
import os
import tempfile
import threading

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import scan_engine as scan_engine_module
from database import Base
from models import Finding, Scan
from scan_engine import EngineContext, ScanEngine
from scan_profiles import get_scan_profile, require_self_service_profile


def validate(target):
    return target, "example.test", ["203.0.113.10"]


def finding(rule_id, title):
    return {
        "scanner": "web-security",
        "rule_id": rule_id,
        "category": "Configuration",
        "severity": "info",
        "title": title,
        "url": "https://example.test/",
        "description": "d",
        "impact": "i",
        "recommendation": "r",
        "evidence": "e",
        "reference": None,
        "raw_output": "private raw",
    }


# Static policy invariants: customer products map to fixed server-owned depth.
assert get_scan_profile("free").adapter_slots == ("primary",)
assert get_scan_profile("monthly").adapter_slots == ("primary", "secondary", "surface")
assert get_scan_profile("free").primary_tuning == "12"
assert get_scan_profile("monthly").primary_tuning == "1234b"
assert "6" not in get_scan_profile("monthly").primary_tuning
try:
    require_self_service_profile("annual")
except ValueError:
    pass
else:
    raise AssertionError("annual must not resolve to a self-service scan policy")


with tempfile.TemporaryDirectory() as tmp:
    db_path = os.path.join(tmp, "tier-orchestration.db")
    engine_db = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine_db)
    Base.metadata.create_all(bind=engine_db)

    original_session = scan_engine_module.SessionLocal
    scan_engine_module.SessionLocal = TestSession
    try:
        def new_scan(profile):
            with TestSession() as db:
                row = Scan(
                    target="https://example.test",
                    scanner="web-security",
                    status="queued",
                    scan_profile=profile,
                )
                db.add(row)
                db.commit()
                db.refresh(row)
                return row.id

        def run_profile(profile):
            sid = new_scan(profile)
            eng = ScanEngine(validate)
            calls = []

            def slot(name):
                def adapter(ctx, stop_event):
                    calls.append(name)
                    return [finding(f"policy.{name}", f"Policy {name}")]
                return adapter

            # Replace private slot implementations, not the selected adapter list.
            # This verifies that ScanEngine itself selects slots from ScanProfile.
            eng._adapter_slots = {
                "primary": slot("primary"),
                "secondary": slot("secondary"),
                "surface": slot("surface"),
            }
            eng._jobs[sid] = {
                "status": "queued",
                "stage": "queued",
                "progress": 5,
                "logs": [],
                "started_at": 0,
                "stop_event": threading.Event(),
                "error": None,
                "adapter_runs": [],
            }
            eng._execute(EngineContext(sid, "https://example.test", profile, "example.test"))
            return sid, eng, calls

        # FREE must execute only the primary slot.
        sid, eng, calls = run_profile("free")
        assert calls == ["primary"]
        with TestSession() as db:
            assert db.get(Scan, sid).status == "completed"
            assert db.query(Finding).filter(Finding.scan_id == sid).count() == 1

        # MONTHLY must execute all three controlled slots in policy order.
        sid, eng, calls = run_profile("monthly")
        assert calls == ["primary", "secondary", "surface"]
        with TestSession() as db:
            assert db.get(Scan, sid).status == "completed"
            assert db.query(Finding).filter(Finding.scan_id == sid).count() == 3

        # ANNUAL must fail closed before any adapter can execute.
        sid, eng, calls = run_profile("annual")
        assert calls == []
        with TestSession() as db:
            row = db.get(Scan, sid)
            assert row.status == "failed"
            assert db.query(Finding).filter(Finding.scan_id == sid).count() == 0
        assert eng.snapshot(sid)["status"] == "failed"
    finally:
        scan_engine_module.SessionLocal = original_session

print("tier orchestration closeout tests: OK")
