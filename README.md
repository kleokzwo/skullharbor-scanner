# SkullHarbor UI-Scanner v0.4.0

KISS pentest quick-check MVP: React/Vite/Tailwind frontend + FastAPI backend + SQLAlchemy + scanner adapters.

## Current security flow

```text
Add target
   ↓
Publish DNS TXT challenge
   ↓
Verify target
   ↓
Scan gate checks exact verified hostname + public DNS
   ↓
FREE web-security profile
   ↓
Normalized findings
```

An arbitrary URL can no longer be scanned merely by typing it into the UI/API.

## Run backend

Internal scanner adapters must be installed on the backend host. See `THIRD_PARTY.md`.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Default DB: `backend/ui_scanner.db`.

## Run frontend

```bash
cd frontend
npm install
npm run dev
```

## Verify a target

Create challenge:

```bash
curl -X POST http://127.0.0.1:8000/api/targets \
  -H 'Content-Type: application/json' \
  -d '{"domain":"example.com"}'
```

Publish the returned TXT record, then:

```bash
curl -X POST http://127.0.0.1:8000/api/targets/1/verify
```

Only after `status` becomes `verified` will `/api/scan` accept that exact hostname.

## API

- `GET /api/health`
- `GET /api/users`
- `POST /api/users`
- `GET /api/targets`
- `POST /api/targets`
- `POST /api/targets/{id}/verify`
- `GET /api/scans`
- `GET /api/scans/{id}`
- `GET /api/scans/{id}/status`
- `POST /api/scans/{id}/stop`
- `POST /api/scan`

## Safety rules

- only exact verified hostnames can be scanned
- localhost/private/link-local/reserved/non-global IP destinations are rejected
- DNS is checked again immediately before the web security engine runs
- scanner flags are server-controlled
- FREE scans use only tuning categories `1,2`
- DoS scan categories are not exposed to self-service users

See `docs/SPRINT-02-TARGET-VERIFICATION.md` for the E2E test plan.

## Sprint 8 Step 6 architecture hardening

Product coverage is now policy-owned under `backend/services/plans/`. FREE uses
only the primary bounded web check. Advanced composes primary + controlled
known-vulnerability/misconfiguration checks + bounded web-surface discovery.
Customer-facing APIs remain vendor-neutral.

Frontend page boundaries are under `frontend/src/pages/`; new page presentation
must be implemented there rather than expanding the application controller.
