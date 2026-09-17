"""Sprint 8 Step 4: Settings must not mislabel identity or expired Advanced access."""
from pathlib import Path
ui=(Path(__file__).resolve().parent.parent/'frontend'/'src'/'main.jsx').read_text()
assert 'organizationApproved=current?.verification_status==="approved"' in ui
assert 'Organization not configured' in ui
assert 'Verification pending' in ui
assert 'advancedActive=isAdvanced && accessState==="ACTIVE"' in ui
assert 'Advanced is not active.' in ui
assert 'inactive access cannot start new scans.' in ui
assert 'current={currentKey==="free"}' in ui
print('product UX step 4 account-state UI tests: OK')
