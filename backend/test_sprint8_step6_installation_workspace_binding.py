"""Sprint 8 / Step 6: production workspace is installation-bound, never guessed."""
import os, tempfile
fd,path=tempfile.mkstemp(suffix='.db'); os.close(fd)
os.environ['DATABASE_URL']=f'sqlite:///{path}'
os.environ['SKULLHARBOR_DATA_DIR']=tempfile.mkdtemp()
import main
from fastapi import HTTPException
from database import Base,engine,SessionLocal
from models import User, EntitlementInstallation
Base.metadata.create_all(bind=engine)
db=SessionLocal()
try:
    # Exercise production behavior even though the source tree carries the dev marker.
    main._DEV_AUTHORITY_ENABLED=False
    a=User(name='A',email='a@example.test',company_name='A Ltd',verification_status='approved')
    b=User(name='B',email='b@example.test',company_name='B Ltd',verification_status='approved')
    db.add_all([a,b]); db.commit(); db.refresh(a); db.refresh(b)

    # Before activation, historical rows must not become an implicit identity.
    assert main.users(db)==[]
    try:
        main._require_workspace_customer(db,a.id)
        raise AssertionError('unbound production customer was accepted')
    except HTTPException as exc:
        assert exc.status_code==403

    installation=main._installation_id()
    db.add(EntitlementInstallation(user_id=a.id,installation_id=installation,status='active'))
    db.commit()

    # Restart-equivalent resolution returns exactly the bound customer.
    rows=main.users(db)
    assert len(rows)==1 and rows[0]['id']==a.id
    assert main._require_workspace_customer(db,a.id).id==a.id
    try:
        main._require_workspace_customer(db,b.id)
        raise AssertionError('foreign local customer was accepted')
    except HTTPException as exc:
        assert exc.status_code==403

    # Releasing the binding locks the workspace again; it must not fall back to A/B.
    binding=db.query(EntitlementInstallation).filter_by(installation_id=installation).first()
    binding.status='released'; db.commit()
    assert main.users(db)==[]
finally:
    db.close(); engine.dispose()
    try: os.unlink(path)
    except OSError: pass
print('sprint 8 step 6 installation workspace binding tests: OK')
