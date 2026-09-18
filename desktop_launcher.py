"""SkullHarbor local desktop launcher.

Production packaging can expose this as the single clickable application entrypoint.
It starts the local API/UI only on loopback and opens the local workspace. It does
not send targets, scans or findings to a remote service.
"""
from __future__ import annotations

import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

import uvicorn

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from main import app  # noqa: E402

HOST = "127.0.0.1"
PORT = 8765


def _open_when_ready() -> None:
    deadline = time.time() + 15
    while time.time() < deadline:
        try:
            with socket.create_connection((HOST, PORT), timeout=0.25):
                webbrowser.open(f"http://{HOST}:{PORT}/")
                return
        except OSError:
            time.sleep(0.15)


def main() -> None:
    threading.Thread(target=_open_when_ready, daemon=True).start()
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning", access_log=False)


if __name__ == "__main__":
    main()
