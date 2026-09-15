import copy
import os
from datetime import UTC, datetime, timedelta

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
import main
from database import Base, SessionLocal, engine
from entitlement_signing import sign_entitlement, verify_entitlement
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from models import User

Base.metadata.create_all(bind=engine)
db = SessionLocal()
ctx = main.TrustedReviewContext(actor_id="authority-closeout", actor_role="entitlement-admin", source="entitlement-authority")
user = User(name="Closeout User", email="closeout@example.test", verification_status="approved", company_name="Closeout GmbH", company_domain="closeout.example", intended_use="Authorized web security checks")
db.add(user); db.commit(); db.refresh(user)
main._issue_entitlement(db, user.id, "monthly", ctx, license_id="LIC-CLOSEOUT-1", seat_limit=1)
main._bind_installation(db, user.id, "install-closeout", ctx)
payload = main._signed_entitlement_payload(db, user.id, "install-closeout")
private = Ed25519PrivateKey.generate(); public = private.public_key()

issued = datetime.fromisoformat(payload["issued_at"].replace("Z", "+00:00"))
expiry = datetime.fromisoformat(payload["valid_until"].replace("Z", "+00:00"))
assert timedelta(0) < expiry - issued <= timedelta(hours=24)
assert not ({"target", "scan", "finding", "raw_output", "verification_token", "scanner"} & set(payload))
assert verify_entitlement(sign_entitlement(payload, private), public, "install-closeout")["license_id"] == "LIC-CLOSEOUT-1"

# A correctly signed grant is still rejected if its offline lifetime is stretched.
long_lived = copy.deepcopy(payload)
long_lived["valid_until"] = (issued + timedelta(hours=24, seconds=1)).isoformat().replace("+00:00", "Z")
try: verify_entitlement(sign_entitlement(long_lived, private), public, "install-closeout"); raise AssertionError("overlong grant accepted")
except ValueError: pass

# Future-dated grants beyond the small clock-skew allowance fail closed.
future = copy.deepcopy(payload)
future_issued = datetime.now(UTC) + timedelta(minutes=6)
future["issued_at"] = future_issued.isoformat().replace("+00:00", "Z")
future["valid_until"] = (future_issued + timedelta(hours=1)).isoformat().replace("+00:00", "Z")
try: verify_entitlement(sign_entitlement(future, private), public, "install-closeout"); raise AssertionError("future grant accepted")
except ValueError: pass

# Missing/null/malformed timestamp material cannot turn into an unbounded grant.
for field, value in (("issued_at", None), ("valid_until", None), ("issued_at", "not-a-time")):
    bad = copy.deepcopy(payload); bad[field] = value
    try: verify_entitlement(sign_entitlement(bad, private), public, "install-closeout"); raise AssertionError("bad timestamp accepted")
    except ValueError: pass

# Authority-side termination prevents issuance of a fresh grant. Previously issued
# offline grants are intentionally bounded by the 24h local grant lifetime above.
main._set_entitlement_state(db, user.id, "blocked", ctx, "security closeout")
try: main._signed_entitlement_payload(db, user.id, "install-closeout"); raise AssertionError("blocked entitlement issued fresh grant")
except main.HTTPException as exc: assert exc.status_code == 403

print("sprint 6 security closeout tests: OK")
