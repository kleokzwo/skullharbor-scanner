from pathlib import Path

src = (Path(__file__).parents[1] / "frontend" / "src" / "main.jsx").read_text()

# Customer identity is chosen independently of target/scan rows. Never recover
# or switch an account from another customer's target ownership data.
assert 'verifiedOwner=targetRows.find' not in src
assert 'const approved=userRows.find(row=>row.verification_status==="approved")' in src
assert 'if(effectiveId) setUserId(effectiveId)' in src

# Customer-facing plan comparison explains value without exposing scanner names.
for phrase in (
    "Choose the coverage you need",
    "Common file and configuration checks",
    "Information disclosure checks",
    "Injection and XSS checks",
    "SQL injection checks",
    "Software identification",
    "Public-service exposure checks",
    "Managed pentest engagement",
):
    assert phrase in src

settings = src[src.index('if(page==="settings")'):src.index('if(page==="scans")')]
for internal_name in ("Nikto", "Nuclei", "Nmap"):
    assert internal_name not in settings

print("product UX step 4 settings tests: OK")
