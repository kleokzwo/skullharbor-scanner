"""Regression for readiness stability and bounded Advanced failure diagnostics."""
from pathlib import Path
import scanner

customer = Path('controllers/customer_controller.py').read_text(encoding='utf-8')
engine = Path('scan_engine.py').read_text(encoding='utf-8')
ui = Path('../frontend/src/controllers/AppController.jsx').read_text(encoding='utf-8')

assert 'urlparse(' not in customer
assert 'except HTTPException:\n            hostname = None' in customer
assert scanner.SECONDARY_ADAPTER_TIMEOUT_SECONDS <= 120
assert 'record.coverage_summary = json.dumps(' in engine
assert 'setTimeout(()=>{' in ui
assert 'looksComplete' in ui
print('advanced runtime hotfix3 tests: OK')
