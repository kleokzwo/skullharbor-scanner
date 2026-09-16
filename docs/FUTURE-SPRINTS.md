# Roadmap after Sprint 4

## Sprint 4 — Scan Engine & Multi-Adapter Orchestration

Central ScanEngine and multi-adapter orchestration behind the authorized SkullHarbor Quick Check workflow.

**Status:** DONE in v0.4.0.

**DONE because:** authorized scans can orchestrate enabled internal adapters, normalize/deduplicate findings, isolate adapter failures, enforce execution budgets/cancellation, and return customer-safe results without exposing concrete scanner branding.

## Sprint 4.1 — Scan Profiles & Product Tiers

**Status:** DONE in v0.4.1.

Define the server-side scan policies that use the Sprint 4 engine. Customers select a SkullHarbor product/check level; they never select or configure concrete scanner tools.

### FREE — SkullHarbor Quick Check

- Limited automated security check.
- Internal Nikto policy uses only tuning categories 1 and 2 by default.
- Additional internal adapters may run only in a deliberately limited/safe configuration.
- No customer-controlled raw scanner arguments or tuning switches.

### MONTHLY — SkullHarbor Advanced Check

- Broader automated check using the same ScanEngine.
- Internal primary web policy uses six controlled categories (`1,2,3,4,9,b`), including SQL-injection checks; DoS category `6` remains excluded.
- Do not expose Nikto DoS tuning category 6 in customer self-service scans.
- Additional internal adapters can be enabled with server-owned safe profiles.
- The customer still sees only SkullHarbor findings/results, not underlying scanner names.

### ANNUAL — Managed Pentest

- Annual is not an unrestricted automated scanner tier.
- Customer contacts hello@skullharbor.org.
- Includes two manually coordinated pentests per year.
- Scope, timing and authorization are handled as an engagement rather than by exposing stronger scanner controls.

### Architecture rule

Implement FREE, MONTHLY and ANNUAL now as product/scan-profile policy. Do not implement payment, subscription lifecycle, seats or real license validation here; those remain Sprint 6 responsibilities.

**DONE:** ScanEngine selects server-owned tier policies; FREE and MONTHLY have measurably different bounded depth; ANNUAL is blocked from self-service execution; customers cannot select internal scanners or unsafe tuning; tier orchestration and customer-boundary regressions pass.

## Sprint 5 — Customer / Company Verification

**Status:** COMPLETE — Steps 1–4 DONE; 14/14 backend regression/policy/security tests pass.

The product remains downloadable/local: customer scans and findings execute locally and are not moved to a SkullHarbor cloud scanner. Registration does not automatically grant commercial scanner access. Add customer/company approval state and abuse controls.

Product tier alone must never authorize arbitrary targets. Customer/company approval is a separate prerequisite for commercial scanner eligibility.

Step 2 adds a minimal local company review payload (company name/domain/intended authorized use). Customer-editable company data cannot mutate approval state and company identity never substitutes for exact-host DNS authorization.

**DONE when:** only approved customers are eligible for trial/subscription access, approval state is enforced by the product authorization path, and the downloadable/local scan architecture remains intact. Local cached state alone is not considered anti-tamper security.

## Sprint 6 — License / Entitlement Authority

**Status:** COMPLETE — Steps 1–4 DONE; Sprint-6 security closeout confirmed.

Central products, subscriptions, licenses, seats, installations and trial history. This is an entitlement/activation service, not a cloud scanner: scan targets, raw results and findings remain local.

Connect the product tiers defined in Sprint 4.1 to real entitlement state. Billing/subscription state must not bypass customer approval or target/scope authorization.

**DONE when:** API can reliably return ACTIVE, TRIAL, EXPIRED, NO_SEAT or BLOCKED and map valid entitlements to the correct server-owned scan profile.

## Sprint 7 — Scope / Engagement Authorization

**Status:** COMPLETE — Steps 1–3 DONE; Sprint-7 security closeout confirmed.

Extend the exact-host ownership model with a separate authorized-engagement workflow for professional pentesters and customer-approved third-party scopes.

This also provides the authorization model needed for manually coordinated ANNUAL pentest engagements.

**DONE when:** scanner access always requires either verified ownership or an approved engagement scope.

## Sprint 8 — Product UX

Return to the visual design after core security/functionality is stable. Finalize mobile-first dashboard, target onboarding, scan/finding detail, filtering, product-tier presentation, managed-pentest contact flow and robust errors.

**DONE when:** a customer can understand their SkullHarbor product, verify/onboard targets and use the permitted scanner workflow safely without terminal knowledge.

## Sprint 9 — Release & Security Hardening

Packaging/download, worker isolation, rate limits, secure token handling, production TLS/configuration, audit logging, legal/privacy review and release testing.

Include final abuse-case testing across account approval, entitlements, target authorization and scan-profile enforcement.

**DONE when:** distributable commercial release candidate is ready.
