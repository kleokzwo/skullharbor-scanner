"""Minimal signed SkullHarbor entitlement envelope.

This module deliberately knows nothing about targets, scans, findings or scanner output.
The authority signs a canonical JSON payload with Ed25519; local software needs only
the public verification key.
"""
from __future__ import annotations

import base64
import json
from datetime import UTC, datetime, timedelta
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

SCHEMA = "skullharbor-entitlement-v1"
ALLOWED_KEYS = {
    "schema", "license_id", "product_key", "status", "installation_id",
    "seat_limit", "issued_at", "valid_until",
}
ALLOWED_STATUS = {"ACTIVE", "TRIAL"}
ALLOWED_PRODUCTS = {"free", "monthly"}
LOCAL_GRANT_MAX_HOURS = 24
CLOCK_SKEW_MINUTES = 5


def _b64e(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64d(value: str) -> bytes:
    if not isinstance(value, str) or not value or len(value) > 512:
        raise ValueError("Invalid signature encoding")
    try:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except Exception as exc:
        raise ValueError("Invalid signature encoding") from exc


def canonical_payload(payload: dict[str, Any]) -> bytes:
    if not isinstance(payload, dict) or set(payload) != ALLOWED_KEYS:
        raise ValueError("Invalid entitlement payload shape")
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sign_entitlement(payload: dict[str, Any], private_key: Ed25519PrivateKey) -> dict[str, Any]:
    body = canonical_payload(payload)
    return {"payload": payload, "signature": _b64e(private_key.sign(body))}


def verify_entitlement(envelope: dict[str, Any], public_key: Ed25519PublicKey, installation_id: str, *, now: datetime | None = None) -> dict[str, Any]:
    """Verify signature, schema, installation binding and local expiry. Fail closed."""
    if not isinstance(envelope, dict) or set(envelope) != {"payload", "signature"}:
        raise ValueError("Invalid signed entitlement envelope")
    payload = envelope.get("payload")
    body = canonical_payload(payload)
    try:
        public_key.verify(_b64d(envelope.get("signature")), body)
    except (InvalidSignature, ValueError, TypeError) as exc:
        raise ValueError("Entitlement signature verification failed") from exc

    if payload["schema"] != SCHEMA or payload["status"] not in ALLOWED_STATUS or payload["product_key"] not in ALLOWED_PRODUCTS:
        raise ValueError("Unsupported entitlement grant")
    if not installation_id or payload["installation_id"] != installation_id:
        raise ValueError("Entitlement is not bound to this installation")
    if not isinstance(payload["seat_limit"], int) or isinstance(payload["seat_limit"], bool) or not 1 <= payload["seat_limit"] <= 100:
        raise ValueError("Invalid entitlement seat limit")
    if not payload["license_id"] or len(payload["license_id"]) > 120:
        raise ValueError("Invalid entitlement license identifier")

    current = (now or datetime.now(UTC)).astimezone(UTC)
    try:
        issued = datetime.fromisoformat(payload["issued_at"].replace("Z", "+00:00"))
        expiry = datetime.fromisoformat(payload["valid_until"].replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("Invalid entitlement grant timestamps") from exc
    if issued.tzinfo is None or expiry.tzinfo is None:
        raise ValueError("Entitlement grant timestamps must include UTC timezone")
    issued, expiry = issued.astimezone(UTC), expiry.astimezone(UTC)
    if issued > current + timedelta(minutes=CLOCK_SKEW_MINUTES):
        raise ValueError("Entitlement grant is not valid yet")
    if expiry <= issued or expiry > issued + timedelta(hours=LOCAL_GRANT_MAX_HOURS):
        raise ValueError("Invalid entitlement grant lifetime")
    if expiry <= current:
        raise ValueError("Entitlement has expired")
    return dict(payload)
