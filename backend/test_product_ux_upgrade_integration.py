"""Sprint 8 Step 2 upgrade integration: existing verified target survives UX upgrade."""
import os, tempfile
from datetime import datetime, timedelta

fd, path = tempfile.mkstemp(suffix='.db'); os.close(fd)
os.environ['DATABASE_URL'] = f'sqlite:///{path}'

import main
from database import Base, engine, SessionLocal
from models import User, Target, Entitlement

Base.metadata.create_all(bind=engine)
db=SessionLocal()
try:
    # Simulate a real upgraded development DB: several historical profiles exist,
    # but only one approved customer has usable product access. Ownership proof
    # predates user scoping and therefore has user_id=NULL.
    stale=User(name='Old profile', email='old@example.test', verification_status='pending')
    owner=User(name='SkullHarbor customer', email='owner@example.test', verification_status='approved',
               company_name='SkullHarbor', company_domain='skullharbor.org')
    db.add_all([stale,owner]); db.commit(); db.refresh(owner)
    db.add(Entitlement(user_id=owner.id, product_key='monthly', authority_status='active',
                       source='entitlement-authority', seat_limit=1,
                       valid_until=datetime.utcnow()+timedelta(days=30)))
    target=Target(domain='skullharbor.org', verification_token='already-proven', status='verified',
                  verified_at=datetime.utcnow(), user_id=None)
    db.add(target); db.commit(); db.refresh(target)

    changed=main._migrate_legacy_verified_targets(db)
    db.refresh(target)
    assert changed == 1
    assert target.user_id == owner.id

    status=main._product_ux_status(db, owner)
    assert status['verification'] == 'approved'
    assert status['access'] == 'ACTIVE'
    assert status['authorized_targets'] == 1
    assert status['ready_for_quick_check'] is True

    # The exact authoritative scan-authorization resolver now returns the same
    # already-verified target for this customer; no second DNS proof is needed.
    resolved, engagement=main._scan_authorization(db, 'skullharbor.org', owner.id)
    assert resolved.id == target.id and engagement is None
finally:
    db.close(); engine.dispose()
    try: os.unlink(path)
    except OSError: pass
print('product UX upgrade integration tests: OK')
