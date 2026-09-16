# Sprint 1 — Nikto MVP

**Status:** IN PROGRESS  
**Current build:** UI-Scanner v0.1.3  
**Sprint goal:** Complete one reliable end-to-end Nikto Quick Check before adding another scanner.

## Definition of Done

Sprint 1 is complete when an authorized target can be entered in the React UI, the FastAPI backend starts Nikto, live progress is visible, the scan can be stopped, Nikto output is normalized, findings are stored locally, and completed scans/findings can be reopened in the UI.

## Development log

### Step 1 — Project direction

**Done**

The project was defined as **SkullHarbor Pentest Quick-Check Tool** with repository name `UI-Scanner`.

Architecture chosen:

```text
React/Vite
    |
FastAPI
    |
Scanner adapter
    |
Normalizer
    |
Local database
```

Existing scanners are integrated instead of implementing a new vulnerability scanner.

Initial scanner order:

1. Nikto
2. Nmap
3. Nuclei

### Step 2 — Backend MVP

**Done**

Implemented:

- FastAPI backend
- `/api/health`
- `/api/scan`
- target URL validation
- Nikto CLI adapter
- JSON result handling
- basic Nikto normalizer
- scanner timeout/error handling foundation

### Step 3 — Local persistence

**Done**

Implemented SQLAlchemy models:

- `users`
- `scans`
- `findings`

A scan can optionally be assigned to a user.

SQLite is the default local database. `DATABASE_URL` is supported for later integration, but the existing SkullHarbor production database must not be connected blindly without reviewing its schema/migrations.

### Step 4 — React UI

**Done**

Implemented React/Vite frontend with:

- target field
- user assignment
- Start Quick Check
- recent scan history
- findings panel
- severity presentation
- SkullHarbor dark UI

### Step 5 — Environment compatibility fix

**Done**

Kali Rolling was using Python 3.14.6. The pinned Pydantic build was incompatible with that environment because its PyO3 version supported up to Python 3.13.

Development environment changed to:

```text
Python 3.13.15
```

Backend health endpoint was successfully started and verified.

### Step 6 — Scan progress UX

**Done in code — needs end-to-end verification**

UI-Scanner v0.1.1 added:

- background Nikto execution
- animated scanning state
- elapsed timer
- five-stage progress stepper
- percentage progress bar
- live Nikto console
- Stop button
- findings placeholder while scan runs
- `/api/scans/{id}/status`
- `/api/scans/{id}/stop`

Stages:

```text
Initializing
    |
Running Nikto
    |
Processing
    |
Saving
    |
Completed
```

## Current Sprint 1 checklist

- [x] Repository structure
- [x] React/Vite frontend
- [x] FastAPI backend
- [x] Local SQLAlchemy database
- [x] User/scan/finding data model
- [x] Nikto adapter
- [x] Basic normalizer
- [x] Scan history UI
- [x] Live progress UI implemented
- [x] Backend health check verified
- [ ] Run first complete Nikto scan from React UI
- [ ] Verify live Nikto console output
- [ ] Verify progress-stage transitions
- [ ] Verify elapsed timer
- [ ] Verify Stop behavior
- [ ] Verify real Nikto JSON against normalizer
- [ ] Verify findings persisted in database
- [ ] Verify findings render correctly in UI
- [ ] Verify completed scan can be reopened from history
- [ ] Test invalid/unresolvable target
- [ ] Test Nikto failure/error state
- [ ] Fix issues discovered during E2E testing
- [ ] Mark Sprint 1 DONE

## Next action

Start the first authorized end-to-end Nikto test using UI-Scanner v0.1.1.

Do **not** start Nmap or Nuclei integration until this checklist is green.

### Step 7 — License-controlled Nikto profiles + customer findings UI

**Implemented in v0.1.2 — E2E verification pending**

Nikto scan depth is now controlled by the backend. The frontend cannot submit raw `-Tuning` values.

Current profiles:

```text
FREE     -> -Tuning 12
MONTHLY  -> -Tuning 12349b (reserved for later authenticated licensing)
ANNUAL   -> manual pentest engagement; not an unrestricted self-service profile
```

Nikto tuning category `6` (Denial of Service) is intentionally excluded from customer self-service profiles.

Implemented:

- server-side `NIKTO_PROFILES`
- FREE scans are hard-wired to the `free` profile in `/api/scan`
- Nikto receives `-Tuning 12` for current self-service scans
- scan profile is persisted on scans
- normalized findings now include customer-facing `impact` and `recommendation`
- lightweight SQLite compatibility migration for the new v0.1.2 columns
- light UI replacing the dark scanner-centric presentation
- result summary with Critical / High / Medium / Low / Info counts
- simple finding list
- clickable finding detail view
- finding detail answers: What did we find? Why does this matter? What should I do?
- technical evidence/reference hidden behind an expandable section
- live Nikto console hidden behind an expandable Technical scan log
- FREE / Quick profile is visible to the user without exposing raw CLI controls

Security rule: future paid profiles must be selected from authenticated server-side entitlement data. Never trust a profile or raw Nikto tuning value supplied by the browser.


### Step 8 — Dedicated Finding Page

**Implemented in v0.1.3 — E2E verification pending**

The modal-based finding view was removed to make the result easier for non-technical customers to read.

Implemented:

- `View` opens a dedicated finding page instead of a modal
- clear `Back to results` navigation
- large severity + OPEN status header
- target, scanner and scan date shown as simple facts
- separate customer-language cards for `What did we find?`, `Why does this matter?`, and `What should I do?`
- Technical details, raw Nikto output and references remain collapsed by default
- previous/next finding navigation for scans with multiple findings
- browser history/hash support so Back returns to scan results
- dashboard order simplified so Findings are visually primary and Recent scans are secondary

KISS rule: the customer-facing page explains the result first; scanner evidence is secondary and opt-in.

### Step: v0.1.4 Tailwind UI parity

The v0.1.3 CSS implementation was replaced by a mobile-first Tailwind CSS frontend to match the approved dashboard/finding-detail mockup more closely. Backend scan behavior remains unchanged.
