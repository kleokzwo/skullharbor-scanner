"""Production activation transport boundary.

Only minimal account/entitlement metadata crosses this boundary. Targets, scans,
findings and scanner data are intentionally not part of the request or response.
"""
from __future__ import annotations
import json, os, urllib.request, urllib.error


def exchange_activation_code(code: str, installation_id: str) -> dict:
    base = os.getenv("SKULLHARBOR_AUTHORITY_URL", "").strip().rstrip("/")
    if not base:
        raise RuntimeError("SkullHarbor Authority is not configured")
    if not base.startswith("https://"):
        raise RuntimeError("SkullHarbor Authority must use HTTPS")
    code = (code or "").strip()
    if not 8 <= len(code) <= 512 or not installation_id:
        raise ValueError("Invalid activation request")
    body = json.dumps({"activation_code": code, "installation_id": installation_id}, separators=(",", ":")).encode()
    req = urllib.request.Request(base + "/v1/desktop/activate", data=body, headers={"Content-Type":"application/json","Accept":"application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=12) as res:
            if res.status != 200:
                raise RuntimeError("Activation was rejected")
            data = json.loads(res.read(65536))
    except urllib.error.HTTPError as exc:
        if exc.code in (400, 401, 403, 404, 409, 410):
            raise RuntimeError("Activation code is invalid, expired, or unavailable") from exc
        raise RuntimeError("SkullHarbor Authority is temporarily unavailable") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError("Could not reach SkullHarbor Authority") from exc
    if not isinstance(data, dict) or set(data) != {"customer", "entitlement"}:
        raise RuntimeError("Invalid Authority activation response")
    return data
