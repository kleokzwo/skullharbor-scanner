"""Sprint 8 Step 5: professional customer-facing plan UX."""
from pathlib import Path
ui='\n'.join(x.read_text() for x in (Path(__file__).resolve().parent.parent/'frontend'/'src').rglob('*.jsx'))
roadmap=(Path(__file__).resolve().parent.parent/'docs'/'FEATURE-SPRINT.md').read_text()
assert 'function daysRemaining(validUntil)' in ui
assert 'function customerPlanState(status)' in ui
assert 'days left' in ui
assert 'Advanced · Active' in ui
assert 'Manage subscription · coming later' in ui
assert '>Upgrade to Advanced</button>' in ui
assert 'planState.detail' in ui
# Customer-facing status should not render the raw authority state badge.
assert '>{accessState}</span>' not in ui
assert '### Step 4 — Single-Customer Trial & Upgrade Lifecycle — DONE' in roadmap
assert '### Step 5 — Professional Plan UX — DONE' in roadmap
print('product UX step 5 plan UI tests: OK')
