from scanner import normalize_nuclei_line

sample = {
    "template-id": "missing-security-header",
    "matched-at": "https://example.test/",
    "matcher-name": "header-check",
    "info": {
        "name": "Missing security header",
        "severity": "low",
        "description": "A recommended response header was not observed.",
        "tags": ["misconfig"],
        "classification": {"cwe-id": ["CWE-693"]},
        "reference": ["https://owasp.org/"]
    }
}

finding = normalize_nuclei_line(sample, "https://example.test")
assert finding is not None
assert finding["scanner"] == "web-security"
assert finding["severity"] == "low"
assert finding["category"] == "Configuration"
assert finding["rule_id"] == "web.check.missing-security-header"
assert "CWE-693" in finding["reference"]
assert "nuclei" not in str(finding).lower()
print("secondary adapter normalization tests: OK")
