import threading
from scan_engine import ScanEngine


def fake_validate(target):
    return target, "example.test", ["203.0.113.10"]


engine = ScanEngine(fake_validate)

# Cross-adapter duplicates collapse while retaining extra evidence/reference.
a = {
    "scanner": "web-security", "rule_id": "web.test", "category": "Configuration",
    "severity": "medium", "title": "Example finding", "url": "https://example.test/path",
    "description": "d", "impact": "i", "recommendation": "r",
    "evidence": "first evidence", "reference": None, "raw_output": "raw",
}
b = dict(a)
b["evidence"] = "second evidence"
b["reference"] = "CVE: CVE-2099-0001"
result = engine._deduplicate_findings([a, b])
assert len(result) == 1
assert "first evidence" in result[0]["evidence"]
assert "second evidence" in result[0]["evidence"]
assert result[0]["reference"] == "CVE: CVE-2099-0001"

# Internal adapter telemetry exists but is deliberately absent from public snapshot.
engine._jobs[9] = {
    "status": "running", "stage": "web-security", "progress": 50, "logs": [],
    "started_at": 0, "stop_event": threading.Event(), "error": None, "adapter_runs": [],
}
engine._record_adapter_run(9, 1, "completed", 0, 2)
assert len(engine._jobs[9]["adapter_runs"]) == 1
assert "adapter_runs" not in engine.snapshot(9)
print("orchestration hardening tests: OK")
