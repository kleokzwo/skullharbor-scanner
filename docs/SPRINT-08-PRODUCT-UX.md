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

## Step 3 — Scan & Finding Experience — DONE (pending target-machine confirmation)

Step 3 turns the working scan lifecycle and normalized findings into a customer-first desktop experience. It does not change authorization, entitlement, scan-profile or adapter policy.

### Customer experience

- Active checks show a calm SkullHarbor progress card with customer-safe stages such as **Confirming authorization**, **Checking website**, **Reviewing results** and **Saving results**.
- The customer-facing **Technical scan log** was removed. Internal engine logs remain available to engineering in the local runtime, but are not part of the normal product surface.
- Completed scans now lead with an outcome-oriented summary: important issues, findings to review, or no findings in this Quick Check.
- A zero-finding result explicitly says it is not a guarantee that the website has no vulnerabilities.
- Finding detail keeps the three plain-language questions: **What did we find?**, **Why does this matter?**, and **What should I do?**
- Normalized evidence remains available under **Evidence & details**, while raw-adapter wording/output and internal rule identifiers are removed from the normal customer UI.
- The unfinished false-positive placeholder action was removed rather than shipping a dead control.
- Customer-visible result metadata uses SkullHarbor product names only; no internal engine/tool name is presented.

### Security boundary

Step 3 is presentation only. `/api/scan`, entitlement resolution, exact target/engagement authorization, execution budgets, normalization and local persistence are unchanged. No scan data is moved to a cloud service and no customer-controlled scanner options are introduced.

### Regression

Added `backend/test_product_ux_step3.py` to lock the customer-safe progress/result/finding language, removal of the technical-log/raw-output surface, and preservation of backend authorization enforcement.

## Step 4 — Product UX Closeout & Tier Validation — IMPLEMENTED (pending target-machine confirmation)

Step 4 adds a development-only way to exercise both customer self-service tiers end-to-end before Sprint 8 is closed.

### Development tier validation

The isolated Trusted Test Authority now exposes two explicit development choices for an already completed organization profile:

- **FREE test access** — issues the real bounded FREE trial (maximum seven days) and therefore resolves to the FREE scan profile.
- **MONTHLY test access** — issues a 30-day ACTIVE development entitlement and therefore resolves to the MONTHLY / Advanced Security Check profile.

Switching the development entitlement uses the same trusted review and entitlement issuance primitives as Sprint 5/6. It does not modify `/api/scan`, target authorization, scan policy resolution, or scanner arguments in the customer UI. The development bridge accepts only `free` or `monthly`; ANNUAL remains managed-only.

The `.skullharbor-development` marker remains the load boundary for this test authority. Production packaging must omit the marker and development authority module/control. A customer production build must never be able to self-approve or self-upgrade.

### Tier policy validated by this step

- FREE resolves to the bounded Quick Check policy.
- MONTHLY resolves to the Advanced Security Check policy, including the documented paid depth (`1,2,3,4,9,b`) and controlled additional checks.
- DoS category `6`, brute force, uncontrolled fuzzing and other disruptive self-service behavior remain excluded.
- Customer-facing UI shows SkullHarbor product names only; internal scanner names/tuning codes remain implementation details.

### Regression

Added `backend/test_product_ux_step4.py` covering trusted MONTHLY issuance, actual `monthly` profile resolution, switching back to bounded FREE trial, development endpoint allowlisting, and presence of both test controls in the development UI.

### Step 4 follow-up — reachable development tier switch
- Development FREE/MONTHLY switching is available from **Settings → Test product access**, including when the dashboard is already fully ready.
- The dashboard remains customer-focused; development authority controls do not occupy the normal Quick Check flow.
- The Settings switch is development-only and must be omitted from production packaging together with `.skullharbor-development` / `dev_authority.py`.

## Step 4 — Single-Customer Trial & Upgrade Lifecycle — IN PROGRESS

### Product decision

SkullHarbor has one durable customer/company identity. FREE, Advanced and future managed/custom offerings are product access states for that same customer; they are not separate customer profiles.

The customer must never re-enter company name, work email, company domain, intended use or repeat DNS ownership verification merely because the product tier changes. Existing verified targets and valid engagement authorization remain attached to the same customer and keep their own lifecycle.

### Target lifecycle

1. Company registration and trusted customer verification happen once.
2. An approved customer receives a bounded SkullHarbor FREE trial (maximum 7 days).
3. During the trial the customer can run the FREE Quick Check against authorized scope.
4. If the trial expires without paid access, new scans are blocked by entitlement policy. Existing local scans and findings remain locally readable.
5. FREE -> SkullHarbor Advanced changes the entitlement for the existing customer only. It does not create a second customer/company record and does not repeat ownership verification.
6. Advanced uses the MONTHLY self-service policy. Custom/yearly remains a separately scoped managed pentest engagement, not an unrestricted automated tier.

### Step-4 UX implemented in this iteration

- Removed the customer/profile selector from the Quick Check readiness panel. Plan selection is no longer modeled as profile selection.
- Settings is now **Account & plan** and shows the durable organization identity separately from product access.
- FREE customers get a single **Upgrade to Advanced** action. In development this uses the trusted test authority against the same customer record; production checkout is deliberately not invented in Sprint 8.
- Advanced clearly reports that organization verification and authorized websites are preserved.
- Custom/yearly is presented as a managed pentest engagement.
- Development FREE/MONTHLY simulation remains available only under a collapsed internal testing section and remains excluded from production packaging.

### Security invariants

- Customer approval is never created by the customer-facing upgrade UX.
- Product access is still issued only through the trusted entitlement authority.
- `/api/scan` remains authoritative and fail-closed for verification, entitlement and exact scope authorization.
- Trial remains FREE-only and <= 7 days.
- Upgrade does not modify target verification tokens, verified timestamps, target ownership, engagement scope, scan data or findings.
- Targets/findings/raw scanner data remain local and are never sent to the central authority.

### Deferred intentionally

Payment provider integration, checkout, contract acceptance/versioning, cancellation, renewal, invoices and final withdrawal/cancellation wording are a later dedicated commercial/legal sprint. Sprint 8 establishes the product lifecycle and UX boundary only.

### Regression

Added `test_product_ux_single_customer_upgrade.py` and `test_product_ux_step4_single_account_ui.py`. They assert that FREE -> MONTHLY mutates the existing entitlement without recreating customer identity or DNS ownership proof, and that the customer-facing dashboard no longer presents plan changes as customer-profile selection.

### Step 4 hardening — account/plan state truthfulness

Step 4 now keeps the Settings surface aligned with authoritative local state: pending or missing organization data is no longer labelled as verified, and an expired/blocked Advanced entitlement is no longer described as active. Inactive access remains fail-closed for new scans while the existing local customer identity, verified targets and authorization records remain untouched. The Free plan comparison is marked current only when the resolved product key is actually `free`.

### Step 6 — Advanced secondary QuickCheck runtime closeout (Hotfix 11)
- Replaced broad upstream tag selection with a version-controlled local allow-list.
- Root cause confirmed on Kali/Nuclei v3.11.1: broad tags loaded 3,650 templates and planned 7,796 requests for one target (~4m runtime).
- Advanced secondary now runs six safe, GET-only HTTP exposure/misconfiguration templates shipped with SkullHarbor.
- No customer-controlled template paths/flags; no automatic scan, headless, code, network, DoS, fuzz or brute-force templates.
- Advanced remains fail-closed: all three promised coverage families must complete before results are published.


### Step 6 final closeout — truthful external-service surface
- Independent bounded Nmap reference: 10 open additional services produced exactly 10 SkullHarbor observations; 17 filtered ports produced none.
- Public Service Exposure excludes website ports 80/443 from probing and customer results.
- Fixed allow-list focuses on FTP, SSH, Telnet, mail, RPC, LDAP, SMB, NFS, Docker API, MySQL, RDP, PostgreSQL, VNC, Redis, Elasticsearch, Memcached and MongoDB.
- Only state `open` becomes an observation; closed, filtered and out-of-policy ports are suppressed.
- Open services are observations, not automatically vulnerabilities. Detail view explains evidence, relevance and remediation.
- Dashboard distinguishes security findings from verified external-service observations.
