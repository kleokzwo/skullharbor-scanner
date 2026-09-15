# Sprint 4.1 — Scan Profiles & Product Tiers

## Step 1 — Server-owned policy

Status: **DONE**

Sprint 4.1 separates customer products from concrete backend scanner configuration.
The customer API does not accept scanner names, CLI flags, tuning values, or a requested tier.
Until Sprint 6 connects authenticated license entitlements, self-service `/api/scan` resolves
server-side to the FREE policy.

### Product policies

- **FREE / SkullHarbor Quick Check** — self-service; deliberately limited scan depth; primary internal web check only; primary tuning categories 1 and 2.
- **MONTHLY / SkullHarbor Advanced Check** — self-service once entitlement exists; primary + secondary internal checks; controlled primary tuning `1,2,3,4,b`; DoS tuning category 6 is excluded.
- **ANNUAL / SkullHarbor Managed Pentest** — not executable as a self-service scan; contact `hello@skullharbor.org`; two manually coordinated pentests per year.

Concrete scanner names remain backend implementation details and are not present in the public product catalog.

### Security boundary

`ScanProfile` is backend-owned. A request cannot upgrade FREE to MONTHLY by adding a request parameter because `ScanRequest` contains no profile/tier/scanner/tuning fields. Sprint 6 will replace the temporary server-side FREE entitlement resolution with authenticated license state.

### Verification

- Existing Sprint 3/4 regression tests: PASS
- State transition tests: PASS
- Customer boundary tests: PASS
- New scan profile policy tests: PASS
- Python compile check: PASS
- Frontend build: not revalidated in build sandbox; uploaded `node_modules` was incomplete and dependency reinstall exceeded the sandbox execution window. No frontend source changes were required for Step 1.

## Next

Step 2 should connect product-safe presentation/selection semantics without trusting a customer-supplied tier. Real entitlement resolution remains Sprint 6.
