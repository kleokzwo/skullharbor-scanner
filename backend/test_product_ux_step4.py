"""Sprint 8 Step 4: development FREE/MONTHLY product switching closeout."""
import os, tempfile
from pathlib import Path
fd, db_path=tempfile.mkstemp(prefix='ui-scanner-s8-step4-',suffix='.db'); os.close(fd)
os.environ['DATABASE_URL']=f'sqlite:///{db_path}'
try:
    import main
    from models import User
    from scan_profiles import require_self_service_profile
    with main.SessionLocal() as db:
        u=User(name='Product Tester',email='tester@example.invalid',verification_status='pending',company_name='SkullHarbor',company_domain='skullharbor.org',intended_use='Authorized local product development security testing.',company_profile_submitted_at=main.datetime.utcnow())
        db.add(u); db.commit(); db.refresh(u)
        main._apply_trusted_review(db,u.id,'approved',main.TrustedReviewContext(actor_id='local-development-reviewer',actor_role='admin',source='trusted-admin'),'Local development validation only')
        now=main.datetime.now(main.UTC).replace(tzinfo=None)
        monthly=main._issue_entitlement(db,u.id,'monthly',main.TrustedReviewContext(actor_id='local-development-authority',actor_role='admin',source='entitlement-authority'),license_id='dev-monthly-test',seat_limit=1,valid_until=now+main.timedelta(days=30),trial=False)
        assert monthly['status']=='ACTIVE'
        assert monthly['product_key']=='monthly' and monthly['scan_profile']=='monthly'
        policy=require_self_service_profile(monthly['scan_profile'])
        assert policy.key=='monthly'
        # A FREE trial remains FREE even after testing MONTHLY.
        free=main._issue_entitlement(db,u.id,'free',main.TrustedReviewContext(actor_id='local-development-authority',actor_role='admin',source='entitlement-authority'),license_id='dev-free-test',seat_limit=1,valid_until=now+main.timedelta(days=7),trial=True)
        assert free['status']=='TRIAL' and free['scan_profile']=='free'
    dev=Path(__file__).with_name('dev_authority.py').read_text()
    ui=(Path(__file__).parents[1]/'frontend/src/main.jsx').read_text()
    assert 'test_products": ["free", "monthly"]' in dev
    assert '/access/{product_key}' in dev
    assert 'Use MONTHLY test access' in ui and 'Use FREE test access' in ui
    assert 'product_key not in {"free", "monthly"}' in dev
    print('product UX step 4 monthly test access tests: OK')
finally:
    try: os.unlink(db_path)
    except FileNotFoundError: pass
