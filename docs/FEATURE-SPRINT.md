# SkullHarbor — Feature Sprint Plan

This file is the working product-feature sequence. Development follows these steps in order; do not skip ahead unless a blocking defect must be fixed first.

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
