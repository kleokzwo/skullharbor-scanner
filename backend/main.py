"""SkullHarbor ASGI composition entrypoint. No business logic belongs here."""
from infrastructure import startup  # noqa: F401
from app_factory import create_app
from core.config import DEV_AUTHORITY_ENABLED
app = create_app()
if DEV_AUTHORITY_ENABLED:  # development/test compatibility only; absent in production package
    from development_compat import *  # noqa: F401,F403
