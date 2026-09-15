# Sprint 6 — License / Entitlement Authority

## Architecture boundary

Sprint 6 is trust/entitlement only. SkullHarbor remains downloadable local software. Targets, scan execution, raw scanner output and normalized findings stay local and are not inputs to entitlement resolution.

## Step 1 — Entitlement State & Policy Resolution — DONE

Step 1 replaces the Sprint-4.1 temporary hard-coded FREE selection with a minimal trusted entitlement decision boundary.

### State model

The authority cache accepts only the internal states `active`, `trial`, `expired`, `no_seat` and `blocked`. Customer-safe resolution returns exactly `ACTIVE`, `TRIAL`, `EXPIRED`, `NO_SEAT` or `BLOCKED`. Unknown/malformed state, missing entitlement, an unapproved customer or an untrusted source fails closed to `BLOCKED`.

### Product mapping

- `TRIAL` always maps to the bounded FREE profile.
- `ACTIVE` maps to the authority-selected `free`, `monthly` or `annual` product.
- `annual` remains managed pentest only and is rejected by the existing self-service policy gate.
- Expired validity is resolved as `EXPIRED` even if the cached authority state still says active/trial.

### Enforcement order

For self-service scan creation the authorization chain is now:

`approved customer -> ACTIVE/TRIAL entitlement -> self-service product policy -> target parsing/public-IP check -> verified exact target -> local ScanEngine`

This deliberately checks trust/entitlement before target/DNS work. Entitlement never replaces exact-target authorization.

### Customer boundary

`GET /api/users/{user_id}/entitlement` is read-only. No customer endpoint can issue, activate, upgrade or mutate an entitlement. `ScanRequest` still contains only target and user identity; customers cannot supply product tier, scan profile, scanner controls, license state or authority state.

### Data minimization

The entitlement cache contains customer ID, product key, authority state, optional validity, authority source and update time. It contains no target, scan, finding, raw-output or DNS verification-token fields.

### Tests

`test_entitlement_authority.py` covers missing entitlement, customer-approval dependency, bounded trial mapping, active monthly mapping, expiry, no-seat, blocked, managed annual rejection, untrusted source rejection, customer request boundary and data minimization.

All previous 14 tests plus the Step-1 suite pass: **15/15 PASS**.

## Next — Step 2

Trusted issuance/lifecycle data for subscriptions, licenses, seats/installations and trial history. Do not move scan data into the authority boundary.

## Step 2 — Trusted Issuance / Seat & Installation Lifecycle — DONE

Step 2 adds the minimal trusted lifecycle behind the Step-1 entitlement resolver. It does not add a customer mutation API or a cloud scan path.

### Trusted issuance

Only `entitlement-admin` or `admin` actors from the exact `entitlement-authority` source may issue or change lifecycle state. Issuance requires an already approved Sprint-5 customer, a bounded authority-owned license identifier, a known product key and a seat limit from 1–100. Trial issuance is FREE-only and capped at seven days. Invalid/untrusted issuance fails before entitlement mutation.

### Seats and installations

An entitlement owns a small seat limit. Installation bindings use an opaque installation identifier and `active` / `released` lifecycle only. Binding is allowed only for ACTIVE/TRIAL entitlements and fails closed when no seat is available. Releasing a binding frees the seat. A license cannot be reissued with a seat limit below its current active installation count.

### Lifecycle / audit

The trusted authority can terminate local entitlement use through `blocked` or `expired`. Successful issuance, binding, release and terminal-state changes create minimal lifecycle audit rows. The audit contains actor/action/license/installation metadata only; targets, scans, findings, raw output and DNS verification secrets are excluded.

### Customer boundary

No POST/PUT/PATCH/DELETE customer entitlement endpoint exists. Customers retain only the Step-1 read-only entitlement view. The local scan path remains: approved customer -> valid entitlement -> product policy -> exact verified target -> local ScanEngine.

### Regression

`test_entitlement_lifecycle.py` covers trusted/untrusted issuance, approved-customer dependency, seat exhaustion, bind/release/rebind, idempotent-bind authorization, blocked lifecycle, seven-day trial issuance, lifecycle audit and data minimization.

## Step 3 — Signed Entitlement / Local Trust Verification

Step 3 closes the trust boundary between the future central SkullHarbor entitlement authority and the downloadable local application without moving scanning into the cloud.

### Signed grant

The authority can derive a minimal grant only for an already active installation binding. The signed payload contains only schema version, authority-owned license ID, product key, resolved ACTIVE/TRIAL state, opaque installation ID, seat limit and issuance/expiry timestamps. It explicitly contains no customer target, scan, finding, scanner raw output or DNS verification secret.

The wire payload is canonical JSON and is signed with Ed25519. The authority keeps the private signing key; the local SkullHarbor application needs only the public verification key. No shared signing secret is embedded in the downloadable scanner.

### Fail-closed local verification

Local verification requires a valid Ed25519 signature, exact schema/field set, supported self-service product/status, exact installation binding, bounded seat count and non-expired UTC validity. Wrong key, payload tampering, extra fields, wrong installation and expired grants are rejected. TRIAL grants always require an expiry.

A released installation cannot obtain a fresh signed payload from the trusted cache. ANNUAL remains managed-only and is intentionally not accepted as a local self-service signed grant.

### Tests

`test_signed_entitlement.py` covers valid signing/verification, payload minimization, payload tampering, wrong public key, installation mismatch, released binding, local expiry and rejection of extra/smuggled fields.

## Step 4 — Security Hardening & Sprint-6 Closeout — DONE

Step 4 closes Sprint 6 without adding product features or moving scanning into the trust service.

### Offline grant replay bound

A signed local entitlement is now a short-lived authorization grant rather than a copy of the full subscription lifetime. Fresh grants are valid for at most 24 hours and never beyond the authority-side entitlement expiry. This bounds use of a previously signed grant after a later authority-side block/release while preserving the local scan architecture. The authority still receives no target, scan, finding or scanner-output data.

### Fail-closed timestamp validation

The local verifier now requires both `issued_at` and `valid_until`, timezone-aware timestamps, a positive lifetime of at most 24 hours, and rejects grants issued more than five minutes in the future. Null, malformed, expired, future-dated and artificially extended grants fail closed even when correctly signed.

### Revocation semantics

Authority-side block/release prevents issuance of any fresh signed grant immediately. An already issued offline grant cannot be remotely erased from a disconnected local machine; its residual validity is therefore explicitly bounded to at most 24 hours. This limitation is documented rather than hidden behind a false immediate-revocation claim.

### Regression / closeout

`test_sprint6_security_closeout.py` covers the 24-hour lifetime cap, future-dated grants, malformed/null timestamps, data minimization and prevention of fresh issuance after authority blocking. The existing Step-3 signed-entitlement suite remains green.

**SPRINT 6 COMPLETE.**
