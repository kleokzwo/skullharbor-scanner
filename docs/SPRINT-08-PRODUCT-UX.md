# Sprint 8 — Product UX

## Step 1 — Dashboard Access & Readiness — DONE (pending target-machine confirmation)

The Sprint-8 roadmap starts with the mobile-first dashboard. Step 1 therefore turns the already-enforced Sprint 5–7 security state into one simple customer-facing readiness view before changing target onboarding, finding detail, filtering or managed-pentest flow.

### Customer experience

The dashboard now shows one compact **Access status** card with three understandable states:

- Customer verification
- SkullHarbor product access
- Authorized scope availability

It gives one next action and enables **Start Scan** only when the local UX summary says the customer has approved verification, usable ACTIVE/TRIAL self-service access, and at least one verified target or active engagement scope. If scope is the missing item, the customer is sent directly to Targets.

The header no longer hard-codes `FREE PLAN`; it presents the resolved SkullHarbor product when available. A single local customer profile is selected automatically; multiple development profiles remain explicitly selectable so the existing local test fixture remains usable.

### Security boundary

The readiness card is presentation only. `/api/scan` remains the authoritative enforcement point and still re-checks customer approval, entitlement/product policy, target parsing/public-IP rules and exact authorization. Disabling/enabling a button in the UI is never treated as security.

The new local `GET /api/users/{user_id}/product-status` endpoint composes existing local policy state. It returns customer-safe status/counts only and does not expose engagement hostnames, targets, scan IDs, findings, raw scanner output, scanner identity or DNS verification secrets. It does not introduce any cloud scan path.

### Scope deliberately not included in Step 1

- target onboarding redesign
- scan/finding detail redesign
- finding filters
- product comparison/upgrade flow
- managed-pentest contact flow
- global error-system redesign

Those remain later Sprint-8 steps.

### Regression

Added `backend/test_product_ux_step1.py` covering blocked verification, active product without scope, verified-target readiness, engagement-scope readiness, data minimization and frontend enforcement wording.

## Step 2 — Target Ownership Onboarding — DONE (pending target-machine confirmation)

Step 2 turns the existing DNS ownership gate into a guided SkullHarbor desktop-product flow without changing the Sprint-7 authorization model.

### Customer experience

- Reworked Targets into a modern **Verify ownership** experience.
- The page explains why ownership verification exists: SkullHarbor must not be used against systems the customer does not control.
- Onboarding is reduced to three visible steps: enter domain, add one DNS TXT record, verify.
- DNS host/value are presented as copyable fields with a single clear **Verify ownership** action.
- Verified targets get a direct **Start Quick Check** action.
- Pending/verified counts make the state understandable at a glance.
- Target rows are scoped in the UI to the selected local customer profile.
- The alternate legitimate Sprint-7 path is explained explicitly: customer-owned domains use ownership verification; customer systems covered by a trusted pentest engagement use the approved engagement authorization path.

### Security boundary

This is a UX redesign only. The backend remains authoritative. Target creation still canonicalizes the hostname, rejects non-public resolution, creates a cryptographically random per-target verification token and requires the matching SkullHarbor DNS TXT proof. Starting a scan still re-checks authorization independently of UI state.

No cloud scanning, scanner identity exposure, wildcard authorization or self-approval was introduced.

### Regression

Added `backend/test_product_ux_step2.py` covering the customer-facing ownership flow, preservation of the DNS proof boundary, selected-customer target scoping, engagement-path wording and scanner-name hiding.

## Step 2 closeout fix — verified-target handoff & visual polish

After local product-owner validation, Step 2 received a closeout correction before Step 3:

- A verified website no longer falsely promises that a scan can start when customer verification or product entitlement is missing.
- The verified-target action now continues to the Dashboard; the Dashboard presents the exact readiness prerequisites.
- The authoritative `/api/scan` customer, entitlement and scope gates are unchanged and remain fail-closed.
- DNS ownership verification remains mandatory for owned targets; approved engagement scope remains the separate Sprint-7 authorization path.
- Customer-facing shell branding was simplified to `SKULLHARBOR`; the repository/internal name is no longer shown in the product header.
- Dashboard visual language was upgraded toward a desktop-product experience: wider workspace, stronger hierarchy, readiness steps, local-execution indicator, and a simplified primary scan launcher.

Regression baseline remains 23 tests (the Step-2 regression was extended for this closeout fix).


### Step 2 Fix 2 — Preserve verified-target customer association

Fixed the remaining multi-profile UX regression: selecting or entering an already verified website now reuses the target's persisted local `user_id` association before readiness is resolved. A UI/version change therefore does not make an existing DNS ownership proof appear missing and does not require the customer to repeat DNS verification. The authoritative customer, entitlement and exact-target checks in `/api/scan` remain unchanged.

### Step 2 Fix 3 — Frontend initialization regression

- Fixed a React temporal-dead-zone crash introduced by Step 2 Fix 2.
- `active` scan state is now derived before the ownership-association effect references it.
- Added a regression assertion that preserves this initialization order.
- Existing ownership/customer association behavior and backend authorization gates are unchanged.

### Step 2 Fix 4 — legacy verified target migration

Pre-customer-bound ownership records (`verified` targets with no `user_id`) are now migrated locally without repeating DNS verification when ownership can be determined safely. Historical scan/customer provenance is preferred; a single local customer is the fallback. Ambiguous multi-customer data remains unassigned and fail-closed. No target, finding, scan or raw scanner data is sent to a central authority.

### Step 2 Fix 5 — real upgrade-path ownership binding

Fix 4 handled only the single-local-customer fallback and therefore did not cover a real upgraded development database containing several historical customer rows. Fix 5 resolves that gap without weakening authorization: for a pre-scoping `verified` target with `user_id=NULL`, SkullHarbor now prefers (1) one historical scan owner, (2) one exact company-domain match, (3) exactly one already-approved customer that already has usable ACTIVE/TRIAL self-service entitlement, then (4) the legacy single-user fallback. Any ambiguity remains unassigned and fail-closed.

A new integration regression recreates the upgrade case with multiple local profiles, one approved/entitled customer and an already-verified `skullharbor.org`. It asserts migration, product readiness and the authoritative exact-target authorization resolver end-to-end. No DNS proof is repeated and no approval or entitlement is created by the migration.

### Step 2 Fix 6 — runtime truth split removed

Product-owner runtime validation showed the actual upgraded local database can contain verified pre-Sprint-5 targets/scans but no customer record at all. Previous fixes incorrectly treated this as a target/customer-binding problem. Fix 6 separates the three facts correctly: DNS ownership is reported from the verified local target even when no customer profile exists; customer approval and entitlement remain separate fail-closed gates.

A new local `GET /api/product-readiness` composition endpoint is target-aware and never asks for a second DNS proof when the exact local target is already verified. The Dashboard now says `Website verified` and marks `Authorized website` ready for that case instead of the false `Verify ownership` state. It does not invent an approved customer or entitlement: if those records do not exist, scanning remains blocked and the next action explicitly says customer/product setup is required.

This closes the misleading ownership UX regression. Customer onboarding/activation still has to use the trusted Sprint-5/6 authority model; it must not be implemented as local self-approval merely to enable the button.

Regression baseline: 25 tests, including `test_product_ux_runtime_context.py`.

### Step 2 Fix 7 — remove the dead-end setup state

Runtime validation established that the upgraded development database contains a valid legacy DNS ownership proof but no Sprint-5 customer/entitlement records. That is not safely repairable by inventing approval or licensing locally. Fix 7 therefore removes the customer-facing dead end without weakening the security model: the Dashboard now routes missing identity to an in-product **Verify your organization** flow that creates the pending customer record and submits company data using the existing Sprint-5 public APIs. Pending state is explicit and the UI states that trusted SkullHarbor review is required. Product activation is shown as a separate trusted step and is never generated by the desktop app.

This preserves the hard rule that customers cannot self-approve or self-issue entitlements. A verified website remains verified and does not need another DNS proof. Scan remains fail-closed until trusted customer approval and ACTIVE/TRIAL product access exist.

### Step 2 Fix 8 — development activation closeout

Runtime testing proved that the upgraded development database can legitimately contain a verified legacy target while Sprint-5 customer approval and Sprint-6 entitlement do not yet exist. Those states cannot be invented by the customer UI. To make the development build testable end-to-end without weakening the production boundary, Fix 8 adds an explicitly isolated **development-only trusted authority bridge**. It is loaded only when the repository marker `.skullharbor-development` exists and must be omitted from production packaging.

The development bridge does not add customer mutation endpoints. It invokes the existing trusted Sprint-5 review primitive with an admin reviewer context and the existing Sprint-6 entitlement primitive with an entitlement-authority context, issuing only a bounded seven-day FREE trial. The customer-facing `/api/users` and entitlement APIs remain unable to self-approve or self-issue access.

The organization-verification screen exposes this bridge only in development builds as `Trusted test authority`, so the product owner can complete the real end-to-end Quick Check flow without Python/SQL/manual database edits. Production builds must have no marker, no development authority route registration and no test-authority UI.

### Step 2 Fix 9 — graceful Quick Check execution budget

Target-machine validation after the authorization closeout exposed a separate runtime failure: the FREE Quick Check primary web check was being terminated by the generic 300-second process watchdog. Because termination was abrupt, structured output could be lost and the primary-only FREE profile then had zero successful checks, causing the whole scan to fail after exactly five minutes.

Fix 9 gives the internal primary engine its own graceful per-host runtime cap before the process watchdog: FREE is capped at 90 seconds and MONTHLY at 180 seconds. The outer watchdog remains a private kill-switch with an additional 20-second grace period. This allows the engine to finish and flush structured JSON normally instead of being killed at the old five-minute boundary. Cancellation remains immediate and fail-safe. No customer-controlled timeout, scanner option or tool identity is exposed.

Added `test_quick_check_runtime_budget.py` to assert the bounded FREE policy and preservation of normalized findings after graceful completion. Regression baseline: 28 tests.


### Product policy refinement — paid security depth

Product-owner review refined the server-owned MONTHLY depth while preserving the self-service safety boundary:

- FREE remains the deliberately small baseline: primary categories `1,2`.
- MONTHLY primary depth is now `1,2,3,4,9,b`, adding the SQL-injection category (`9`) to the paid Advanced Check.
- DoS category `6` remains prohibited in all customer self-service profiles. Availability/stress testing is reserved for explicitly scoped managed engagements and is never implied by a MONTHLY entitlement.
- The MONTHLY secondary template-driven web checks remain controlled: DoS, intrusive, fuzzing and brute-force classes are excluded; execution remains rate/concurrency bounded by server-owned policy.
- The MONTHLY bounded surface-discovery slot remains part of Advanced Check for public web-service exposure.
- ANNUAL remains a managed pentest engagement rather than an unrestricted automated tier. More invasive testing, including any explicitly authorized availability or authentication-resistance work, must be separately scoped and coordinated.
- Customer-facing tier/marketing copy must describe outcomes (misconfiguration, information disclosure, injection/XSS, SQL-injection, software exposure, known web-security issues and bounded public service exposure) without exposing scanner brands, tuning codes, CLI flags or adapter names.

This is a policy-depth refinement only. Customers still cannot select scanners, tuning categories, ports or raw arguments.
