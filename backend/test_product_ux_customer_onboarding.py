"""Sprint 8: customer onboarding is actionable but never self-approves."""
from pathlib import Path
src='\n'.join(p.read_text(encoding='utf-8') for p in Path('../frontend/src').rglob('*.jsx'))
api=Path('application.py').read_text(encoding='utf-8')
assert 'Set up customer profile' in src
assert 'Verify your organization' in src
assert 'Submit for verification' in src
assert 'trusted SkullHarbor reviewer' in src
assert 'cannot approve itself' in src
assert 'method:"POST"' in src and '/api/users`' in src
assert '/company-profile`' in src
assert '@app.post("/api/users/{user_id}/approve")' not in api
assert '@app.post("/api/users/{user_id}/entitlement")' not in api
print('product UX customer onboarding tests: OK')
