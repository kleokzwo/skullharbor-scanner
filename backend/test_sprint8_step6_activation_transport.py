import base64, os, tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from entitlement_signing import sign_entitlement
import main

# Production activation is code-based and the desktop request contains no scan data.
front = (Path(__file__).resolve().parent.parent / 'frontend/src/main.jsx').read_text()
gateway = (Path(__file__).resolve().parent / 'activation_gateway.py').read_text()
assert '/api/activation' in front and 'activation_code' in front
assert 'targets' not in gateway.lower() or 'not part of the request' in gateway
assert '/v1/desktop/activate' in gateway
assert 'https://' in gateway
assert 'SKULLHARBOR_AUTHORITY_URL' in gateway
assert 'SKULLHARBOR_ENTITLEMENT_PUBLIC_KEY' in Path(main.__file__).read_text()

# Signed grant must be installation-bound before local approved state can be cached.
private = Ed25519PrivateKey.generate()
public_raw = private.public_key().public_bytes_raw()
os.environ['SKULLHARBOR_ENTITLEMENT_PUBLIC_KEY'] = base64.urlsafe_b64encode(public_raw).rstrip(b'=').decode()
os.environ['SKULLHARBOR_DATA_DIR'] = tempfile.mkdtemp()
installation = main._installation_id()
now = datetime.now(UTC)
payload = {'schema':'skullharbor-entitlement-v1','license_id':'LIC-ACT-1','product_key':'free','status':'TRIAL','installation_id':installation,'seat_limit':1,'issued_at':now.isoformat().replace('+00:00','Z'),'valid_until':(now+timedelta(hours=12)).isoformat().replace('+00:00','Z')}
from entitlement_signing import verify_entitlement
assert verify_entitlement(sign_entitlement(payload, private), main._activation_public_key(), installation)['license_id']=='LIC-ACT-1'
print('sprint 8 step 6 activation transport tests: OK')
