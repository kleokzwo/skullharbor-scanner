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
ctx = main.TrustedReviewContext(actor_id="authority-1", actor_role="entitlement-admin", source="entitlement-authority")
user = User(name="Signed User", email="signed@example.test", verification_status="approved", company_name="Signed GmbH", company_domain="signed.example", intended_use="Authorized web security checks")
db.add(user); db.commit(); db.refresh(user)
main._issue_entitlement(db, user.id, "monthly", ctx, license_id="LIC-SIGNED-1", seat_limit=1)
main._bind_installation(db, user.id, "install-A", ctx)
payload = main._signed_entitlement_payload(db, user.id, "install-A")
assert set(payload) == {"schema", "license_id", "product_key", "status", "installation_id", "seat_limit", "issued_at", "valid_until"}
assert not ({"target", "scan", "finding", "raw_output", "verification_token"} & set(payload))
private = Ed25519PrivateKey.generate(); public = private.public_key()
envelope = sign_entitlement(payload, private)
verified = verify_entitlement(envelope, public, "install-A")
assert verified["product_key"] == "monthly" and verified["status"] == "ACTIVE"

# Any payload/signature tampering fails closed.
tampered = copy.deepcopy(envelope); tampered["payload"]["product_key"] = "free"
try: verify_entitlement(tampered, public, "install-A"); raise AssertionError("tamper accepted")
except ValueError: pass
try: verify_entitlement(envelope, Ed25519PrivateKey.generate().public_key(), "install-A"); raise AssertionError("wrong key accepted")
except ValueError: pass
try: verify_entitlement(envelope, public, "install-B"); raise AssertionError("wrong installation accepted")
except ValueError: pass

# Released installations cannot receive a new signed payload.
main._release_installation(db, user.id, "install-A", ctx)
try: main._signed_entitlement_payload(db, user.id, "install-A"); raise AssertionError("released install accepted")
except main.HTTPException as exc: assert exc.status_code == 403

# Local verifier independently rejects an expired signed grant.
expired_payload = dict(payload); expired_payload["valid_until"] = (datetime.now(UTC)-timedelta(seconds=1)).isoformat().replace("+00:00", "Z")
expired_env = sign_entitlement(expired_payload, private)
try: verify_entitlement(expired_env, public, "install-A"); raise AssertionError("expired grant accepted")
except ValueError: pass

# Envelope is strict: extra fields cannot smuggle scan data into signed trust material.
extra = copy.deepcopy(payload); extra["target"] = "example.test"
try: sign_entitlement(extra, private); raise AssertionError("extra signed field accepted")
except ValueError: pass

print("signed entitlement step 3 tests: OK")
