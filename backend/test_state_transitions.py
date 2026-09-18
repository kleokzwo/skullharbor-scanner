"""Sprint 4 closeout: deterministic database lifecycle policy tests."""
import os
import tempfile
import threading

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import scan_engine as scan_engine_module
from database import Base
from models import Finding, Scan
from scan_engine import EngineContext, ScanEngine


def validate(target):
    return target, "example.test", ["203.0.113.10"]


def finding(title="Example finding"):
    return {
        "scanner": "web-security", "rule_id": "web.test", "category": "Configuration",
        "severity": "low", "title": title, "url": "https://example.test/",
        "description": "d", "impact": "i", "recommendation": "r",
        "evidence": "e", "reference": None, "raw_output": "private raw",
    }


with tempfile.TemporaryDirectory() as tmp:
    db_path = os.path.join(tmp, "state-tests.db")
    engine_db = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine_db)
    Base.metadata.create_all(bind=engine_db)

    original_session = scan_engine_module.SessionLocal
    scan_engine_module.SessionLocal = TestSession
    try:
        def new_scan():
            with TestSession() as db:
                row = Scan(target="https://example.test", scanner="web-security", status="queued", scan_profile="free")
                db.add(row); db.commit(); db.refresh(row)
                return row.id

        def prepare(scan_id, adapters, stopped=False):
            eng = ScanEngine(validate)
            eng._adapters = tuple(adapters)
            stop_event = threading.Event()
            if stopped:
                stop_event.set()
            eng._jobs[scan_id] = {
                "status": "queued", "stage": "queued", "progress": 5, "logs": [],
                "started_at": 0, "stop_event": stop_event, "error": None, "adapter_runs": [],
            }
            return eng

        # Fail-closed regression: when a policy promises every configured check,
        # partial adapter success must never be published as a completed report.
        sid = new_scan()
        def fail(ctx, stop): raise RuntimeError("private adapter failure")
        def succeed(ctx, stop): return [finding()]
        eng = prepare(sid, [fail, succeed])
        eng._execute(EngineContext(sid, "https://example.test", "free", "example.test"))
        with TestSession() as db:
            row = db.get(Scan, sid)
            assert row.status == "failed"
            assert "promised security coverage" in (row.error or "").lower()
            assert db.query(Finding).filter(Finding.scan_id == sid).count() == 0
        assert eng.snapshot(sid)["status"] == "failed"

        # All adapters fail -> failed, neutral public error, no findings.
        sid = new_scan()
        eng = prepare(sid, [fail, fail])
        eng._execute(EngineContext(sid, "https://example.test", "free", "example.test"))
        with TestSession() as db:
            row = db.get(Scan, sid)
            assert row.status == "failed"
            assert row.error == "Web security checks could not be completed"
            assert db.query(Finding).filter(Finding.scan_id == sid).count() == 0
        assert "private adapter failure" not in (eng.snapshot(sid)["error"] or "")

        # Stop before execution -> stopped and can never become completed.
        sid = new_scan()
        eng = prepare(sid, [succeed], stopped=True)
        eng._execute(EngineContext(sid, "https://example.test", "free", "example.test"))
        with TestSession() as db:
            row = db.get(Scan, sid)
            assert row.status == "stopped" and row.error is None
            assert db.query(Finding).filter(Finding.scan_id == sid).count() == 0
        assert eng.snapshot(sid)["status"] == "stopped"
    finally:
        scan_engine_module.SessionLocal = original_session

print("database state transition tests: OK")
