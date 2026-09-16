# Sprint 7 — Scope / Engagement Authorization

## Architecture boundary

SkullHarbor remains downloadable local software. Engagement authorization is trust/scope metadata only. Targets are represented only as the exact hostnames explicitly authorized for an engagement; scan execution, findings, raw scanner output and DNS verification secrets remain local and are not part of engagement review/audit data.

## Step 1 — Trusted Engagement Scope Foundation — DONE

Step 1 introduces the second legal authorization path required by the roadmap: an approved professional engagement can authorize an exact hostname without pretending that the pentester owns the customer's DNS zone. The existing DNS-TXT ownership path remains unchanged.

### Trust boundary

Only `engagement-reviewer` or `admin` actors from the exact `engagement-authority` source may approve or terminate an engagement. The subject user must already be an approved Sprint-5 customer. No customer-facing POST/PUT/PATCH/DELETE engagement endpoint exists. Customers can only read their engagement records.

### Exact-host scope

An engagement contains 1–100 normalized exact hostnames. Scope does not inherit to parent domains, sibling hosts or subdomains. Wildcard syntax is rejected by the existing strict domain parser. Duplicate hostnames fail closed.

### Lifecycle

An engagement has an authority-owned reference, customer name, approved user, explicit validity window and `approved`, `revoked` or `expired` state. Authorization requires `approved` plus a currently active validity window. `revoked` and `expired` are terminal in Step 1. Validity is bounded to at most 366 days.

### Scan gate integration

The local scan creation path now requires either:

`verified exact-host ownership OR approved exact-host engagement scope`

This is still downstream of the existing customer approval and entitlement gates. An engagement cannot bypass Sprint 5 customer approval or Sprint 6 entitlement/product policy.

### Data minimization

Engagement trust/audit storage contains no scan records, findings, raw output, DNS verification tokens or scanner controls. Audit records contain only the engagement reference, actor, action and bounded metadata.

### Tests

`test_engagement_authorization.py` covers untrusted self-approval, customer approval dependency, exact-host matching, out-of-scope denial, revocation, expiry, terminal transitions, read-only customer boundary and data minimization.

## Next — Step 2

Continue the engagement lifecycle/authorization hardening only after Step 1 is confirmed on the target machine. Do not begin Product UX or release work here.

## Step 2 — Authorization Hardening & Local Provenance — DONE

Step 2 hardens the Step-1 engagement path without adding a second authorization architecture.

### Defense in depth

The engagement lookup now independently requires the subject customer to remain Sprint-5 `approved`. Suspension/rejection therefore invalidates direct engagement authorization even if a caller reaches the helper outside the normal scan route. Hostnames are canonicalized again at the authorization boundary and malformed values fail closed.

### Local authorization provenance

A locally created scan can now retain the `engagement_id` that authorized it when DNS ownership was not the authorization path. This is local provenance only: engagement authority/audit storage is not given a scan ID, target payload, finding, raw output or scanner data. Verified ownership continues to use `target_id`.

The scan-create response reports only the customer-safe authorization mode (`verified-ownership` or `approved-engagement`) and, for the engagement path, its authority reference.

### Lifecycle safety

Invalid lifecycle transitions remain non-mutating and do not create audit decisions. Revoked/expired engagements remain terminal as defined in Step 1.

### Tests

`test_engagement_hardening.py` covers canonical exact-host matching, malformed-host denial, customer suspension invalidation, non-mutating invalid transitions, local engagement provenance and authority-audit minimization.

## Next — Step 3

Continue Sprint 7 only after Step 2 is confirmed on the target machine. Do not begin Sprint 8 Product UX here.

## Step 3 — Security Closeout — DONE

Step 3 closes Sprint 7 without adding product UX or Sprint-8 features.

### Single authorization decision

The scan route now resolves verified ownership versus approved engagement scope through one local policy decision. This removes the previous split engagement check and ensures the exact engagement that authorizes a scan is the engagement retained as local provenance. Verified ownership takes precedence when both authorization paths exist.

### Boundary hardening

Cross-customer engagement reuse fails closed. Revoked, expired, malformed, out-of-scope or customer-invalid engagement authorization remains denied. Engagement authority audit storage continues to contain trust/scope metadata only and receives no scan IDs, findings, raw output, scanner data or DNS verification secrets.

### Tests

`test_sprint7_security_closeout.py` covers cross-customer isolation, single-decision provenance, verified-ownership precedence, revocation denial and authority-audit minimization.

**SPRINT 7 COMPLETE.**
