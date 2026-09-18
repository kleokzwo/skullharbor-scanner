"""Regression: primary HTTPS execution must preserve the canonical authorized URL.

A host/port/-ssl rewrite caused real HTTPS targets to fail despite the older URL
invocation working on the supported Kali scanner build.
"""
from pathlib import Path
scanner = (Path(__file__).resolve().parent / "scanner.py").read_text()
start = scanner.index("def run_nikto_streaming")
end = scanner.index("# ---------------------------------------------------------------------------\n# Sprint 4 / Step 2", start)
body = scanner[start:end]
assert '"-h", target' in body
assert '"-p", str(target_port)' not in body
assert 'cmd.append("-ssl")' not in body
assert '_is_connectivity_diagnostic' in body
assert 'if diagnostics and not findings:' in body
print("sprint8 primary HTTPS invocation hotfix7 tests: OK")
