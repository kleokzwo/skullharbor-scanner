# Sprint 03 Closeout — Finding Engine

Release: **v0.3.1**

## Closed bugs

### S3-BUG-01 — Valid scanner evidence became `Web security observation`

Cause:
The adapter assumed a small number of top-level JSON shapes. When structured
output was nested differently, the real finding text was not reached and the
generic fallback was stored instead.

Fix:
- recursive discovery of finding-like records
- support for multiple message fields
- preserve request/path plus the real source message as evidence
- conservative fallback only when no textual evidence exists
- regression fixtures for list, nested-object, and standard finding shapes

## Sprint 3 acceptance state

- unified customer-facing engine identity
- normalized finding schema
- initial SkullHarbor knowledge rules
- unknown findings remain INFO/unclassified
- concrete scanner vendor is not shown in the normal customer UI
- target authorization from Sprint 2 remains enforced
- normalizer regression tests pass

## Deferred

UI/UX polish remains intentionally deferred until the core product flow is
complete.
