from pathlib import Path

root = Path(__file__).resolve().parent.parent
frontend = (root / "frontend" / "src" / "main.jsx").read_text()
launcher = (root / "desktop_launcher.py").read_text()
backend = (root / "backend" / "main.py").read_text()
roadmap = (root / "docs" / "FEATURE-SPRINT.md").read_text()

assert 'FIRST RUN' in frontend
assert 'Activation required' in frontend
assert 'users.length===0 && !devAuthority' in frontend
assert 'one-time activation code' in frontend
assert '/api/activation' in frontend
assert 'Activate SkullHarbor' in frontend
assert 'activateProduction' in frontend
assert 'uvicorn.run(app, host=HOST, port=PORT' in launcher
assert 'HOST = "127.0.0.1"' in launcher
assert 'frontend" / "dist"' in backend
assert 'Step 5 — Professional Plan UX — DONE' in roadmap
assert 'Step 6 — Download & First-Run Onboarding — CURRENT' in roadmap
print('sprint 8 step 6 first-run onboarding tests: OK')
