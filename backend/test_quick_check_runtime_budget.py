"""Regression for the real five-minute Quick Check failure seen in Sprint 8."""
import json
import os
import threading

import scanner


class FinishedProcess:
    def __init__(self):
        self.returncode = 0
    def poll(self):
        return self.returncode
    def terminate(self):
        self.returncode = -15
    def kill(self):
        self.returncode = -9
    def wait(self, timeout=None):
        return self.returncode


captured = {}
original_popen = scanner.subprocess.Popen


def fake_popen(cmd, stdout=None, stderr=None):
    captured["cmd"] = list(cmd)
    output_path = cmd[cmd.index("-output") + 1]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"vulnerabilities": [{"msg": "Server version banner", "url": "https://example.test/"}]}, f)
    return FinishedProcess()


scanner.subprocess.Popen = fake_popen
try:
    findings = scanner.run_nikto_streaming(
        "https://example.test",
        lambda _line: None,
        threading.Event(),
        profile="free",
    )
finally:
    scanner.subprocess.Popen = original_popen

cmd = captured["cmd"]
assert "-maxtime" in cmd, "primary web check must have a graceful internal runtime cap"
assert cmd[cmd.index("-maxtime") + 1] == "90s", "FREE Quick Check must remain quick and bounded"
assert findings, "graceful completion must preserve normalized findings"

# Paid self-service may be deeper, but it is still bounded and below the old
# ungraceful five-minute kill point.
assert scanner.PRIMARY_MAXTIME_SECONDS["monthly"] == 180
assert scanner.PRIMARY_MAXTIME_SECONDS["free"] < scanner.PRIMARY_MAXTIME_SECONDS["monthly"] < 300

print("quick check runtime budget regression tests: OK")
