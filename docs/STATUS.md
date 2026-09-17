# Current Status

**Project:** SkullHarbor UI-Scanner  
**Current sprint:** Sprint 8 — Product UX  
**Build:** v0.8.0-dev  
**Status:** SPRINTS 1–7 COMPLETE / SPRINT 8 STEPS 1–2 CONFIRMED / SPRINT 8 STEP 3 IMPLEMENTED — TARGET-MACHINE CONFIRMATION PENDING

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

## Sprint 7 — Step 1 — Trusted Engagement Scope Foundation

- Added a separate trusted engagement authorization model for professional/customer-approved third-party scopes.
- Engagement approval is internal-only and requires an approved SkullHarbor customer plus an `engagement-reviewer`/`admin` actor from the exact `engagement-authority` source.
- Scope entries are exact normalized hostnames only; no wildcard/subdomain inheritance is granted.
- Engagements have explicit validity windows and approved/revoked/expired lifecycle semantics.
- Scan authorization now accepts either the existing verified exact-host ownership record or a currently approved exact-host engagement scope for the same user.
- Customer engagement API is read-only; no customer self-approval/mutation endpoint exists.
- Engagement/audit storage contains no scans, findings, raw scanner output, DNS verification secrets or scanner controls.
- `test_engagement_authorization.py` adds positive/negative scope, trust, expiry, revocation, boundary and minimization regression coverage.

## Sprint 7 — Step 2 — Authorization Hardening & Local Provenance

- Engagement authorization independently rechecks Sprint-5 customer approval.
- Exact-host matching is canonicalized again at the authorization boundary; malformed hosts fail closed.
- Local scans retain the authorizing `engagement_id` when engagement scope is used.
- Engagement authority/audit storage remains free of scan IDs, targets, findings, raw output and scanner data.
- Invalid lifecycle transitions remain non-mutating and do not create audit decisions.
- `test_engagement_hardening.py` adds defense-in-depth and provenance regression coverage.

## Next

Sprint 7 Step 3 only after Step 2 is confirmed on the target machine.


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

## Sprint 7 — Step 3 / Closeout

- Scan authorization now resolves verified ownership or approved engagement scope in one local policy decision.
- The engagement returned by that decision is the same engagement retained as local scan provenance, avoiding a split-check authorization gap.
- Verified ownership takes precedence when both authorization paths exist.
- Cross-customer scope reuse and revoked engagement reuse fail closed.
- Engagement authority/audit storage remains free of scan IDs, findings, raw output, scanner data and DNS verification secrets.
- `test_sprint7_security_closeout.py` adds Sprint-7 closeout coverage.
- **SPRINT 7 COMPLETE.**

## Next

Sprint 8 — Product UX. Do not begin it as part of the Sprint-7 closeout.

## Sprint 8 — Step 1 — Dashboard Access & Readiness

- Product UX starts with the roadmap's mobile-first dashboard.
- Added a customer-safe local product/readiness summary combining existing verification, entitlement and scope state.
- Dashboard presents Customer / Product access / Authorized scope in plain SkullHarbor language.
- Start Scan is UX-disabled until readiness is satisfied, while `/api/scan` remains the authoritative security gate.
- Header product badge is resolved from entitlement instead of hard-coded FREE.
- Readiness summary exposes counts/status only; no target hostname, scan ID, finding, raw output, scanner identity or DNS secret is added.
- No cloud scan path or central scan-data flow introduced.
- `test_product_ux_step1.py` added.
- **Sprint 8 Step 2 implementation complete; awaiting target-machine regression confirmation before Step 2.**

- Sprint 8 Step 2 Fix 4: legacy verified targets retain ownership through deterministic local migration; no repeated DNS challenge.
- Sprint 8 Step 2 Fix 5: multi-profile legacy ownership migration now uses deterministic historical/company/eligible-customer provenance; added full upgrade integration regression. Step 2 still awaits target-machine confirmation.

## Sprint 8 — Step 2 runtime closeout Fix 9

- Fixed the target-machine five-minute Quick Check failure after successful authorization.
- FREE primary web check now receives a 90-second graceful internal runtime cap; MONTHLY receives 180 seconds.
- The process watchdog remains backend-owned and fires only after a 20-second grace window, so structured results can be flushed instead of discarded by an abrupt 300-second kill.
- Cancellation and authorization behavior are unchanged.
- Added `test_quick_check_runtime_budget.py`; regression baseline is 28 tests.


## Product policy refinement — current

- FREE primary depth: `1,2`.
- MONTHLY primary depth: `1,2,3,4,9,b`; SQL-injection category `9` is explicitly included.
- DoS category `6` remains excluded from every customer self-service tier.
- MONTHLY retains controlled secondary web checks and bounded web-surface discovery; destructive/intrusive/fuzz/bruteforce classes remain excluded from automatic customer scans.
- ANNUAL remains a managed pentest, not an unrestricted automated scanner tier.
- Public/marketing presentation describes security coverage and customer benefit only; internal scanner brands, tuning codes and CLI details remain private implementation details.

## Sprint 8 — Step 3 — Scan & Finding Experience

- Replaced customer-facing technical scan logs/stage identifiers with simple SkullHarbor progress states.
- Completed results now use outcome-oriented summaries and a clear zero-finding limitation statement.
- Finding detail keeps normalized evidence and remediation guidance but removes raw-adapter wording/internal rule presentation from normal customer UX.
- Removed the unimplemented false-positive placeholder control.
- No authorization, entitlement, scan-profile or local-execution boundary changed.
- Added `test_product_ux_step3.py`.
- **Step 3 implementation complete; awaiting target-machine confirmation before Step 4.**

## Sprint 8 Step 4 — Product UX Closeout / Tier Validation
Implemented, pending product-owner target-machine confirmation. Development-only Trusted Test Authority can now switch a verified test customer between FREE trial and MONTHLY active access so both real self-service policies can be exercised end-to-end. Production trust boundaries remain unchanged.

## 2026-09-16 — Sprint 8 Step 4 current
Single-customer trial/upgrade lifecycle is now the active feature step. Customer/company identity is durable; FREE -> Advanced changes trusted entitlement only. Dashboard profile switching was removed from customer UX, Settings now separates Organization from Plan & billing, and Custom/yearly remains managed pentest. Commercial/legal checkout implementation is deferred to its dedicated later sprint.
