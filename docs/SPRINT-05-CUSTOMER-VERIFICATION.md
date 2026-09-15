# Sprint 5 — Customer / Company Verification

## Architecture rule: downloadable/local product

SkullHarbor UI-Scanner is distributed software. Scans execute on the customer's machine; this sprint does **not** turn the scanner into a cloud scanning service and does not upload targets/findings to SkullHarbor.

Because local software can be modified by its owner, a local SQLite flag alone is not a cryptographic trust boundary. Sprint 5 models and enforces the product workflow locally. A later trusted approval/license mechanism can provide signed/validated entitlement state without moving scan execution or customer findings into the cloud.

## Step 1 — Verification State & Enforcement — DONE

- Added customer states: `pending`, `approved`, `rejected`, `suspended`.
- New registrations always start `pending`.
- Self-service scan creation now requires an explicit user and `approved` customer state.
- Anonymous, pending, rejected and suspended customers fail closed before target authorization and scan creation.
- No customer request field can set approval state.
- No public approve/reject/suspend mutation endpoint exists in Step 1.
- Existing exact-host DNS authorization remains a separate mandatory gate.
- Product entitlement remains FREE until Sprint 6.

### Current authorization chain

`approved customer -> verified exact target -> server-owned FREE policy -> local ScanEngine`

### Important limitation

Step 1 is workflow enforcement, not anti-tamper DRM. The authoritative/signed approval mechanism belongs with the later license/entitlement design. Scan execution remains local.

## Next — Step 2

Add company verification data required for review while minimizing stored personal/company data. Customer-supplied company data must never be able to set or imply approval.

## Step 2 — Minimal Company Verification Data — DONE

The downloadable/local architecture remains unchanged. Step 2 adds only a small local review payload to the customer record:

- `company_name`
- `company_domain`
- `intended_use`
- `company_profile_submitted_at`

### Security boundary

- `CompanyProfileRequest` contains no approval, tier, license, scanner or scan-profile field.
- Updating company data never changes `verification_status`.
- Existing `rejected` or `suspended` decisions remain unchanged when profile data is edited.
- `company_domain` is normalized as an identity/review field only; it does **not** prove ownership and does not authorize scanning.
- Exact scan authorization remains the separate DNS-TXT target-verification gate.
- Company profile submission does not call target resolution or scan authorization logic.
- No scan targets, findings or raw scanner output are uploaded by this workflow.

### API

`PUT /api/users/{user_id}/company-profile`

This is a local profile-editing workflow, not an approval endpoint. In the commercial design, trusted approval remains separate from customer-editable data.

### Tests

`test_company_profile.py` verifies data normalization, persistence, pending-state preservation, suspended-state preservation, and absence of protected authorization fields from the request model.

## Step 3 — Trusted/Admin Review — DONE

Step 3 adds a deliberately internal trusted review boundary. It does **not** add a customer-facing approve/reject/suspend endpoint.

### Review policy

- Trusted roles are explicitly limited to `trusted-reviewer` and `admin`.
- Review source is explicitly limited to the internal `trusted-admin` boundary.
- Decisions are limited to `approved`, `rejected` and `suspended`.
- Allowed transitions are explicit and fail closed:
  - `pending -> approved | rejected`
  - `approved -> suspended`
  - `rejected -> approved` after remediation/re-review
  - `suspended -> approved | rejected`
- Same-state and all other transitions are rejected.
- Approval requires the Step-2 company review payload to be complete.
- Rejection requires a non-empty controlled reason.
- Existing scan enforcement still requires `approved`, so rejection/suspension immediately keeps self-service scans blocked.

### Audit boundary

Each successful decision creates a `verification_review_audit` row containing only:

- customer ID
- reviewer/actor ID and trusted role
- trusted source
- previous and resulting verification state
- optional review reason
- review timestamp

The audit schema intentionally contains no target, scan, finding, raw-output or DNS verification-token data.

### Local/downloadable trust limitation

`_apply_trusted_review` is an internal policy boundary, not a claim that a locally modifiable Python/SQLite installation can authenticate SkullHarbor administrators cryptographically. No public admin mutation API was added. A later signed/remote trust or entitlement adapter may feed this boundary while still receiving **no** scan targets, raw scanner data or findings.

### Tests

`test_trusted_admin_review.py` covers incomplete-profile approval denial, unauthorized actor/source denial, positive approval, invalid transitions, suspension enforcement, mandatory rejection reason, re-review approval, audit history and absence of customer-facing decision endpoints.

All previous 12 regression/policy tests plus the new Step-3 test pass: **13/13 PASS**.

## Next — Step 4

Security tests and Sprint-5 closeout. Do not start Step 4 until explicitly requested.

## Step 4 — Security Tests & Sprint-5 Closeout — DONE

Step 4 closes Sprint 5 without adding a new product feature. The review/verification boundary was exercised as a complete authorization chain and two small fail-closed hardenings were applied where the closeout tests identified useful boundary improvements.

### Security hardening

- Customer-facing Pydantic request models now use `extra="forbid"`. Attempts to inject protected fields such as `verification_status`, reviewer authority, scan tier/profile or other unknown controls are rejected instead of silently ignored.
- The approved-customer gate now runs before target URL parsing and DNS resolution in `/api/scan`. Pending/rejected/suspended/anonymous callers therefore stop at the customer authorization boundary before protected target-validation work begins.
- Trusted reviewer identifiers are bounded to the persisted audit schema length before a decision can be committed.
- Failed review attempts leave both customer state and review-audit history unchanged.

### Closeout regression coverage

`test_sprint5_security_closeout.py` verifies:

- fail-closed rejection of protected/unknown customer request fields;
- approval enforcement before target parsing/DNS work;
- incomplete-profile approval denial;
- mandatory rejection reason and invalid-decision denial;
- no audit row/state mutation after failed decisions;
- bounded reviewer identity;
- successful trusted approval and resulting scan eligibility;
- absence of target/scan/finding/raw-output/DNS-token fields from the review audit schema.

All previous tests plus the Step-4 closeout suite pass: **14/14 PASS**.

### Sprint 5 final authorization chain

`trusted review approval -> approved customer -> verified exact target -> server-owned FREE policy -> local ScanEngine`

The chain remains local for scan execution. The review workflow contains no targets, raw scan output or findings. A local SQLite/Python installation is still not treated as a cryptographic trust authority; signed/authoritative entitlement remains Sprint 6 and must preserve this local-scan boundary.

## Sprint 5 — COMPLETE

Definition of Done is satisfied:

- customer verification states and scan gate are enforced;
- minimal company verification data exists and cannot self-approve;
- trusted/admin decisions use explicit roles, transitions and audit records;
- negative and positive security paths are regression tested;
- customer requests fail closed on protected-field injection;
- protected scanning remains dependent on successful review and exact-target authorization;
- scan targets, raw data and findings remain outside the trust/review process;
- all 14 backend regression/policy/security tests pass.

**Next sprint:** Sprint 6 — License / Entitlement Authority. Do not start it as part of Sprint 5 closeout.
