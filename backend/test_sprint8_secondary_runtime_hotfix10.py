from pathlib import Path
from services.plans.advanced import POLICY

scanner = Path("scanner.py").read_text(encoding="utf-8")
assert POLICY.secondary_automatic_scan is False
assert set(POLICY.secondary_include_tags.split(",")) == {"misconfig", "exposure", "xss", "sqli"}
assert "tech" not in POLICY.secondary_include_tags.split(",")
assert '"-type", "http"' in scanner
assert POLICY.secondary_request_timeout == "3"
assert POLICY.secondary_retries == "0"
assert int(POLICY.secondary_rate_limit) <= 20
assert int(POLICY.secondary_concurrency) <= 8
print("sprint8 secondary runtime hotfix10 tests: OK")
