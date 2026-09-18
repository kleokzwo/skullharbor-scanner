"""Sprint 8 runtime-context regression: legacy DNS proof stays visible without a customer profile."""
import os, tempfile
from datetime import datetime
fd,path=tempfile.mkstemp(suffix='.db'); os.close(fd)
os.environ['DATABASE_URL']=f'sqlite:///{path}'
import main
from database import Base,engine,SessionLocal
from models import Target
Base.metadata.create_all(bind=engine)
db=SessionLocal()
try:
    db.add(Target(domain='skullharbor.org', verification_token='old-proof', status='verified', verified_at=datetime.utcnow(), user_id=None))
    db.commit()
    # A legacy proof may exist, but without an active matching customer it must not authorize scanning
    row=db.query(Target).filter(Target.domain=='skullharbor.org',Target.status=='verified').first()
    assert row is not None and row.user_id is None
    # endpoint source must explicitly preserve this state instead of claiming re-verification
    src=open('application.py',encoding='utf-8').read()
    assert '@app.get("/api/product-readiness")' in src
    assert 'ownership_verified = bool(user is not None and row.user_id == user.id)' in src
    assert 'Website ownership is verified. Set up your customer profile and product access to scan.' in src
    ui='\n'.join(p.read_text(encoding='utf-8') for p in __import__('pathlib').Path('../frontend/src').rglob('*.jsx'))
    assert '/api/product-readiness?' in ui
    assert 'status.ownership_verified' in ui
    assert 'scopeOk?"Website verified":"Setup required"' in ui
finally:
    db.close(); engine.dispose()
    try: os.unlink(path)
    except OSError: pass
print('product UX runtime context tests: OK')
