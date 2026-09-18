import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
import time
import xml.etree.ElementTree as ET

from scan_profiles import get_scan_profile
from services.plans import ADVANCED_POLICY

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
NUCLEI_INCLUDE_TAGS = ADVANCED_POLICY.secondary_include_tags
NUCLEI_QUICKCHECK_TEMPLATE_DIR = Path(__file__).resolve().parent / "resources" / "secondary_quickcheck"
NUCLEI_EXCLUDED_TAGS = ADVANCED_POLICY.secondary_excluded_tags
NUCLEI_RATE_LIMIT = ADVANCED_POLICY.secondary_rate_limit
NUCLEI_CONCURRENCY = ADVANCED_POLICY.secondary_concurrency
NUCLEI_AUTOMATIC_SCAN = ADVANCED_POLICY.secondary_automatic_scan
NUCLEI_REQUEST_TIMEOUT = ADVANCED_POLICY.secondary_request_timeout
NUCLEI_RETRIES = ADVANCED_POLICY.secondary_retries
NUCLEI_MAX_HOST_ERRORS = ADVANCED_POLICY.secondary_max_host_errors

# Hard execution budgets keep a stalled CLI process from blocking a job forever.
# Values are backend policy, not customer-controlled parameters.
# The primary web check has its own graceful per-host runtime cap.  The outer
# process budget is only a kill-switch and is deliberately slightly larger so
# the adapter can flush structured results instead of being killed at 5 min.
PRIMARY_MAXTIME_SECONDS = {"free": 90, "monthly": 180}
PRIMARY_ADAPTER_GRACE_SECONDS = 20
PRIMARY_ADAPTER_TIMEOUT_SECONDS = 200
SECONDARY_ADAPTER_TIMEOUT_SECONDS = 120
SURFACE_ADAPTER_TIMEOUT_SECONDS = 90
SURFACE_ALLOWED_PORTS = ADVANCED_POLICY.surface_ports
PROCESS_STOP_GRACE_SECONDS = 5




# Operational/connectivity messages describe scanner execution, not customer
# vulnerabilities. They must never be published as security findings.
_CONNECTIVITY_DIAGNOSTIC_PATTERNS = (
    "unable to connect",
    "cannot connect",
    "connection refused",
    "connection timed out",
    "could not connect",
    "failed to connect",
    "no route to host",
    "name or service not known",
)

def _is_connectivity_diagnostic(finding):
    text = " ".join(str(finding.get(k) or "") for k in ("raw_output", "description", "evidence", "title")).lower()
    return any(pattern in text for pattern in _CONNECTIVITY_DIAGNOSTIC_PATTERNS)

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
    text = re.sub(r"(?i)\b(?:nikto|nuclei|nmap)\b", "SkullHarbor Web Check", text)
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


def _primary_command(target, tuning, output_path, graceful_limit, strategy="canonical"):
    """Build one bounded primary-engine invocation.

    HTTPS handling is intentionally adapter-owned.  Some real-world TLS stacks
    misbehave with connection reuse, while some Nikto/Perl builds behave better
    with explicit host/port/SSL.  We therefore keep a small, deterministic
    compatibility ladder instead of declaring the whole paid check failed after
    one transport variant.
    """
    from urllib.parse import urlparse

    base = [
        "nikto",
        "-Tuning", tuning,
        "-maxtime", f"{graceful_limit}s",
        "-Format", "json",
        "-output", output_path,
        "-nointeractive",
    ]
    parsed = urlparse(target)

    if strategy == "canonical":
        return ["nikto", "-h", target] + base[1:]

    if strategy == "canonical_no_keepalive":
        return ["nikto", "-h", target, "-nosslkeepalive"] + base[1:]

    if strategy == "explicit_tls" and parsed.scheme.lower() == "https" and parsed.hostname:
        port = parsed.port or 443
        return [
            "nikto", "-h", parsed.hostname,
            "-p", str(port), "-ssl", "-nosslkeepalive",
            "-vhost", parsed.hostname,
        ] + base[1:]

    return ["nikto", "-h", target] + base[1:]


def _run_primary_attempt(cmd, output_path, stop_event, hard_limit):
    """Run one primary transport strategy and return structured data + diagnostics."""
    # Remove a previous attempt's report so stale JSON can never make a retry
    # appear successful.
    try:
        os.unlink(output_path)
    except OSError:
        pass

    fd, diag_path = tempfile.mkstemp(suffix=".primary.log")
    os.close(fd)
    try:
        with open(diag_path, "wb") as diag:
            proc = subprocess.Popen(cmd, stdout=diag, stderr=subprocess.STDOUT)
            rc = _wait_bounded(proc, stop_event, hard_limit)

        if stop_event.is_set():
            raise RuntimeError("Scan stopped by user")

        diagnostic_text = ""
        try:
            diagnostic_text = Path(diag_path).read_text(encoding="utf-8", errors="replace")[-12000:]
        except OSError:
            pass

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            return rc, None, diagnostic_text

        try:
            with open(output_path, "r", encoding="utf-8", errors="replace") as f:
                return rc, json.load(f), diagnostic_text
        except (OSError, json.JSONDecodeError):
            return rc, None, diagnostic_text
    finally:
        try:
            os.unlink(diag_path)
        except OSError:
            pass


def _core_http_baseline(target, stop_event, timeout_seconds=12):
    """First-party bounded HTTP(S) baseline used only when the primary CLI
    cannot establish transport. This is real coverage, not a synthetic success:
    completion requires an actual HTTP response from the authorized target.
    """
    import ssl
    import urllib.error
    import urllib.request

    if stop_event.is_set():
        raise RuntimeError("Scan stopped by user")

    req = urllib.request.Request(
        target,
        headers={"User-Agent": "SkullHarbor-QuickCheck/0.8"},
        method="GET",
    )
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=float(timeout_seconds), context=context) as response:
            headers = {str(k).lower(): str(v) for k, v in response.headers.items()}
            final_url = response.geturl() or target
    except urllib.error.HTTPError as exc:
        # An HTTP status such as 401/403/404 still proves transport and gives us
        # response headers that can be assessed safely.
        headers = {str(k).lower(): str(v) for k, v in exc.headers.items()}
        final_url = exc.geturl() or target
    except Exception as exc:
        raise RuntimeError("Core web security could not establish an HTTP response") from exc

    findings = []
    def add(rule_id, category, severity, title, description, impact, recommendation):
        findings.append({
            "rule_id": rule_id,
            "category": category,
            "severity": severity,
            "title": title,
            "url": final_url,
            "description": description,
            "impact": impact,
            "recommendation": recommendation,
            "evidence": "Header not detected in the observed HTTP response.",
            "reference": None,
            "raw_output": "",
        })

    if "x-content-type-options" not in headers:
        add("web.header.x-content-type-options.missing", "Security Headers", "low",
            "Missing X-Content-Type-Options header",
            "The website does not send the recommended X-Content-Type-Options browser security header.",
            "Without this protection, a browser may try to guess a response's content type.",
            "Configure the web server to return X-Content-Type-Options: nosniff.")
    if "content-security-policy" not in headers:
        add("web.header.content-security-policy.missing", "Security Headers", "low",
            "Content Security Policy not detected",
            "The website does not appear to send a Content-Security-Policy header.",
            "A well-designed Content Security Policy can reduce the impact of browser-side injection problems.",
            "Define and test a restrictive Content-Security-Policy for the application.")
    if str(final_url).lower().startswith("https://") and "strict-transport-security" not in headers:
        add("web.header.hsts.missing", "Transport Security", "low",
            "HSTS protection not detected",
            "The HTTPS service does not appear to advertise HTTP Strict Transport Security.",
            "Without HSTS, browsers may be more willing to attempt an insecure HTTP connection first.",
            "After confirming HTTPS is deployed for the whole host, consider enabling Strict-Transport-Security.")
    if "x-frame-options" not in headers and "frame-ancestors" not in headers.get("content-security-policy", "").lower():
        add("web.header.frame-protection.missing", "Security Headers", "low",
            "Missing clickjacking protection",
            "The website does not provide a complete browser policy that prevents unwanted framing.",
            "A page that can be embedded by another website may be exposed to clickjacking-style attacks.",
            "Prefer a Content-Security-Policy frame-ancestors directive and optionally X-Frame-Options for legacy clients.")
    return findings


def run_nikto_streaming(target, log_cb, stop_event, profile="free", timeout_seconds=None):
    """Internal primary web-security adapter with bounded HTTPS compatibility retry."""
    try:
        policy = get_scan_profile(profile)
    except ValueError as exc:
        raise RuntimeError("Unknown web scan profile") from exc
    tuning = policy.primary_tuning
    if not policy.self_service or not tuning:
        raise RuntimeError("Web scan profile is not available for self-service execution")

    graceful_limit = PRIMARY_MAXTIME_SECONDS.get(policy.key, 90)
    # A caller-supplied timeout remains authoritative.  Otherwise each transport
    # attempt gets a bounded slice; connectivity failures usually terminate far
    # earlier than the scanner max-time.
    hard_limit = float(timeout_seconds) if timeout_seconds is not None else graceful_limit + PRIMARY_ADAPTER_GRACE_SECONDS

    fd, output_path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        log_cb(f"Starting {profile.upper()} web security profile against {target}")
        log_cb("Initializing web checks")

        strategies = ["canonical"]
        if str(target).lower().startswith("https://"):
            strategies += ["canonical_no_keepalive", "explicit_tls"]

        last_private_diag = ""
        for attempt_no, strategy in enumerate(strategies, start=1):
            cmd = _primary_command(target, tuning, output_path, graceful_limit, strategy)
            rc, data, private_diag = _run_primary_attempt(cmd, output_path, stop_event, hard_limit)
            last_private_diag = private_diag or last_private_diag

            if data is None:
                # Retry only transport/setup failures.  The private CLI text is
                # deliberately not exposed to customers.
                if attempt_no < len(strategies):
                    log_cb("Retrying core web transport compatibility")
                    continue
                log_cb("Running core HTTP compatibility baseline")
                return _core_http_baseline(target, stop_event)

            normalized = normalize_nikto(data, target)
            diagnostics = [item for item in normalized if _is_connectivity_diagnostic(item)]
            findings = [item for item in normalized if not _is_connectivity_diagnostic(item)]

            # Findings prove that the engine exchanged usable HTTP responses.
            # A genuinely clean structured report (no finding records and no
            # connectivity diagnostic) is also valid coverage.
            if findings or not diagnostics:
                return findings

            # Connectivity-only JSON is transport failure, not a customer
            # finding. Try the next bounded compatibility strategy before
            # failing the paid coverage family.
            if attempt_no < len(strategies):
                log_cb("Retrying core web transport compatibility")
                continue

            # The CLI transport failed, but that must not automatically make a
            # customer check unusable. Run a small first-party HTTP baseline.
            # It only counts as completed if the target actually returns HTTP.
            log_cb("Running core HTTP compatibility baseline")
            return _core_http_baseline(target, stop_event)

        raise RuntimeError("Core web security could not complete")
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

    if not NUCLEI_QUICKCHECK_TEMPLATE_DIR.is_dir():
        raise RuntimeError("Secondary QuickCheck policy is not installed")

    fd, output_path = tempfile.mkstemp(suffix=".jsonl")
    os.close(fd)

    cmd = [
        "nuclei",
        "-u", target,
        "-jsonl",
        "-silent",
        "-o", output_path,
        "-t", str(NUCLEI_QUICKCHECK_TEMPLATE_DIR),
        "-exclude-tags", NUCLEI_EXCLUDED_TAGS,
        "-rl", NUCLEI_RATE_LIMIT,
        "-c", NUCLEI_CONCURRENCY,
        "-timeout", NUCLEI_REQUEST_TIMEOUT,
        "-retries", NUCLEI_RETRIES,
        "-mhe", NUCLEI_MAX_HOST_ERRORS,
        "-duc",
    ]
    if NUCLEI_AUTOMATIC_SCAN:
        cmd.append("-as")

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


# ---------------------------------------------------------------------------
# Sprint 4.1 / Step 2: bounded web-surface discovery adapter
# ---------------------------------------------------------------------------
def normalize_surface_xml(xml_text, target):
    """Convert bounded external-service discovery into customer-facing observations.

    The website's normal HTTP/HTTPS ports (80/443) are deliberately not part of
    this family.  This family exists to reveal *additional* externally reachable
    services such as SSH, FTP, SMB, databases, remote administration and
    alternate/admin web services.  An open port is evidence of attack surface,
    not automatically a vulnerability.
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    service_labels = {
        21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
        110: "POP3", 111: "RPC bind", 135: "MS RPC", 139: "NetBIOS",
        143: "IMAP", 389: "LDAP", 445: "SMB", 465: "SMTPS",
        587: "SMTP submission", 636: "LDAPS", 993: "IMAPS", 995: "POP3S",
        1433: "Microsoft SQL Server", 1521: "Oracle database", 2049: "NFS",
        2375: "Docker API", 2376: "Docker API (TLS)", 3000: "Alternate web/admin service",
        3306: "MySQL", 3389: "Remote Desktop", 5432: "PostgreSQL",
        5672: "AMQP", 5900: "VNC", 6379: "Redis", 8000: "Alternate web service",
        8080: "Alternate HTTP/admin service", 8443: "Alternate HTTPS/admin service",
        8888: "Alternate web/admin service", 9200: "Elasticsearch HTTP",
        9300: "Elasticsearch transport", 11211: "Memcached", 27017: "MongoDB",
    }

    findings = []
    for port in root.findall(".//port"):
        state = port.find("state")
        if state is None or state.get("state") != "open":
            continue
        try:
            port_id = int(port.get("portid", "0"))
        except ValueError:
            continue
        if port_id not in SURFACE_ALLOWED_PORTS:
            continue

        service = port.find("service")
        detected = (service.get("name") if service is not None else None)
        service_name = service_labels.get(port_id) or detected or "TCP service"
        host = _target_hostname(target)
        finding_url = f"tcp://{host}:{port_id}"
        title = f"{service_name} publicly reachable"
        description = (
            f"TCP port {port_id} is reachable from the public network on the verified target. "
            f"The port is commonly associated with {service_name}. This is an external attack-surface "
            "observation and does not by itself prove a vulnerability."
        )
        findings.append({
            "scanner": PUBLIC_ENGINE_ID,
            "rule_id": f"surface.external-service.{port_id}",
            "category": "External Service Exposure",
            "severity": "info",
            "title": title,
            "url": finding_url,
            "description": description,
            "impact": "Additional publicly reachable services increase the externally accessible attack surface and should be intentional.",
            "recommendation": "Confirm that this service must be internet-accessible. Restrict it by firewall/VPN or trusted source networks where possible, and keep the service securely configured and patched.",
            "evidence": f"TCP/{port_id} open; observed_service={detected or 'not fingerprinted'}; expected_service={service_name}.",
            "reference": None,
            "raw_output": f"open tcp/{port_id} service={detected or service_name}",
        })
    return findings


def _target_hostname(target):
    """Extract the already-authorized hostname without adding a new trust decision."""
    from urllib.parse import urlparse
    parsed = urlparse(target if "://" in target else f"https://{target}")
    return parsed.hostname or target


def run_surface_discovery_streaming(target, log_cb, stop_event, profile="free", timeout_seconds=SURFACE_ADAPTER_TIMEOUT_SECONDS):
    """Advanced-only fixed-port external-service discovery; no scripts, UDP, OS or version scan."""
    try:
        policy = get_scan_profile(profile)
    except ValueError as exc:
        raise RuntimeError("Unknown web scan profile") from exc
    if not policy.self_service or "surface" not in policy.adapter_slots:
        raise RuntimeError("Surface discovery is not enabled for this profile")

    hostname = _target_hostname(target)
    fd, output_path = tempfile.mkstemp(suffix=".xml")
    os.close(fd)
    cmd = [
        "nmap",
        "-sT", "-Pn", "-T2",
        "--max-retries", "1",
        "--host-timeout", "60s",
        "-p", ",".join(str(p) for p in SURFACE_ALLOWED_PORTS),
        "-oX", output_path,
        hostname,
    ]
    log_cb("Starting bounded external service exposure discovery")
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        rc = _wait_bounded(proc, stop_event, timeout_seconds)
        if stop_event.is_set():
            raise RuntimeError("Scan stopped by user")
        if rc != 0:
            raise RuntimeError(f"Web surface discovery exited with code {rc}")
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise RuntimeError("Public service exposure check did not produce scan evidence")
        xml_text = Path(output_path).read_text(encoding="utf-8", errors="replace")
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            raise RuntimeError("Public service exposure check produced invalid scan evidence") from exc
        # Exit code 0 alone is insufficient. Require a real host record and
        # finished run metadata so 'completed' means the bounded probe ran.
        if root.find(".//host") is None or root.find(".//runstats/finished") is None:
            raise RuntimeError("Public service exposure check did not complete its bounded probes")
        return normalize_surface_xml(xml_text, target)
    finally:
        try:
            os.unlink(output_path)
        except OSError:
            pass
