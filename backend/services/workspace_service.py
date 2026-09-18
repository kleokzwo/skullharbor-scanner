from datetime import UTC, datetime, timedelta
import base64, os, uuid, secrets
from pathlib import Path as _Path
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models import Engagement, EngagementAudit, EngagementScope, Entitlement, EntitlementInstallation, EntitlementLifecycleAudit, Finding, Scan, Target, User, VerificationReviewAudit
from schemas.api import TrustedReviewContext
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from core.config import DEV_AUTHORITY_ENABLED
from services.customer_service import _require_approved_customer
def _installation_id() -> str:
    configured = os.getenv("SKULLHARBOR_INSTALLATION_ID", "").strip()
    if configured:
        return configured
    path = _Path(os.getenv("SKULLHARBOR_DATA_DIR", str(_Path.home() / ".skullharbor"))) / "installation-id"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        value = path.read_text().strip()
        if 8 <= len(value) <= 120:
            return value
    value = "sh-" + uuid.uuid4().hex
    path.write_text(value)
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return value


def _bound_workspace_user(db: Session) -> User | None:
    """Return the customer bound to this installation in production.

    Development builds intentionally keep explicit multi-customer switching for
    isolation testing. Production never chooses a customer from arbitrary local
    rows, targets, scans, e-mail addresses, or request-supplied IDs.
    """
    if DEV_AUTHORITY_ENABLED:
        return None
    installation_id = _installation_id()
    binding = db.query(EntitlementInstallation).filter(
        EntitlementInstallation.installation_id == installation_id,
        EntitlementInstallation.status == "active",
    ).first()
    return db.get(User, binding.user_id) if binding else None


def _require_workspace_customer(db: Session, user_id: int | None) -> User:
    """Fail closed when a production request names any customer except the
    customer cryptographically activated/bound to this installation.
    """
    if DEV_AUTHORITY_ENABLED:
        return _require_approved_customer(db, user_id)
    bound = _bound_workspace_user(db)
    if not bound or user_id is None or bound.id != user_id:
        # Do not disclose whether another local customer row exists.
        raise HTTPException(403, "This installation is not activated for that customer")
    if bound.verification_status != "approved":
        raise HTTPException(403, "Customer verification is required")
    return bound


def _activation_public_key() -> Ed25519PublicKey:
    raw = os.getenv("SKULLHARBOR_ENTITLEMENT_PUBLIC_KEY", "").strip()
    if not raw:
        raise HTTPException(503, "Production activation is not configured")
    try:
        padding = "=" * (-len(raw) % 4)
        key = base64.urlsafe_b64decode(raw + padding)
        if len(key) != 32:
            raise ValueError
        return Ed25519PublicKey.from_public_bytes(key)
    except Exception as exc:
        raise HTTPException(503, "Production activation key is invalid") from exc


ENGAGEMENT_TRUSTED_ROLES = {"engagement-reviewer", "admin"}
ENGAGEMENT_TRUSTED_SOURCE = "engagement-authority"
ENGAGEMENT_STATES = {"approved", "revoked", "expired"}


