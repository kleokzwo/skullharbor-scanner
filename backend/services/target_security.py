"""Target canonicalization and public-network safety policy.

Pure target validation lives here so API routes and scan orchestration share one
fail-closed implementation. This module does not decide customer ownership.
"""
import ipaddress
import socket
from urllib.parse import urlparse
from fastapi import HTTPException


def normalize_domain(value: str) -> str:
    value = (value or "").strip().lower().rstrip(".")
    if "://" in value:
        parsed = urlparse(value)
        value = (parsed.hostname or "").lower().rstrip(".")
    if not value or len(value) > 253 or "." not in value:
        raise HTTPException(400, "Enter a valid public domain name")
    try:
        value = value.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise HTTPException(400, "Invalid domain name") from exc
    labels = value.split(".")
    if any(not label or len(label) > 63 for label in labels):
        raise HTTPException(400, "Invalid domain name")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-")
    if any(label[0] == "-" or label[-1] == "-" or any(ch not in allowed for ch in label) for label in labels):
        raise HTTPException(400, "Invalid domain name")
    return value


def resolve_public_ips(hostname: str) -> list[str]:
    try:
        infos = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise HTTPException(400, "Target hostname could not be resolved") from exc
    ips = sorted({info[4][0] for info in infos})
    if not ips:
        raise HTTPException(400, "Target hostname did not resolve to an IP address")
    for raw in ips:
        if not ipaddress.ip_address(raw).is_global:
            raise HTTPException(400, "Target resolves to a non-public IP address and cannot be scanned")
    return ips


def validate_target_url(target: str) -> tuple[str, str, list[str]]:
    parsed = urlparse((target or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(400, "Target must be a valid http:// or https:// URL")
    if parsed.username or parsed.password:
        raise HTTPException(400, "Credentials in target URLs are not allowed")
    hostname = normalize_domain(parsed.hostname)
    return target.strip(), hostname, resolve_public_ips(hostname)
