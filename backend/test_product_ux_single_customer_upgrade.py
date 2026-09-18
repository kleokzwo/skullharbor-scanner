"""Sprint 8 Step 4: plan upgrade mutates entitlement, never customer identity/scope."""
import os, tempfile
from datetime import UTC, datetime, timedelta
fd,path=tempfile.mkstemp(suffix='.db'); os.close(fd)
os.environ['DATABASE_URL']=f'sqlite:///{path}'
import main
from database import Base, engine, SessionLocal
from models import User, Target
Base.metadata.create_all(bind=engine)
db=SessionLocal()
try:
    user=User(name='Owner',email='owner@example.test',verification_status='approved',company_name='Example GmbH',company_domain='example.test',intended_use='Authorized security testing')
    db.add(user); db.commit(); db.refresh(user)
    target=Target(domain='example.test',verification_token='proof-kept',status='verified',verified_at=datetime.now(UTC).replace(tzinfo=None),user_id=user.id)
    db.add(target); db.commit(); db.refresh(target)
    ctx=main.TrustedReviewContext(actor_id='test-authority',actor_role='admin',source='entitlement-authority')
    main._issue_entitlement(db,user.id,'free',ctx,license_id='trial-license',seat_limit=1,valid_until=datetime.now(UTC).replace(tzinfo=None)+timedelta(days=7),trial=True)
    before=(user.id,user.email,user.company_name,user.company_domain,target.id,target.verification_token,target.verified_at)
    main._issue_entitlement(db,user.id,'monthly',ctx,license_id='monthly-license',seat_limit=1,valid_until=datetime.now(UTC).replace(tzinfo=None)+timedelta(days=30),trial=False)
    db.refresh(user); db.refresh(target)
    after=(user.id,user.email,user.company_name,user.company_domain,target.id,target.verification_token,target.verified_at)
    assert before==after, 'upgrade must not recreate identity or ownership proof'
    assert db.query(User).count()==1
    status=main._product_ux_status(db,user)
    assert status['access']=='ACTIVE' and status['product_key']=='monthly'
    assert status['authorized_targets']==1 and status['ready_for_quick_check'] is True
finally:
    db.close(); engine.dispose()
    try: os.unlink(path)
    except OSError: pass
print('product UX single-customer upgrade tests: OK')
