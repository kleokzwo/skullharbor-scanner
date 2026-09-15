# Sprint 4 — Scan Engine & Orchestration

**Baseline:** v0.3.2  
**Target build:** v0.4.0  
**Step 1:** COMPLETE  
**Step 2:** COMPLETE
**Step 3:** COMPLETE
**Step 4:** COMPLETE
**Step 5:** COMPLETE
**Sprint status:** DONE

## Goal

Move scan lifecycle/orchestration out of the FastAPI route layer so SkullHarbor can run multiple internal security adapters behind one authorized Quick Check workflow without exposing concrete scanner products to customers.

## Step 1 — Central ScanEngine

Completed: central job lifecycle, cancellation, execution-time target re-validation, centralized finding persistence, vendor-neutral API/UI boundary and restart recovery.

## Step 2 — Multi-adapter orchestration

A second internal web-security adapter is now executed by the same `ScanEngine` after the primary adapter.

### Completed

- one authorized Quick Check can execute both enabled internal adapters
- both adapters return the same normalized `Finding` schema
- findings from both adapters are merged and persisted centrally
- stop/cancellation is checked between adapters and while the second process is running
- customer-facing scanner identity remains `web-security`
- raw CLI banners are not streamed to the customer
- secondary adapter uses bounded concurrency/rate settings
- `dos`, `fuzz`, `bruteforce` and `intrusive` template tags are explicitly excluded from self-service execution
- source-provided severity is preserved conservatively; unknown severity becomes `info`
- CVE/CWE/reference metadata is retained when supplied by the adapter
- regression test added for secondary-adapter normalization and branding boundary

## Security invariants retained

- no scan is created for an unverified exact hostname
- destination must resolve only to public IP addresses
- destination is re-resolved immediately before execution
- scan flags remain server controlled
- dangerous scan modes are not customer selectable
- customer-facing scanner identity remains SkullHarbor / `web-security`

## Operational dependency

The backend host now needs both internal command-line adapters installed. See `THIRD_PARTY.md`. Their names remain engineering/deployment details and are intentionally not exposed in customer scan results.


## Step 3 — Orchestration hardening

Completed:

- adapter failures are isolated so one failed internal check does not discard successful results from another
- a scan fails only when no internal adapter completes successfully
- cancellation still stops the whole orchestration immediately
- private per-adapter execution metadata records status, duration and finding count for engineering diagnostics
- private adapter metadata is intentionally excluded from the customer status API
- overlapping normalized findings are deduplicated before persistence
- duplicate evidence and references are merged instead of silently discarded
- customer logs use neutral SkullHarbor wording for partial failures
- regression coverage added for deduplication and the private/public metadata boundary


## Step 4 — Execution budgets & cancellation hardening

Completed:

- every internal adapter now has a backend-owned hard execution budget
- a stalled child process is terminated gracefully and force-killed after a short grace period when necessary
- cancellation and timeout are distinct internal outcomes
- timeout of one adapter is isolated by the existing partial-success orchestration policy
- if every adapter times out/fails, the overall scan fails instead of hanging indefinitely
- child CLI stdout/stderr is discarded at the process boundary; structured result files remain the only ingestion path
- this avoids pipe back-pressure deadlocks while preserving the customer-facing neutral log boundary
- timeout values are not exposed as customer-controlled scan parameters
- deterministic regression coverage added for timeout, cancellation and normal process completion

## Step 5 — Closeout

Completed:

- deterministic database lifecycle coverage for partial success, total adapter failure and stopped jobs
- partial success persists useful normalized findings and completes the overall Quick Check
- total adapter failure produces a neutral customer-safe failure instead of leaking adapter exception text
- stopped jobs remain stopped and persist no findings
- customer boundary regression test covers frontend branding and normalized adapter text
- `raw_output` remains available internally in the database but is no longer serialized by the customer scan-detail API
- customer-safe text filtering covers both currently enabled internal adapters
- full Sprint 4 backend regression suite passes

## Sprint 4 Definition of Done

**DONE.** One authorized SkullHarbor Quick Check can orchestrate the enabled internal adapters behind a central ScanEngine, enforce bounded execution and cancellation, tolerate partial adapter failure, normalize/deduplicate results, persist stable lifecycle states and expose only vendor-neutral customer data.

**Final Sprint 4 build:** v0.4.0


## Next

Sprint 5 — Customer / Company Verification.
