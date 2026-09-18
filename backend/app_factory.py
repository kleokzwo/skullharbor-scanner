from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controllers.system_controller import router as system_router
from controllers.customer_controller import router as customer_router
from controllers.target_controller import router as target_router
from controllers.scan_controller import router as scan_router
from core.config import DEV_AUTHORITY_ENABLED

def create_app() -> FastAPI:
    app = FastAPI(title="SkullHarbor UI-Scanner", version="0.8.0-dev")
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    for router in (system_router, customer_router, target_router, scan_router):
        app.include_router(router)
    if DEV_AUTHORITY_ENABLED:
        from dev_authority import register_dev_authority
        register_dev_authority(app)
    _mount_frontend(app)
    return app

def _mount_frontend(app: FastAPI) -> None:
    from pathlib import Path
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    if not dist.is_dir(): return
    assets = dist / "assets"
    if assets.is_dir(): app.mount("/assets", StaticFiles(directory=str(assets)), name="frontend-assets")
    @app.get("/", include_in_schema=False)
    def desktop_index(): return FileResponse(str(dist / "index.html"))
