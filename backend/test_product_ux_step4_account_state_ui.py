"""Sprint 8 Step 4: Settings must not mislabel identity or expired Advanced access."""
from pathlib import Path
ui="\n".join(p.read_text() for p in (Path(__file__).resolve().parent.parent/'frontend'/'src').rglob('*.jsx'))
compact="".join(ui.split())
assert 'organizationApproved=current?.verification_status==="approved"' in compact
assert 'Organization not configured' in ui
assert 'Verification pending' in ui
assert 'advancedActive=isAdvanced&&accessState==="ACTIVE"' in compact
assert 'Advanced is not active.' in ui
assert 'inactive access cannot start new scans.' in ui
assert 'current={currentKey==="free"}' in compact
print('product UX step 4 account-state UI tests: OK')
