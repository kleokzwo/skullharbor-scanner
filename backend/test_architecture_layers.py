from pathlib import Path
root=Path(__file__).resolve().parent
main=(root/'main.py').read_text()
application=(root/'application.py').read_text()
assert len(main.splitlines()) <= 12
assert len(application.splitlines()) <= 5
for forbidden in ('def scan(', 'def create_target(', '@app.get(', '@app.post(', 'class ScanRequest'):
    assert forbidden not in main and forbidden not in application
for f in ('system_controller.py','customer_controller.py','target_controller.py','scan_controller.py'):
    assert (root/'controllers'/f).exists()
for f in ('customer_service.py','workspace_service.py','engagement_service.py','entitlement_service.py','verification_service.py','target_security.py'):
    assert (root/'services'/f).exists()
front=root.parent/'frontend/src'
assert len((front/'main.jsx').read_text().splitlines()) <= 12
assert len((front/'app/App.jsx').read_text().splitlines()) <= 12
assert (front/'controllers/AppController.jsx').exists()
assert (front/'services/apiClient.js').exists()
print('layered architecture regression tests: OK')
