"""Sprint 8 Step 5 security hotfix: customer history isolation + FREE one-site boundary."""
import os, tempfile
from datetime import UTC, datetime, timedelta
from fastapi import HTTPException
fd,path=tempfile.mkstemp(suffix='.db'); os.close(fd)
os.environ['DATABASE_URL']=f'sqlite:///{path}'
import main
import controllers.target_controller as target_controller
import controllers.scan_controller as scan_controller
from database import Base, engine, SessionLocal
from models import User, Target, Scan
Base.metadata.create_all(bind=engine)
db=SessionLocal()
try:
    a=User(name='A',email='a@example.test',verification_status='approved',company_name='A GmbH',company_domain='a.test',intended_use='authorized')
    b=User(name='B',email='b@example.test',verification_status='approved',company_name='B GmbH',company_domain='b.test',intended_use='authorized')
    db.add_all([a,b]); db.commit(); db.refresh(a); db.refresh(b)
    ctx=main.TrustedReviewContext(actor_id='test',actor_role='admin',source='entitlement-authority')
    until=datetime.now(UTC).replace(tzinfo=None)+timedelta(days=7)
    main._issue_entitlement(db,a.id,'free',ctx,license_id='free-a',valid_until=until,trial=True)
    main._issue_entitlement(db,b.id,'monthly',ctx,license_id='adv-b',valid_until=until,trial=False)
    ta=Target(domain='a.test',verification_token='a',status='verified',user_id=a.id)
    tb=Target(domain='b.test',verification_token='b',status='verified',user_id=b.id)
    db.add_all([ta,tb]); db.commit(); db.refresh(ta); db.refresh(tb)
    sa=Scan(target='https://a.test',status='completed',user_id=a.id,target_id=ta.id)
    sb=Scan(target='https://b.test',status='completed',user_id=b.id,target_id=tb.id,scan_profile='monthly')
    db.add_all([sa,sb]); db.commit(); db.refresh(sa); db.refresh(sb)

    rows=main.scans(a.id,db)
    assert [r['id'] for r in rows]==[sa.id], 'scan history leaked across customers'
    try: main.scan_detail(sb.id,a.id,db); raise AssertionError('foreign scan detail leaked')
    except HTTPException as e: assert e.status_code==404
    try: main.scan_status(sb.id,a.id,db); raise AssertionError('foreign scan status leaked')
    except HTTPException as e: assert e.status_code==404

    # FREE already has one authorized website: a second enrollment must fail
    target_controller._resolve_public_ips=lambda domain:['203.0.113.10']
    try: main.create_target(main.TargetRequest(domain='second-a.test',user_id=a.id),db); raise AssertionError('FREE added second website')
    except HTTPException as e: assert e.status_code==403

    # Upgrade mutates entitlement only, then second website enrollment is allowed.
    main._issue_entitlement(db,a.id,'monthly',ctx,license_id='adv-a',valid_until=until,trial=False)
    created=main.create_target(main.TargetRequest(domain='second-a.test',user_id=a.id),db)
    assert created['domain']=='second-a.test' and created['user_id']==a.id

    # A foreign customer's verified domain must not make product readiness scan-ready.
    foreign=main.product_readiness(target='https://b.test',user_id=a.id,db=db)
    assert foreign['target_user_id']==b.id
    assert foreign['ownership_verified'] is False
    assert foreign['ready_for_quick_check'] is False

    # The authoritative scan gate must also reject the foreign domain.
    scan_controller.validate_target_url=lambda value: ('https://b.test','b.test',['203.0.113.11'])
    try: main.scan(main.ScanRequest(target='https://b.test',user_id=a.id),db); raise AssertionError('foreign domain scan was accepted')
    except HTTPException as e: assert e.status_code==403

    # Verification endpoint is customer-scoped and does not expose foreign target ids.
    try: main.verify_target(tb.id,a.id,db); raise AssertionError('foreign target verification was accepted')
    except HTTPException as e: assert e.status_code==404
finally:
    db.close(); engine.dispose()
    try: os.unlink(path)
    except OSError: pass
print('Sprint 8 Step 5 customer isolation security tests: OK')
