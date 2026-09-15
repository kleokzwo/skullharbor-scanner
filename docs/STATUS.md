# Current Status

**Project:** SkullHarbor UI-Scanner  
**Current sprint:** Sprint 6 — License / Entitlement Authority  
**Build:** v0.6.0-dev  
**Status:** SPRINT 4 COMPLETE / SPRINT 4.1 COMPLETE / SPRINT 5 COMPLETE / SPRINT 6 STEP 1 COMPLETE / SPRINT 6 STEP 2 COMPLETE / SPRINT 6 STEP 3 COMPLETE / SPRINT 6 COMPLETE

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

## Sprint 5 — Step 1

- Downloadable/local architecture explicitly preserved: scans and findings stay on the customer machine.
- Customer verification states added: pending / approved / rejected / suspended.
- New accounts start pending.
- Scan creation now requires an approved customer and still separately requires an exact verified target.
- No public approval mutation endpoint or customer-controlled approval field exists.
- Local approval state is not treated as anti-tamper DRM; trusted/signed entitlement authority remains a later concern.

## Sprint 5 — Step 2

- Minimal company review payload added: company name, company domain and intended authorized use.
- Company profile edits never change approval state.
- Company domain is identity/review metadata only and never substitutes for exact-host DNS authorization.
- No approval/tier/license/scanner controls exist in the company profile request.
- Local/downloadable scan architecture remains unchanged.

## Sprint 5 — Step 3

- Internal trusted/admin review boundary added; no customer-facing decision endpoint exists.
- Explicit trusted roles, review source, decisions and fail-closed state transitions.
- Approval requires complete Step-2 customer/company review data.
- Rejection requires a reason; successful decisions are written to a minimal audit trail.
- Audit data contains no targets, scans, findings, raw output or DNS verification secrets.
- Existing approved-customer scan gate remains authoritative for local self-service execution.
- 13/13 backend regression/policy tests pass.

## Sprint 5 — Step 4 / Closeout

- Customer-facing request models reject unknown/protected fields instead of silently ignoring them.
- Customer approval is checked before target parsing/DNS resolution on scan creation.
- Failed trusted-review attempts do not mutate customer state or create audit decisions.
- Reviewer identity is bounded before audit persistence.
- Dedicated Sprint-5 security closeout regression added.
- 14/14 backend regression/policy/security tests pass.
- **SPRINT 5 COMPLETE.**

## Sprint 6 — Step 1 — Entitlement State & Policy Resolution

- Added a minimal entitlement authority cache separated from scan/target data.
- Resolved public states are `ACTIVE`, `TRIAL`, `EXPIRED`, `NO_SEAT` and `BLOCKED`.
- Customer approval remains an independent prerequisite; a valid entitlement cannot bypass Sprint-5 verification.
- Missing, malformed or untrusted-source entitlement state fails closed as `BLOCKED`.
- `TRIAL` is deliberately bounded to the server-owned FREE scan profile.
- Trial duration is capped at 7 days; missing/overlong trial validity fails closed. Entitlement expiry is evaluated consistently in UTC.
- `ACTIVE` maps to the authority-selected product profile; ANNUAL remains managed-only and cannot execute self-service.
- Scan requests contain no entitlement/license/tier/profile controls.
- Entitlement is checked before target parsing/DNS work.
- Customer has read-only entitlement status; no customer mutation endpoint was added.
- Entitlement storage contains no targets, scans, findings, raw output or DNS verification tokens.
- 15/15 backend regression/policy tests pass.

## Sprint 6 — Step 2 — Trusted Issuance / Seat & Installation Lifecycle

- Added internal trusted issuance for approved customers only.
- Only `entitlement-admin` / `admin` from `entitlement-authority` may mutate lifecycle state.
- Added authority-owned license ID, bounded seat limit and issuance timestamp.
- Added opaque installation bindings with active/released lifecycle and strict seat enforcement.
- FREE trial issuance remains capped at 7 days.
- Added trusted blocked/expired lifecycle termination.
- Added minimal lifecycle audit without target, scan, finding, raw-output or DNS-verification data.
- No customer entitlement mutation endpoint was added.
- 16/16 backend regression/policy tests pass.

## Sprint 6 — Step 3 — Signed Entitlement / Local Trust Verification

- Added canonical minimal signed entitlement grants for active installation bindings.
- Ed25519 keeps the authority private signing key out of the downloadable local scanner; local verification needs only a public key.
- Signed grants contain no targets, scans, findings, raw output or DNS verification secrets.
- Signature, exact payload shape, installation binding, product/status policy, seat bounds and UTC expiry are verified fail-closed.
- Tampering, wrong keys, wrong installations, released bindings, expired grants and extra fields are rejected.
- ANNUAL remains managed-only and is not accepted as a self-service signed grant.
- 17/17 backend regression/policy tests pass.

## Sprint 6 — Step 4 / Closeout

- Signed local grants are capped at 24 hours and never exceed authority-side entitlement expiry.
- Local verification now validates issued-at, expiry, timezone, positive bounded lifetime and future-clock skew fail-closed.
- Authority block/release prevents fresh grant issuance immediately; disconnected replay of an already issued grant is explicitly bounded to at most 24 hours.
- No targets, scans, findings, raw scanner output or DNS verification data enter the entitlement boundary.
- Dedicated Sprint-6 security closeout regression added.
- **SPRINT 6 COMPLETE.**

## Next

Do not begin the next sprint until Sprint 6 closeout is confirmed on the target machine.


## Sprint 4.1 — Scan Profiles & Product Tiers

**Step 1: DONE**

- Server-owned FREE / MONTHLY / ANNUAL scan policies added.
- FREE remains the only pre-license self-service entitlement.
- MONTHLY has controlled expanded depth; DoS tuning category 6 excluded.
- ANNUAL is managed pentest only: hello@skullharbor.org, two pentests/year.
- Customer scan requests cannot supply tier, scanner, tuning, flags or raw arguments.
- Regression + profile-policy tests pass.


## Sprint 4.1 — Step 2

- MONTHLY now orchestrates three private adapter slots: primary, secondary and bounded web-surface discovery.
- FREE remains primary-only.
- Surface discovery is restricted to TCP 80/443/8080/8443 with no scripts, UDP, OS/version detection or customer-controlled port list.
- All current internal tool names are covered by the customer-boundary regression test.
- 9/9 backend tests pass.


## Sprint 4.1 — Step 3 / Closeout

- End-to-end tier orchestration policy test added.
- FREE is verified primary-only.
- MONTHLY is verified primary + secondary + bounded surface discovery.
- ANNUAL is verified fail-closed for self-service execution.
- Customer request cannot select or escalate tier, scanners, tuning or raw flags.
- Sprint 4.1 Definition of Done is satisfied.
- Next sprint: Sprint 5 — Customer / Company Verification.
