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


## Step 2 — Controlled multi-tool profile depth

Status: **DONE**

The original internal tool set is now represented behind the private ScanEngine adapter boundary: primary web checks, additional template-driven web checks, and bounded web-surface discovery. Concrete tool names remain third-party/backend implementation details and are not product controls.

### FREE

- Primary web check only.
- Tuning categories 1 and 2.
- No surface-discovery adapter.

### MONTHLY

- Controlled primary web check with five approved tuning categories (`1,2,3,4,b`); DoS category 6 remains excluded.
- Additional bounded web-security checks with intrusive/DoS/fuzz/bruteforce classes excluded.
- Bounded TCP web-surface discovery on the fixed server-owned port set 80, 443, 8080 and 8443.
- Surface discovery uses connect scanning only; no scripts, UDP scan, OS detection, version detection or customer-controlled port range.
- Alternate reachable web ports (8080/8443) are normalized as informational Attack Surface findings. Standard 80/443 are expected and are not reported as findings merely for being open.

### ANNUAL

Unchanged: managed engagement only, two coordinated pentests per year via `hello@skullharbor.org`; no unrestricted self-service scanner tier.

### Verification

- Existing regression suite: PASS
- Scan-profile policy: PASS
- Customer boundary: PASS, including all current internal tool names
- New bounded surface-adapter policy/normalization test: PASS
- Python compile check: PASS

## Next

Step 3 should close Sprint 4.1 by testing the complete FREE-vs-MONTHLY orchestration policy as a unit and documenting the final tier matrix. Real entitlement selection remains Sprint 6.

## Step 3 — Tier orchestration closeout

Status: **DONE**

Sprint 4.1 is closed with an end-to-end policy regression that verifies the ScanEngine selects execution depth from the server-owned product policy rather than from customer input.

### Final tier matrix

| Product | Delivery | Automated depth | Customer-controlled scanner/flags |
| --- | --- | --- | --- |
| SkullHarbor Quick Check / FREE | Self-service | Primary bounded web check; categories 1 and 2 | No |
| SkullHarbor Advanced Check / MONTHLY | Self-service after trusted entitlement exists | Primary expanded bounded web check + additional bounded web checks + fixed web-surface discovery | No |
| SkullHarbor Managed Pentest / ANNUAL | Managed engagement | No unrestricted self-service execution; two coordinated pentests/year | No |

The MONTHLY primary policy remains limited to the five approved categories `1,2,3,4,b`; DoS category 6 remains excluded. Web-surface discovery remains fixed to TCP 80/443/8080/8443 and cannot be widened by the customer.

### Closeout security assertions

- FREE executes only the FREE adapter slot set.
- MONTHLY executes exactly the controlled MONTHLY adapter slot set and order.
- ANNUAL fails closed if someone attempts to route it through the self-service ScanEngine.
- `/api/scan` still resolves to FREE server-side until Sprint 6 provides a trusted entitlement source.
- `ScanRequest` still has no tier/profile/scanner/tuning/flags/raw-argument controls.
- Public product metadata remains SkullHarbor-only and contains no internal tool or tuning implementation details.
- Company approval and target authorization remain independent gates; a future paid entitlement must never bypass them.

### Verification

- Full backend regression suite: PASS
- New `test_tier_orchestration.py`: PASS
- Python compile check: PASS
- Local user verification for Step 2 before closeout: 9/9 PASS

## Sprint 4.1 result

**SPRINT 4.1 COMPLETE.** Product depth is now a server-owned policy boundary. Billing/license lifecycle is intentionally not implemented here and remains Sprint 6. The next development sprint is Sprint 5 — Customer / Company Verification.
