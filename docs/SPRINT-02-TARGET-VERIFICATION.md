# Sprint 2 — Target Verification & Scan Authorization

**Build:** v0.2.0  
**Status:** IMPLEMENTED — E2E verification still required on a real DNS zone

## Goal

A registered/known customer must not be able to type an arbitrary third-party hostname and start Nikto. The backend now requires the exact hostname to be verified by DNS TXT before a scan can be created.

## Implemented

### Target model

New `targets` table:

- `id`
- `domain`
- `verification_token`
- `status` (`pending` / `verified`)
- `verified_at`
- `created_at`
- optional `user_id`

`scans.target_id` links each new scan to the verified target that authorized it.

### Target API

- `GET /api/targets`
- `GET /api/targets?user_id=<id>`
- `POST /api/targets`
- `POST /api/targets/{id}/verify`

### DNS TXT challenge

For `example.com` the API generates:

```text
Name:  _skullharbor-verification.example.com
Value: sh-verification=<random-token>
```

The target remains `pending` until the TXT value is observed by the backend resolver.

### Scan authorization gate

`POST /api/scan` now requires all of these conditions:

1. Valid HTTP/HTTPS URL.
2. No credentials embedded in the URL.
3. Exact hostname exists in the `targets` table.
4. Exact hostname status is `verified`.
5. Target belongs to the same `user_id` when a user is supplied. Unassigned targets can only be used by unassigned scans.
6. DNS resolves exclusively to public/global IP addresses.
7. DNS is resolved again immediately before Nikto starts.

If the target is not verified the API returns HTTP `403` and Nikto is never started.

### Network safety

Targets resolving to loopback, private, link-local, multicast, reserved or otherwise non-global IP addresses are blocked. This check happens:

- when adding a target,
- when verifying the target,
- when creating a scan,
- immediately before scanner execution.

This reduces DNS-rebinding / SSRF-style abuse against internal services.

### Nikto profile

The Sprint 1 rule remains unchanged:

```text
FREE -> -Tuning 12
```

Raw Nikto tuning parameters are not accepted from the frontend.

## E2E test

### 1. Add the target

```bash
curl -s -X POST http://127.0.0.1:8000/api/targets \
  -H 'Content-Type: application/json' \
  -d '{"domain":"your-authorized-domain.example"}'
```

Copy `verification_name` and `verification_value` from the response.

### 2. Add the TXT record at the DNS provider

Example:

```text
_skullharbor-verification.your-authorized-domain.example
sh-verification=<token>
```

### 3. Verify

```bash
curl -s -X POST http://127.0.0.1:8000/api/targets/1/verify
```

Expected result:

```json
{"status":"verified"}
```

### 4. Start the scan

```bash
curl -s -X POST http://127.0.0.1:8000/api/scan \
  -H 'Content-Type: application/json' \
  -d '{"target":"https://your-authorized-domain.example"}'
```

Expected: scan starts with `scan_profile=free` and the linked `target_id`.

### Negative tests

These must fail:

- arbitrary unverified public domain -> `403`
- `http://127.0.0.1` -> `400`
- private/internal DNS destination -> `400`
- hostname different from the verified hostname -> `403`
- user-bound verified target requested without/mismatched `user_id` -> `403`

## Deliberately deferred

- polished Targets frontend
- login/authentication enforcement
- company/KYC-style customer approval
- authorized engagement workflow for pentesters
- subdomain/wildcard ownership inheritance
- production queue/worker isolation

The UI is deliberately frozen until the functional/security path is complete.

## v0.2.1 follow-up

- Added the Targets screen to the React frontend.
- A customer can add a domain, see the exact DNS TXT challenge, copy both fields and run verification.
- Verified targets can be sent directly back to Quick Check.
- Added a dedicated scan-history screen using the existing scan API.
- Fixed stale RUNNING rows after backend reload/restart: because worker threads are in-memory, any database scan still marked `running` at process startup is now marked `failed` with an interruption reason.
- Confirmed scan authorization is checked before a new Scan row is created, so a newly rejected unverified target cannot create a ghost RUNNING scan.
- `dnspython==2.7.0` is part of backend requirements.
