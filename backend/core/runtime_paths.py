"""SkullHarbor-owned local scanner runtime path resolution.

Sprint 9 foundation: production packaging resolves scanner executables from the
application runtime directory. A development-only PATH fallback is explicit and
must be opted into with SKULLHARBOR_DEV_SYSTEM_SCANNERS=1.
"""
from __future__ import annotations

import os
from pathlib import Path

_RUNTIME_ENV = "SKULLHARBOR_RUNTIME_DIR"
_DEV_FALLBACK_ENV = "SKULLHARBOR_DEV_SYSTEM_SCANNERS"

_SCANNER_RELATIVE_PATHS = {
    "primary": Path("scanners/nikto/nikto"),
    "secondary": Path("scanners/nuclei/nuclei"),
    "surface": Path("scanners/nmap/nmap"),
}
_DEV_COMMANDS = {"primary": "nikto", "secondary": "nuclei", "surface": "nmap"}


def runtime_root() -> Path:
    override = os.environ.get(_RUNTIME_ENV)
    if override:
        return Path(override).expanduser().resolve()
    return (Path(__file__).resolve().parents[2] / "runtime").resolve()


def scanner_executable(slot: str) -> str:
    """Return an owned scanner path, fail-closed unless dev fallback is explicit."""
    try:
        relative = _SCANNER_RELATIVE_PATHS[slot]
    except KeyError as exc:
        raise RuntimeError(f"Unknown scanner runtime slot: {slot}") from exc

    candidate = runtime_root() / relative
    if candidate.is_file() and os.access(candidate, os.X_OK):
        return str(candidate)

    if os.environ.get(_DEV_FALLBACK_ENV) == "1":
        return _DEV_COMMANDS[slot]

    raise RuntimeError(
        "SkullHarbor local scanner runtime is incomplete. "
        f"Missing executable for runtime slot '{slot}'."
    )
