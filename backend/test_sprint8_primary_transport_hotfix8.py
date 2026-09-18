from pathlib import Path
s=Path('scanner.py').read_text()
assert 'canonical_no_keepalive' in s
assert 'explicit_tls' in s
assert '"-nosslkeepalive"' in s
assert '"-vhost", parsed.hostname' in s
assert 'Retrying core web transport compatibility' in s
assert 'Connectivity-only JSON is transport failure' in s
print('sprint8 primary transport hotfix8 tests: OK')
