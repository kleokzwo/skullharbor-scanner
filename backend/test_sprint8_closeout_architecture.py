from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT.parent / "frontend" / "src"

# Current layered architecture: main.py is composition/bootstrap only.
main = (ROOT / "main.py").read_text(encoding="utf-8")
app_factory = (ROOT / "app_factory.py").read_text(encoding="utf-8")
scan = (ROOT / "controllers" / "scan_controller.py").read_text(encoding="utf-8")
customer = (ROOT / "controllers" / "customer_controller.py").read_text(encoding="utf-8")
schemas = (ROOT / "schemas" / "api.py").read_text(encoding="utf-8")
advanced = (ROOT / "services" / "plans" / "advanced.py").read_text(encoding="utf-8")
finding = (FRONTEND / "pages" / "FindingPage.jsx").read_text(encoding="utf-8")
controller = (FRONTEND / "controllers" / "AppController.jsx").read_text(encoding="utf-8")

assert "create_app" in main
assert "include_router" in app_factory
assert '@router.post("/api/scan")' in scan
assert '@router.get("/api/scans/{scan_id}")' in scan
assert '@router.get("/api/users/{user_id}/product-status")' in customer
assert '@router.get("/api/product-readiness")' in customer
assert '@router.get("/api/users/{user_id}/engagements")' in customer
assert "class ScanRequest" in schemas
assert "class CompanyProfileRequest" in schemas

# Advanced public-service exposure must stay bounded and must not sell 80/443
# as special service exposure.
assert "surface_ports" in advanced
policy_block = advanced.split("surface_ports", 1)[1].split(")", 1)[0]
assert "80," not in policy_block and "443," not in policy_block

# Finding detail remains an overlay/detail state; leaving it must clear finding.
assert "setFinding(null)" in controller
assert "Previous result" in finding and "Next result" in finding
assert "Sidebar" in finding and "MobileNav" in finding

print("sprint 8 current-architecture closeout tests: OK")
