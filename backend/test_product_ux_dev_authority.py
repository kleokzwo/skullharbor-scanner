"""Sprint 8 Step 2 closeout: development authority is isolated and uses trusted boundaries."""
import os, tempfile
from pathlib import Path
fd, db_path=tempfile.mkstemp(prefix='ui-scanner-dev-authority-',suffix='.db'); os.close(fd)
os.environ['DATABASE_URL']=f'sqlite:///{db_path}'
try:
    import main
    from models import User
    from dev_authority import register_dev_authority
    with main.SessionLocal() as db:
        u=User(name='Dev Owner',email='dev@example.invalid',verification_status='pending',company_name='SkullHarbor',company_domain='skullharbor.org',intended_use='Authorized local product development security testing.',company_profile_submitted_at=main.datetime.utcnow())
        db.add(u);db.commit();db.refresh(u)
        # Exercise the exact trusted primitives used by the isolated bridge.
        main._apply_trusted_review(db,u.id,'approved',main.TrustedReviewContext(actor_id='local-development-reviewer',actor_role='admin',source='trusted-admin'),'Local development validation only')
        now=main.datetime.now(main.UTC).replace(tzinfo=None)
        ent=main._issue_entitlement(db,u.id,'free',main.TrustedReviewContext(actor_id='local-development-authority',actor_role='admin',source='entitlement-authority'),license_id='dev-test',seat_limit=1,valid_until=now+main.timedelta(days=7),trial=True)
        assert ent['status']=='TRIAL' and ent['scan_profile']=='free'
        assert main._product_ux_status(db,db.get(User,u.id))['verification']=='approved'
    source=Path(main.__file__).read_text().lower()
    assert '@app.post("/api/users/{user_id}/approve")' not in source
    assert '@app.post("/api/users/{user_id}/entitlement' not in source
    dev=Path(__file__).with_name('dev_authority.py').read_text().lower()
    assert '/internal/development-authority/' in dev
    print('product UX development authority tests: OK')
finally:
    try: os.unlink(db_path)
    except FileNotFoundError: pass
