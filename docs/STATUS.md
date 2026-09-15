# Current Status

**Project:** SkullHarbor UI-Scanner  
**Current sprint:** Sprint 4 — Scan Engine & Orchestration  
**Build:** v0.4.0  
**Status:** SPRINT 4 COMPLETE

## Completed foundations

- Sprint 1: Quick Check MVP, controlled FREE web profile, live progress/stop
- Sprint 2: exact-host DNS verification, authorization gate, public-IP protection
- Sprint 3: normalized finding engine and SkullHarbor-only customer-facing branding
- Sprint 4 / Step 1: central `ScanEngine`, queued/running lifecycle, cancellation, execution-time authorization re-check and centralized finding persistence
- Sprint 4 / Step 2: second bounded internal web-security adapter, unified normalized findings and shared cancellation/orchestration
- Sprint 4 / Step 3: partial-failure isolation, private adapter telemetry and cross-adapter finding deduplication
- Sprint 4 / Step 4: execution budgets, process termination and cancellation hardening
- Sprint 4 / Step 5: deterministic DB state-transition coverage and customer API boundary hardening

## Current architecture

FastAPI validates the request and verified target, creates a queued scan record and hands it to `ScanEngine`. The engine owns execution state and invokes private internal adapters. Adapters return the common normalized Finding schema. Customer-facing API/UI data remains scanner-agnostic.

## Next

Sprint 5 — Customer / Company Verification. Registration must not automatically grant commercial scanner access; add approval state and abuse controls before licensing.


## Sprint 4.1 — Scan Profiles & Product Tiers

**Step 1: DONE**

- Server-owned FREE / MONTHLY / ANNUAL scan policies added.
- FREE remains the only pre-license self-service entitlement.
- MONTHLY has controlled expanded depth; DoS tuning category 6 excluded.
- ANNUAL is managed pentest only: hello@skullharbor.org, two pentests/year.
- Customer scan requests cannot supply tier, scanner, tuning, flags or raw arguments.
- Regression + profile-policy tests pass.
