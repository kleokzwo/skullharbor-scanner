from pathlib import Path

root = Path(__file__).resolve().parents[1]
front = root / "frontend"

finding = (front / "src/pages/FindingPage.jsx").read_text(encoding="utf-8")
app = (front / "src/controllers/AppController.jsx").read_text(encoding="utf-8")
pkg = (front / "package.json").read_text(encoding="utf-8")
lock = (front / "package-lock.json").read_text(encoding="utf-8")

# Finding detail must leave overlay state before normal page navigation.
assert "setFinding(null)" in finding
assert "setPage(nextPage)" in finding
assert "<Sidebar" in finding and "<MobileNav" in finding
assert "Previous result" in finding and "Next result" in finding

# App controller must keep the detail page wired to the same page/finding state.
assert "FindingPage" in app
assert "if(finding) return <FindingPage {...pageProps}/>;" in app
assert "finding," in app and "setFinding," in app

# Reproducible frontend dependency metadata must be present for clean installs/builds.
assert '"build": "vite build"' in pkg
assert '"node_modules/vite"' in lock
assert '"node_modules/react"' in lock
assert '"node_modules/react-dom"' in lock

print("sprint 8 frontend closeout contract tests: OK")
