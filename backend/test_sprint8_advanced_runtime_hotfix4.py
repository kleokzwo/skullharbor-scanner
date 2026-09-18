"""Regression: Advanced secondary runtime stays bounded and findings remain attributable."""
from pathlib import Path
root=Path(__file__).resolve().parent
policy=(root/'services/plans/advanced.py').read_text()
scanner=(root/'scanner.py').read_text()
engine=(root/'scan_engine.py').read_text()
controller=(root/'controllers/scan_controller.py').read_text()
model=(root/'models.py').read_text()
ui=(root.parent/'frontend/src/pages/DashboardPage.jsx').read_text()
assert 'secondary_rate_limit: str = "15"' in policy
assert 'secondary_concurrency: str = "5"' in policy
assert 'secondary_retries: str = "0"' in policy
assert 'SECONDARY_ADAPTER_TIMEOUT_SECONDS = 120' in scanner
assert 'coverage_family = self._coverage_names.get(slot' in engine
assert 'coverage_family = Column' in model
assert '"coverage_family": f.coverage_family' in controller
assert 'groupedFindings' in ui and 'Vulnerability & exposure checks' in ui
print('sprint8 advanced runtime hotfix4 tests: OK')
