import os
import stat
import tempfile
from pathlib import Path

from core.runtime_paths import scanner_executable

old_root = os.environ.get("SKULLHARBOR_RUNTIME_DIR")
old_dev = os.environ.get("SKULLHARBOR_DEV_SYSTEM_SCANNERS")
try:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["SKULLHARBOR_RUNTIME_DIR"] = tmp
        os.environ.pop("SKULLHARBOR_DEV_SYSTEM_SCANNERS", None)
        try:
            scanner_executable("secondary")
            raise AssertionError("missing packaged runtime must fail closed")
        except RuntimeError as exc:
            assert "runtime is incomplete" in str(exc)

        p = Path(tmp) / "scanners/nuclei/nuclei"
        p.parent.mkdir(parents=True)
        p.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        p.chmod(p.stat().st_mode | stat.S_IXUSR)
        assert scanner_executable("secondary") == str(p.resolve())

        os.environ["SKULLHARBOR_DEV_SYSTEM_SCANNERS"] = "1"
        assert scanner_executable("primary").endswith("nikto")
finally:
    if old_root is None: os.environ.pop("SKULLHARBOR_RUNTIME_DIR", None)
    else: os.environ["SKULLHARBOR_RUNTIME_DIR"] = old_root
    if old_dev is None: os.environ.pop("SKULLHARBOR_DEV_SYSTEM_SCANNERS", None)
    else: os.environ["SKULLHARBOR_DEV_SYSTEM_SCANNERS"] = old_dev

print("sprint 9 packaged runtime path tests: OK")
