import subprocess
import threading
import time

from scanner import AdapterTimeoutError, _wait_bounded


class FakeProcess:
    def __init__(self):
        self.returncode = None
        self.terminated = False
        self.killed = False

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated = True
        self.returncode = -15

    def kill(self):
        self.killed = True
        self.returncode = -9

    def wait(self, timeout=None):
        if self.returncode is None:
            raise subprocess.TimeoutExpired("fake", timeout)
        return self.returncode


# A hung process must be terminated when its backend-owned budget expires.
p = FakeProcess()
try:
    _wait_bounded(p, threading.Event(), 0.02)
    raise AssertionError("timeout was not raised")
except AdapterTimeoutError:
    pass
assert p.terminated is True

# Cancellation must terminate promptly and be distinguishable from timeout.
p = FakeProcess()
stop = threading.Event()
stop.set()
try:
    _wait_bounded(p, stop, 10)
    raise AssertionError("cancellation was not raised")
except RuntimeError as exc:
    assert str(exc) == "Scan stopped by user"
assert p.terminated is True

# A normally completed child returns its exit status untouched.
p = FakeProcess()
p.returncode = 0
assert _wait_bounded(p, threading.Event(), 1) == 0

print("execution budget and cancellation tests: OK")
