from pathlib import Path
DEV_AUTHORITY_ENABLED = (Path(__file__).resolve().parents[2] / ".skullharbor-development").exists()
