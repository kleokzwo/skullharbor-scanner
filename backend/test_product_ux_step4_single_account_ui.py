"""Sprint 8 Step 4 UX contract: one organization, plan changes are not profile creation."""
from pathlib import Path
ui=(Path(__file__).parents[1]/'frontend/src/main.jsx').read_text()
assert 'Account & plan' in ui
assert 'Changing plan never creates another profile.' in ui
assert 'Upgrade to Advanced' in ui
assert 'You do not register again.' in ui
assert 'Test Advanced upgrade' in ui
assert 'Managed pentest engagement' in ui
assert 'Development testing controls' in ui
assert 'Choose profile' not in ui
assert 'aria-label="Customer profile"' not in ui
print('product UX step 4 single-account UI tests: OK')
