import threading
from unittest.mock import patch
import scanner

class Headers(dict):
    def items(self): return super().items()
class Response:
    headers=Headers({'Server':'test'})
    def geturl(self): return 'https://example.test/'
    def __enter__(self): return self
    def __exit__(self,*a): pass

with patch('urllib.request.urlopen', return_value=Response()):
    findings=scanner._core_http_baseline('https://example.test', threading.Event())
    ids={x['rule_id'] for x in findings}
    assert 'web.header.x-content-type-options.missing' in ids
    assert 'web.header.content-security-policy.missing' in ids
    assert 'web.header.hsts.missing' in ids
    assert 'web.header.frame-protection.missing' in ids
    assert all('unable to connect' not in (x.get('description') or '').lower() for x in findings)

class GoodResponse(Response):
    headers=Headers({'X-Content-Type-Options':'nosniff','Content-Security-Policy':"default-src 'self'; frame-ancestors 'none'",'Strict-Transport-Security':'max-age=1'})
with patch('urllib.request.urlopen', return_value=GoodResponse()):
    assert scanner._core_http_baseline('https://example.test', threading.Event()) == []
print('sprint8 primary HTTP baseline hotfix9 tests: OK')
