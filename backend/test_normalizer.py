from scanner import normalize_nikto

TARGET = "https://example.test"

fixtures = [
    {
        "vulnerabilities": [
            {
                "method": "GET",
                "url": "/",
                "msg": "The anti-clickjacking X-Frame-Options header is not present.",
            }
        ]
    },
    {
        "host": "example.test",
        "results": {
            "items": [
                {
                    "method": "GET",
                    "path": "/",
                    "description": "X-Content-Type-Options header is not set.",
                }
            ]
        },
    },
    [
        {
            "target": "example.test",
            "findings": [
                {
                    "uri": "/files/",
                    "message": "Directory listing appears to be enabled.",
                }
            ],
        }
    ],
]

expected_rules = [
    "web.header.frame-protection.missing",
    "web.header.x-content-type-options.missing",
    "web.directory-indexing",
]

for fixture, expected in zip(fixtures, expected_rules):
    findings = normalize_nikto(fixture, TARGET)
    assert len(findings) == 1, findings
    assert findings[0]["rule_id"] == expected, findings[0]
    assert findings[0]["raw_output"] not in ("", "Web security observation"), findings[0]

print("normalizer regression tests: OK")
