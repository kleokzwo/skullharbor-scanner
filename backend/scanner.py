import json
import os
import re
import subprocess
import tempfile
import time

from scan_profiles import get_scan_profile

# ---------------------------------------------------------------------------
# Internal adapter configuration
# ---------------------------------------------------------------------------
# The browser/API never receives raw scanner flags.
#
# IMPORTANT:
# "nikto" is an implementation detail of this adapter. Customer-facing data
# uses the neutral SkullHarbor engine id "web-security".

PUBLIC_ENGINE_ID = "web-security"

# Secondary adapter policy: keep automated self-service checks bounded.
# High-risk template classes are explicitly excluded and concurrency/rate are low.
NUCLEI_EXCLUDED_TAGS = "dos,fuzz,bruteforce,intrusive"
NUCLEI_RATE_LIMIT = "5"
NUCLEI_CONCURRENCY = "2"

# Hard execution budgets keep a stalled CLI process from blocking a job forever.
# Values are backend policy, not customer-controlled parameters.
PRIMARY_ADAPTER_TIMEOUT_SECONDS = 300
SECONDARY_ADAPTER_TIMEOUT_SECONDS = 300
PROCESS_STOP_GRACE_SECONDS = 5


class AdapterTimeoutError(RuntimeError):
    """Private signal used when an internal adapter exceeds its execution budget."""


def _terminate_process(proc):
    """Best-effort process shutdown: graceful first, then forceful."""
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=PROCESS_STOP_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


def _wait_bounded(proc, stop_event, timeout_seconds):
    """Wait for a child process while honoring cancellation and a hard deadline."""
    deadline = time.monotonic() + max(0.01, float(timeout_seconds))
    while True:
        rc = proc.poll()
        if rc is not None:
            return rc
        if stop_event.is_set():
            _terminate_process(proc)
            raise RuntimeError("Scan stopped by user")
        if time.monotonic() >= deadline:
            _terminate_process(proc)
            raise AdapterTimeoutError("Web security check exceeded its execution budget")
        stop_event.wait(0.1)


MESSAGE_KEYS = (
    "msg",
    "message",
    "description",
    "finding",
    "detail",
    "details",
    "output",
    "info",
)

EVIDENCE_KEYS = (
    "method",
    "url",
    "uri",
    "path",
    "OSVDB",
    "osvdb",
    "id",
)


def _walk_items(data):
    """Return finding-like dictionaries from multiple structured-output shapes.

    Scanner versions do not all emit the same JSON nesting. Some return a
    top-level list, some a `vulnerabilities` list, and others nest findings
    below host/result objects. Recursing here prevents valid messages from
    being replaced by our generic fallback merely because the envelope changed.
    """
    found = []

    def visit(node):
        if isinstance(node, list):
            for child in node:
                visit(child)
            return

        if not isinstance(node, dict):
            return

        has_message = any(node.get(key) not in (None, "", [], {}) for key in MESSAGE_KEYS)
        has_evidence = any(node.get(key) not in (None, "", [], {}) for key in EVIDENCE_KEYS)

        # A message is the strongest signal. Evidence plus a scanner-style id
        # also qualifies, but plain host/metadata dictionaries do not.
        if has_message or (has_evidence and any(k in node for k in ("OSVDB", "osvdb"))):
            found.append(node)
            return

        for value in node.values():
            if isinstance(value, (dict, list)):
                visit(value)

    visit(data)
    return found


def _first_text(item, keys):
    """Pick the first useful textual value without stringifying containers."""
    for key in keys:
        value = item.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            value = value.strip()
            if value:
                return value
        elif isinstance(value, (int, float)):
            return str(value)
    return ""


# ---------------------------------------------------------------------------
# Sprint 3: customer-facing finding knowledge base
# ---------------------------------------------------------------------------
# Rules are intentionally explicit and conservative. Unknown results remain
# informational instead of receiving an invented severity.
FINDING_RULES = [
    {
        "rule_id": "web.header.x-content-type-options.missing",
        "category": "Security Headers",
        "match": lambda s: "x-content-type-options" in s,
        "severity": "low",
        "title": "Missing X-Content-Type-Options header",
        "description": "The website does not send the recommended X-Content-Type-Options browser security header.",
        "impact": "Without this protection, a browser may try to guess a response's content type. In some situations this can weaken browser-side security controls.",
        "recommendation": "Configure the web server to return: X-Content-Type-Options: nosniff",
    },
    {
        "rule_id": "web.header.frame-protection.missing",
        "category": "Security Headers",
        "match": lambda s: "x-frame-options" in s or "anti-clickjacking" in s,
        "severity": "low",
        "title": "Missing clickjacking protection",
        "description": "The website does not provide a complete browser policy that prevents unwanted framing.",
        "impact": "A page that can be embedded by another website may be exposed to clickjacking-style attacks.",
        "recommendation": "Prefer a Content-Security-Policy frame-ancestors directive and, where legacy browser support is needed, also configure X-Frame-Options.",
    },
    {
        "rule_id": "web.header.content-security-policy.missing",
        "category": "Security Headers",
        "match": lambda s: "content-security-policy" in s and ("not" in s or "missing" in s),
        "severity": "low",
        "title": "Content Security Policy not detected",
        "description": "The website does not appear to send a Content-Security-Policy header.",
        "impact": "A well-designed Content Security Policy can reduce the impact of several browser-side injection problems.",
        "recommendation": "Define and test a restrictive Content-Security-Policy that matches the resources your application actually needs.",
    },
    {
        "rule_id": "web.header.hsts.missing",
        "category": "Transport Security",
        "match": lambda s: "strict-transport-security" in s or "hsts" in s,
        "severity": "low",
        "title": "HSTS protection not detected",
        "description": "The HTTPS service does not appear to advertise HTTP Strict Transport Security.",
        "impact": "Without HSTS, a browser may be more willing to attempt an insecure HTTP connection before being redirected to HTTPS.",
        "recommendation": "After confirming HTTPS is correctly deployed for the whole host, consider enabling Strict-Transport-Security with an appropriate max-age.",
    },
    {
        "rule_id": "web.software.version-disclosure",
        "category": "Information Exposure",
        "match": lambda s: ("server" in s and ("banner" in s or "version" in s)) or "server leaks" in s,
        "severity": "info",
        "title": "Server software information exposed",
        "description": "The service exposes software or version information in a response.",
        "impact": "Detailed technology information can make targeted vulnerability research easier for an attacker.",
        "recommendation": "Reduce unnecessary software and version disclosure in HTTP headers and error pages where practical.",
    },
    {
        "rule_id": "web.directory-indexing",
        "category": "Configuration",
        "match": lambda s: "directory indexing" in s or "directory listing" in s,
        "severity": "medium",
        "title": "Directory listing may be enabled",
        "description": "A web directory may expose a browsable list of files.",
        "impact": "Directory listings can reveal files, backups, names, or structure that were not intended to be public.",
        "recommendation": "Disable directory indexing unless it is explicitly required, and review the exposed directory contents.",
    },
]


def _knowledge_result(raw_description: str):
    normalized = (raw_description or "").strip()
    lowered = normalized.lower()

    for rule in FINDING_RULES:
        if rule["match"](lowered):
            return {
                "rule_id": rule["rule_id"],
                "category": rule["category"],
                "severity": rule["severity"],
                "title": rule["title"],
                "description": rule["description"],
                "impact": rule["impact"],
                "recommendation": rule["recommendation"],
            }

    # Unknown source output stays conservative and clearly unclassified.
    return {
        "rule_id": "web.unclassified",
        "category": "General",
        "severity": "info",
        "title": "Web security observation",
        "description": normalized or "The scan returned a technical observation for this target.",
        "impact": "This observation is not yet mapped to a dedicated SkullHarbor rule. It may be informational or require manual review.",
        "recommendation": "Review the technical evidence and confirm whether a configuration change is required.",
    }


def _customer_safe_text(value: str) -> str:
    """Prevent internal adapter/vendor naming from crossing the public boundary."""
    text = (value or "").strip()
    if not text:
        return text

    # Internal tool names are implementation details. Preserve the useful
    # technical content while replacing branding with SkullHarbor wording.
    text = re.sub(r"(?i)\b(?:nikto|nuclei)\b", "SkullHarbor Web Check", text)
    return text


def normalize_nikto(data, target):
    """Internal adapter: convert source output to the common Finding schema."""
    findings = []

    for item in _walk_items(data):
        if not isinstance(item, dict):
            continue

        raw_description = _customer_safe_text(_first_text(item, MESSAGE_KEYS))

        # If a finding-like record contains only structural evidence, preserve
        # that evidence rather than throwing it away behind a generic label.
        method = _first_text(item, ("method",))
        uri = _first_text(item, ("url", "uri", "path"))
        if not raw_description:
            structural = " ".join(part for part in (method, uri) if part).strip()
            raw_description = structural or "Unclassified web security observation"

        mapped = _knowledge_result(raw_description)
        osvdb = item.get("OSVDB") or item.get("osvdb")

        if uri.startswith("http"):
            finding_url = uri
        elif uri:
            finding_url = target.rstrip("/") + "/" + uri.lstrip("/")
        else:
            finding_url = target

        request_evidence = f"{method} {uri}".strip()
        if request_evidence and raw_description and raw_description != request_evidence:
            evidence = f"{request_evidence}\n{raw_description}"
        else:
            evidence = request_evidence or raw_description

        findings.append({
            "scanner": PUBLIC_ENGINE_ID,
            "rule_id": mapped["rule_id"],
            "category": mapped["category"],
            "severity": mapped["severity"],
            "title": mapped["title"],
            "url": finding_url,
            "description": mapped["description"],
            "impact": mapped["impact"],
            "recommendation": mapped["recommendation"],
            "evidence": evidence,
            "reference": f"OSVDB:{osvdb}" if osvdb else None,
            "raw_output": raw_description,
        })

    return findings


def run_nikto_streaming(target, log_cb, stop_event, profile="free", timeout_seconds=PRIMARY_ADAPTER_TIMEOUT_SECONDS):
    """Internal web-scanner adapter. Return normalized customer findings."""
    try:
        policy = get_scan_profile(profile)
    except ValueError as exc:
        raise RuntimeError("Unknown web scan profile") from exc
    tuning = policy.primary_tuning
    if not policy.self_service or not tuning:
        raise RuntimeError("Web scan profile is not available for self-service execution")

    fd, output_path = tempfile.mkstemp(suffix=".json")
    os.close(fd)

    # Implementation detail: Nikto is invoked only inside the backend adapter.
    cmd = [
        "nikto",
        "-h", target,
        "-Tuning", tuning,
        "-Format", "json",
        "-output", output_path,
        "-nointeractive",
    ]

    # Customer-visible live log stays vendor-neutral.
    log_cb(f"Starting {profile.upper()} web security profile against {target}")
    log_cb("Initializing web checks")

    # CLI output is intentionally discarded here. Structured result files are
    # normalized after completion, and DEVNULL prevents an unread pipe from
    # blocking a noisy child process.
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        rc = _wait_bounded(proc, stop_event, timeout_seconds)

        if stop_event.is_set():
            raise RuntimeError("Scan stopped by user")

        if rc != 0 and (not os.path.exists(output_path) or os.path.getsize(output_path) == 0):
            raise RuntimeError(f"Web security engine exited with code {rc}")

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise RuntimeError("Web security engine did not produce structured output")

        with open(output_path, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)

        return normalize_nikto(data, target)
    finally:
        try:
            os.unlink(output_path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Sprint 4 / Step 2: second internal adapter
# ---------------------------------------------------------------------------
def normalize_nuclei_line(item, target):
    """Convert one JSONL result from the secondary adapter to Finding schema."""
    if not isinstance(item, dict):
        return None

    info = item.get("info") if isinstance(item.get("info"), dict) else {}
    name = _customer_safe_text(str(info.get("name") or "").strip())
    severity = str(info.get("severity") or "info").lower().strip()
    if severity not in {"info", "low", "medium", "high", "critical"}:
        severity = "info"

    matched = _customer_safe_text(str(item.get("matched-at") or item.get("url") or target).strip())
    template_id = _customer_safe_text(str(item.get("template-id") or "").strip())
    description = _customer_safe_text(str(info.get("description") or name or "Web security observation").strip())

    classification = info.get("classification") if isinstance(info.get("classification"), dict) else {}
    cve = classification.get("cve-id")
    cwe = classification.get("cwe-id")
    if isinstance(cve, list):
        cve = ", ".join(str(x) for x in cve)
    if isinstance(cwe, list):
        cwe = ", ".join(str(x) for x in cwe)

    refs = info.get("reference")
    if isinstance(refs, list):
        refs = ", ".join(str(x) for x in refs[:5])
    elif refs is not None:
        refs = str(refs)

    reference_parts = [x for x in (f"CVE: {cve}" if cve else "", f"CWE: {cwe}" if cwe else "", refs or "") if x]
    reference = " | ".join(reference_parts) or None

    evidence_parts = []
    if matched:
        evidence_parts.append(f"Matched: {matched}")
    matcher = _customer_safe_text(str(item.get("matcher-name") or "").strip())
    if matcher:
        evidence_parts.append(f"Check: {matcher}")
    extracted = item.get("extracted-results")
    if isinstance(extracted, list) and extracted:
        evidence_parts.append("Observed: " + ", ".join(_customer_safe_text(str(x)) for x in extracted[:10]))

    tags = info.get("tags")
    if isinstance(tags, list):
        tags_text = " ".join(str(x).lower() for x in tags)
    else:
        tags_text = str(tags or "").lower()
    category = "Configuration" if any(x in tags_text for x in ("misconfig", "config")) else "Web Security"

    title = name or "Web security observation"
    impact = "This automated check identified a condition that may affect the security of the target and should be validated in context."
    recommendation = "Review the affected endpoint and technical evidence, confirm the condition, and apply the relevant vendor or configuration remediation."

    return {
        "scanner": PUBLIC_ENGINE_ID,
        "rule_id": f"web.check.{template_id}" if template_id else "web.unclassified",
        "category": category,
        "severity": severity,
        "title": title,
        "url": matched or target,
        "description": description,
        "impact": impact,
        "recommendation": recommendation,
        "evidence": "\n".join(evidence_parts) or description,
        "reference": reference,
        "raw_output": description,
    }


def run_nuclei_streaming(target, log_cb, stop_event, profile="free", timeout_seconds=SECONDARY_ADAPTER_TIMEOUT_SECONDS):
    """Bounded secondary web-security adapter with JSONL-only result ingestion."""
    try:
        policy = get_scan_profile(profile)
    except ValueError as exc:
        raise RuntimeError("Unknown web scan profile") from exc
    if not policy.self_service or "secondary" not in policy.adapter_slots:
        raise RuntimeError("Additional web security checks are not enabled for this profile")

    fd, output_path = tempfile.mkstemp(suffix=".jsonl")
    os.close(fd)

    cmd = [
        "nuclei",
        "-u", target,
        "-jsonl",
        "-silent",
        "-o", output_path,
        "-exclude-tags", NUCLEI_EXCLUDED_TAGS,
        "-rl", NUCLEI_RATE_LIMIT,
        "-c", NUCLEI_CONCURRENCY,
    ]

    log_cb("Starting additional bounded web security checks")
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        rc = _wait_bounded(proc, stop_event, timeout_seconds)
        if stop_event.is_set():
            raise RuntimeError("Scan stopped by user")
        if rc != 0:
            raise RuntimeError(f"Secondary web security engine exited with code {rc}")

        findings = []
        if os.path.exists(output_path):
            with open(output_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        finding = normalize_nuclei_line(json.loads(line), target)
                    except json.JSONDecodeError:
                        continue
                    if finding:
                        findings.append(finding)
        return findings
    finally:
        try:
            os.unlink(output_path)
        except OSError:
            pass
