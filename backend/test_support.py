"""Regression-test helpers for the post-Sprint-8 layered architecture."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def backend_source(*relative_paths: str) -> str:
    return "\n".join((ROOT / p).read_text(encoding="utf-8") for p in relative_paths)

def compact(text: str) -> str:
    return "".join(text.split())
