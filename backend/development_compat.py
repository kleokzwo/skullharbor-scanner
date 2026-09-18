"""Development/test compatibility facade. Omitted from production packaging."""
from datetime import UTC, datetime, timedelta
from fastapi import HTTPException
from database import SessionLocal
from schemas.api import *
from services.customer_service import *
from services.workspace_service import *
from services.engagement_service import *
from services.entitlement_service import *
from services.verification_service import *
from services.target_security import validate_target_url, resolve_public_ips as _resolve_public_ips
from controllers.customer_controller import users, update_company_profile, product_readiness
from controllers.target_controller import create_target, verify_target
from controllers.scan_controller import scans, scan_detail, scan_status, scan
from core.config import DEV_AUTHORITY_ENABLED as _DEV_AUTHORITY_ENABLED
__all__ = [name for name in globals() if not name.startswith('__')]
# Re-export private historical test hooks without placing their implementation in main.py.
for _module_name in ('services.customer_service','services.workspace_service','services.engagement_service','services.entitlement_service','services.verification_service'):
    _module = __import__(_module_name, fromlist=['*'])
    for _name, _value in vars(_module).items():
        if _name.startswith('_') and not _name.startswith('__'):
            globals()[_name] = _value
__all__ = [name for name in globals() if not name.startswith('__')]
