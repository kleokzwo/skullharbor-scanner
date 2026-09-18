"""Regression guard: keep product UI and plan policy out of monoliths."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
main=(root/'frontend/src/main.jsx').read_text()
assert len(main.splitlines()) < 250, 'frontend main.jsx became a page monolith again'
for page in ('DashboardPage.jsx','ScansPage.jsx','TargetsPage.jsx','SettingsPage.jsx','FindingPage.jsx','SetupPage.jsx'):
    text=(root/'frontend/src/pages'/page).read_text()
    assert 'return <' in text, f'{page} must own its rendered page markup'
assert (root/'backend/services/plans/free.py').exists()
assert (root/'backend/services/plans/advanced.py').exists()
assert (root/'backend/services/target_security.py').exists()
backend=(root/'backend/main.py').read_text()
assert 'def _normalize_domain' not in backend
assert 'def validate_target_url' not in backend
print('Sprint 8 SOLID structure tests: OK')
# Entrypoints are composition roots only. Business/page logic must not creep back.
backend_main=(root/'backend/main.py').read_text()
frontend_main=(root/'frontend/src/main.jsx').read_text()
assert len(backend_main.splitlines()) <= 25, 'backend main.py must stay composition-only'
assert len(frontend_main.splitlines()) <= 12, 'frontend main.jsx must stay bootstrap-only'
for forbidden in ('def scan(', 'def create_target(', 'def _issue_entitlement(', '@app.post(', '@app.get('):
    assert forbidden not in backend_main, f'business/API logic leaked into backend main.py: {forbidden}'
for forbidden in ('useState(', 'useEffect(', 'fetch(', 'function App('):
    assert forbidden not in frontend_main, f'application logic leaked into frontend main.jsx: {forbidden}'
