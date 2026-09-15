import threading
from scan_engine import ScanEngine


def fake_validate(target):
    return target, "example.test", ["203.0.113.10"]


engine = ScanEngine(fake_validate)
# Unit-test the lifecycle container without starting an external scanner.
engine._jobs[7] = {
    "status": "queued", "stage": "queued", "progress": 5, "logs": [],
    "started_at": 0, "stop_event": threading.Event(), "error": None,
}
snap = engine.snapshot(7)
assert snap["status"] == "queued"
assert snap["stage"] == "queued"
assert engine.stop(7) is True
snap = engine.snapshot(7)
assert snap["stage"] == "stopping"
assert engine._jobs[7]["stop_event"].is_set()
assert engine.stop(999) is False
print("scan engine lifecycle tests: OK")
