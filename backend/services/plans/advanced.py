"""Advanced self-service product policy.

The paid tier deliberately combines three bounded internal check families.  No
customer can supply raw tool flags, templates, ports, rate limits, or tuning.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class AdvancedPolicy:
    adapter_slots: tuple[str, ...] = ("primary", "secondary", "surface")
    # Paid scans are fail-closed: every promised coverage family must complete.
    require_all_adapters: bool = True
    primary_tuning: str = "12349b"
    # Secondary uses a version-controlled local allow-list of safe HTTP templates.
    # Broad upstream tag selection is intentionally disabled: it expanded to thousands
    # of templates/requests and violated the QuickCheck runtime contract.
    secondary_include_tags: str = ""
    # Quick Check uses an explicit bounded template allow-list. Automatic scan mode
    # can expand into a large technology/CVE workflow and is intentionally disabled.
    secondary_automatic_scan: bool = False
    secondary_request_timeout: str = "4"
    secondary_retries: str = "0"
    secondary_max_host_errors: str = "10"
    secondary_excluded_tags: str = "dos,fuzz,bruteforce,intrusive,headless"
    secondary_rate_limit: str = "15"
    secondary_concurrency: str = "5"
    # Bounded external-service exposure surface. Standard website ports 80/443 are
    # intentionally excluded because Core already covers the website itself.
    # No UDP, OS detection, version scan or NSE scripts.
    surface_ports: tuple[int, ...] = (
        21, 22, 23, 25, 53, 110, 111, 135, 139, 143, 389, 445, 465, 587, 636,
        993, 995, 1433, 1521, 2049, 2375, 2376, 3000, 3306, 3389, 5432, 5672,
        5900, 6379, 8000, 8080, 8443, 8888, 9200, 9300, 11211, 27017,
    )

POLICY = AdvancedPolicy()
