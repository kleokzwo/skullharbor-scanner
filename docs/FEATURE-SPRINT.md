# SkullHarbor — Feature Sprint Plan

This file is the working product-feature sequence. Development follows these steps in order; do not skip ahead unless a blocking defect must be fixed first.


### Step 6 architecture hardening — SOLID/KISS refactor 2

- Frontend page markup is physically split from `main.jsx` into `src/pages/` (Dashboard, Scans, Targets, Settings, Finding, Setup).
- Shared presentation primitives live in `src/components/ui.jsx`; `main.jsx` is reduced to application state/API orchestration and page routing.
- FREE and Advanced product policies remain isolated in `backend/services/plans/free.py` and `advanced.py`.
- Target canonicalization/public-IP validation moved to `backend/services/target_security.py` and is reused by the existing scan engine.
- Existing customer isolation, ownership, entitlement and installation-binding enforcement remains backend-authoritative and fail-closed.
- Architecture regression prevents `main.jsx` from silently becoming the page monolith again.
- No customer-facing scanner-engine names were introduced.

## Sprint 8 — Product UX

### Step 1 — Dashboard Access & Readiness — DONE
Translate existing verification, entitlement and authorization state into a simple customer readiness view. Backend security remains authoritative.

### Step 2 — Target Ownership Onboarding — DONE
Guided DNS ownership verification, verified-target handoff and upgraded-database compatibility. Existing ownership proof must not be repeated without cause.

### Step 3 — Scan & Finding Experience — DONE
Customer-safe scan progress and normalized finding presentation. No internal scanner names or raw technical scan log in normal customer UX.

### Step 4 — Single-Customer Trial & Upgrade Lifecycle — DONE

**Goal:** one customer/company identity for the whole SkullHarbor relationship.

Lifecycle:

`Company registration -> trusted approval -> 7-day FREE trial -> Advanced upgrade OR trial expiry`

Rules:

- Company/customer registration happens once.
- Work email/company/domain are not re-entered on upgrade.
- FREE, Advanced and future access are entitlements of the same customer, never new profiles.
- Existing verified websites remain verified across plan changes.
- Existing valid engagement authorization remains governed by its own validity and is not recreated by plan changes.
- FREE trial is maximum 7 days and FREE-only.
- Trial expiry blocks new scans but does not delete or hide existing local scan history/findings.
- FREE -> Advanced changes only trusted product entitlement and resolves to the MONTHLY scan profile.
- Advanced self-service policy remains controlled; DoS category 6 remains excluded.
- Custom/yearly is a managed pentest engagement with separate scope/contract handling, not a self-service super-tier.
- Development tier simulation is internal-only and must not ship in production.

Acceptance for Step 4:

- Dashboard has no tariff/customer-profile switching concept.
- Settings clearly separates Organization from Plan & billing.
- Same customer can move FREE -> Advanced without duplicate-email/company errors.
- Upgrade preserves customer ID, company data and verified target ownership proof.
- Advanced becomes ACTIVE and the next authorized scan uses the monthly profile.
- Expired access remains fail-closed for new scans.
- Settings automatically resolves the already-bound local customer; legacy duplicate rows must not force re-registration during an upgrade.
- Plan & billing includes a customer-safe Free / Advanced / Custom comparison so upgrade value is understandable without exposing internal scanner names or tuning codes.
- Settings must never display a pending/missing organization as verified, and expired/blocked Advanced access must never be presented as active. Plan changes preserve local identity/scope data even when access is inactive.

### Step 5 — Professional Plan UX — DONE
Customer-facing plan state, trial time remaining, Advanced active state and a clean upgrade/manage-subscription surface. No internal entitlement terminology.

Implemented for local product acceptance:

- Free Trial shows customer-friendly remaining time (`X days left`) and the trial end date.
- Advanced shows `Active` rather than authority/internal entitlement state names.
- Expired/inactive access is presented in customer language while scan enforcement remains backend-authoritative.
- Advanced has a dedicated Manage subscription surface; commercial subscription management remains intentionally disabled until the later checkout/contract sprint.
- Upgrade surface remains in Settings; Dashboard stays Quick-Check-centered.
- Dashboard readiness shows concise plan context (`Free Trial · X days left` or `Advanced · Active`) without exposing scanner or entitlement internals.
- Development-only plan simulation remains isolated in Development testing controls.

### Step 6 — Download & First-Run Onboarding — CURRENT
Target product journey:

`Website -> company registration -> verification/approval -> download -> install -> activate -> Quick Check`

The released desktop product must start by clicking the installed application. No Python, npm, terminal commands or user-run scripts.

Implemented for local product acceptance:

- Production first run fails closed when no approved customer is bound: no scan workspace is exposed as usable.
- First-run UX explains the required sequence: organization registration -> approval -> activation.
- Production first run does not create a customer/company locally and does not simulate trusted approval.
- Development authority remains the only place where local test setup/simulation is allowed.
- A single local `desktop_launcher.py` entrypoint starts the loopback-only application and opens the locally served UI; production packaging can wrap this entrypoint so customers do not run Python/npm/backend commands.
- FastAPI serves a built frontend from the same local process when `frontend/dist` exists. Targets, scans and findings remain local.
- Trusted production activation transport is deliberately not invented in the desktop client; wiring it requires the production Authority endpoint/public-key configuration and remains part of Step 6 before DONE.

### Step 7 — Sprint-8 Security & UX Closeout — PLANNED
End-to-end regression of registration, trial, ownership/engagement authorization, FREE scan, upgrade, Advanced scan and expiry/lock behavior while preserving local-only scan data.

## Later commercial/legal sprint — NOT Sprint 8

Define and then implement payment, contract acceptance/versioning, renewal, cancellation, invoices, applicable withdrawal/cancellation information and the Custom/yearly contracting flow. Legal text and deadlines are not hard-coded before the applicable business/legal model is reviewed.

#### Step 5 security hotfix — customer isolation / FREE target boundary

A local product-acceptance test exposed two blocking defects; Step 5 cannot close until these are locally re-tested.

- Scan history, scan detail, live status and stop operations are customer-scoped in the backend. Switching the development customer must never display another customer's scans/findings.
- The frontend never changes customer identity because a typed/selected hostname belongs to another local customer. Identity is resolved first; scans and targets are loaded for that customer only.
- FREE Trial may enroll/authorize one self-service website. Adding a second website is backend-blocked with an upgrade-required response.
- Advanced may enroll additional websites, but every website still requires its own exact ownership verification (or a separately approved exact-host engagement where applicable). Upgrade never transfers ownership from another customer.
- Cross-customer scan IDs return not-found to the requesting customer; foreign scan detail/status cannot be read or stopped.
- These are authorization boundaries, not UI-only restrictions, and must fail closed.

### Sprint 8 / Step 5 — Security Hotfix 2 (customer-scoped ownership)
- Product readiness may count verified ownership only when the verified target belongs to the active customer.
- A verified target owned by another customer must never enable Start Scan.
- The authoritative `/api/scan` authorization remains exact-customer scoped and fail-closed.
- Target verification is customer-scoped; foreign target IDs return 404.
- Cross-customer domain enrollment returns a support path (`hello@skullharbor.org`) without transferring ownership.
- Development builds may explicitly switch customer workspaces for isolation testing; production remains single-customer and this control is development-only.
- Target cards never switch customer identity implicitly.

### Sprint 8 / Step 6 — Activation transport hardening 1
- Production first-run now accepts a one-time activation code only after the organization was approved outside the desktop app.
- The desktop activation request contains only the one-time code plus an opaque installation identifier. Targets, scans, findings and scanner data are never part of activation transport.
- Production Authority URL is configuration-only and HTTPS is mandatory; no local production self-approval fallback exists.
- Authority entitlement is Ed25519-verified locally and must match the exact installation identifier before approved/product state is cached.
- Missing Authority configuration, invalid/expired code, bad signature, wrong installation, malformed response or unavailable Authority all fail closed.
- Installation identifier is generated once and persisted locally with restrictive file permissions where supported.
- Development authority remains separate and must be omitted from production packaging.


### Sprint 8 / Step 6 — UX hotfix: page-scoped feedback
- Verification/ownership errors and success notices are transient, page-scoped feedback.
- Navigating to another menu clears those messages immediately; a target authorization error must never appear later in Settings, Dashboard, Scans or another unrelated workspace.
- The backend authorization decision is unchanged; this hotfix only prevents stale UI state from leaking across pages.

### Sprint 8 / Step 6 — Installation workspace binding hardening
- Production startup never chooses a customer from arbitrary local database rows, targets, scans, e-mail addresses, or request-supplied IDs.
- The only production customer workspace exposed after activation is the customer with an active binding for this installation identifier.
- Before activation, `/api/users` exposes no historical/local customer as an implicit identity; first-run remains locked.
- Customer-facing target, scan, scan-detail/status/stop, product-status and readiness paths reject a request that names a different local customer.
- A released/missing installation binding fails closed and does not fall back to another local customer.
- Development multi-customer switching remains explicit and isolated to the development build for tenant-isolation testing.

### Sprint 8 / Step 6 — architecture & Advanced coverage hardening
- FREE remains the bounded primary web check only (policy `12`).
- Advanced explicitly orchestrates all three private adapter slots: primary + secondary known-vulnerability/misconfiguration coverage + bounded web-surface discovery.
- Advanced secondary policy is server-owned and restricted to controlled families (`cve`, `misconfig`, `exposure`, `tech`, `xss`, `sqli`) with disruptive classes explicitly excluded (`dos`, `fuzz`, `bruteforce`, `intrusive`, `headless`), low rate/concurrency, and no customer-supplied flags.
- Advanced surface discovery remains TCP/web-focused and bounded to a small server-owned port set; no UDP, OS scan, NSE scripts, brute force or unrestricted modes.
- Product policy moved into `backend/services/plans/free.py` and `advanced.py` so paid/free coverage can be maintained without editing API routes.
- Frontend `src/pages/` boundaries added for Dashboard, Scans, Targets, Settings and Finding. New page-specific presentation work must live there; `main.jsx` remains the controller while existing JSX is migrated without changing security behavior.
- This refactor is intentionally behavior-preserving for customer identity, target authorization, installation binding and tenant isolation.


### Sprint 8 / Step 6 — Composition-root refactor 2 (2026-09-17)
- Backend `main.py` is now a thin ASGI composition root only; business/API implementation was moved out without behavior changes.
- Frontend `main.jsx` is now bootstrap-only; application orchestration lives under `src/app/` and page rendering remains under `src/pages/`.
- Existing regression compatibility is retained through a temporary backend attribute bridge; new code must import owning modules directly.
- Fixed the shared target-security import so public-IP resolution uses the centralized fail-closed target policy.
- Release rule: entrypoints must never accumulate product, entitlement, authorization, target, scan, or UI-page business logic again.

### Sprint 8 / Step 6 — Composition Refactor 4 (architecture correction)
- Backend monolithic `application.py` removed as runtime implementation; it is now compatibility-only.
- `main.py` is composition/bootstrap only and contains no product/business rules.
- FastAPI composition moved to `app_factory.py`.
- API endpoints are split into controllers: system, customer, target, scan.
- Business rules are split into services: customer, workspace, engagement, entitlement, verification, target security, plan policies.
- Request DTOs live under `schemas/`; persistence models remain in `models.py`; startup/database compatibility lives under `infrastructure/`; runtime/config wiring lives under `core/`.
- Development-only compatibility hooks are isolated in `development_compat.py` and must not ship in production packaging.
- Frontend bootstrap remains minimal; `App.jsx` is composition-only; orchestration is in `controllers/AppController.jsx`; pages remain under `pages/`; API transport starts under `services/`.
- Security behavior is intentionally preserved: customer isolation, exact target ownership/engagement authorization, entitlement gating and installation binding remain backend authoritative/fail-closed.

### Sprint 8 / Step 6 — Advanced Coverage Hardening (2026-09-17)
- Advanced remains three bounded internal coverage families: core web security, known vulnerability/exposure checks, and public-service exposure.
- Paid Advanced is now fail-closed for promised coverage: all configured Advanced coverage families must complete before the scan may be published as COMPLETED.
- A failed/timeout Advanced family can no longer silently produce a partial FREE-like "Advanced" result.
- Completed scans persist a vendor-neutral coverage summary; customer UI shows coverage completion without exposing internal scanner/tool names.
- Finding count is not artificially inflated: a completed coverage family may legitimately return zero findings.
- DoS, fuzzing, brute force, intrusive/headless classes and unrestricted surface scanning remain excluded from self-service.


### Sprint 8 / Step 6 — Advanced real-scan runtime hotfix
- Fixed real Advanced scans stalling on blanket historical CVE template coverage.
- Known-vulnerability coverage now uses bounded technology-aware automatic matching plus controlled misconfiguration/exposure/XSS/SQLi/technology families.
- Added request timeout/retry/host-error bounds and disabled update checks during a customer scan.
- Failed/stopped Advanced scans never render a zero-finding result card; partial results remain unpublished.

### Sprint 8 / Step 6 — Advanced Runtime Hotfix 4 + Finding Attribution
- Kept the hard 120-second secondary coverage budget; fixed throughput inside that budget instead of extending customer wait time.
- Advanced secondary checks now use bounded 15 req/s, concurrency 5, 4-second request timeout and zero retries; disruptive template classes remain excluded.
- Every normalized finding is now persisted with a customer-safe coverage family (Core web security / Known vulnerability & exposure checks / Public service exposure).
- Advanced Findings UI is grouped by coverage family and lists the actual findings under each family; coverage completion cards remain execution evidence, not a replacement for findings.
- SQLite compatibility migration adds `findings.coverage_family` without deleting existing data; legacy findings fall back to Core web security in the customer API.


### Sprint 8 / Step 6 — Advanced Runtime Hotfix 5
- Fixed the persistent paid secondary-check timeout at its source: automatic workflow expansion is disabled for Quick Check.
- Advanced secondary coverage now uses the explicit bounded SkullHarbor tag allow-list only (misconfiguration, exposure, technology, XSS, SQL injection), with disruptive classes still excluded.
- Customer wording no longer overclaims blanket CVE coverage; the family is shown as “Vulnerability & exposure checks”.
- Successful Advanced results keep coverage completion separate from the actual itemized findings. Findings are grouped by coverage family and each finding remains individually openable.
- 3/3 fail-closed publication remains mandatory; failed scans do not publish partial security findings.


### Sprint 8 / Step 6 — Advanced Coverage Integrity Hotfix 6
- Coverage completion is evidence-based; process exit code alone is insufficient.
- Core connectivity failures are operational diagnostics and are never published as INFO security findings.
- Surface coverage requires parseable completed probe evidence.
- Successful Advanced results still publish concrete findings grouped by coverage family.
- 3/3 remains fail-closed for Advanced.

### Sprint 8 / Step 6 — Primary HTTPS Invocation Hotfix 7
- Root cause of the Hotfix-6 Core failure identified: rewriting an already-authorized HTTPS URL into separate host/port/`-ssl` arguments changed execution behavior on the supported Kali primary-engine build.
- Primary execution now preserves the canonical authorized target URL exactly as the previously working path did.
- Coverage-integrity hardening from Hotfix 6 remains: connectivity diagnostics are filtered from findings and a connectivity-only primary result cannot count as completed coverage.
- Added a regression guard preventing reintroduction of the broken HTTPS host/port rewrite.

### Sprint 8 / Step 6 — Primary HTTPS transport compatibility hotfix 8
- Core web coverage no longer gives up after one HTTPS transport variant.
- Bounded compatibility ladder: canonical URL -> canonical URL without TLS keep-alive -> explicit TLS host/port with vhost.
- Connectivity-only output remains execution failure and is never published as a customer finding.
- Each retry deletes the previous structured report to prevent stale-result false positives.
- Primary CLI diagnostics stay private/internal; customer UI remains vendor-neutral.
- 3/3 Advanced fail-closed rule remains unchanged.
