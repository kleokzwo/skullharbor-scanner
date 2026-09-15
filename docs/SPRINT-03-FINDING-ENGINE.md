# Sprint 03 — Finding Engine

Version: **v0.3.0**

## Goal

Separate the customer product from concrete scanner implementations and provide
one stable, understandable finding model for all future adapters.

```text
Internal scanner adapter
        ↓
Finding normalizer
        ↓
SkullHarbor knowledge rules
        ↓
Unified Finding
        ↓
API / customer UI
```

## Implemented

- customer-facing engine id: `web-security`
- concrete scanner/vendor name removed from customer UI and API payloads
- existing SQLite rows with the old public scanner id are migrated to
  `web-security`
- normalized fields added:
  - `rule_id`
  - `category`
  - `severity`
  - `title`
  - `description`
  - `impact`
  - `recommendation`
  - `evidence`
  - `reference`
  - `raw_output`
- explicit initial knowledge rules for:
  - X-Content-Type-Options
  - clickjacking/frame protection
  - Content Security Policy
  - HSTS
  - server/version disclosure
  - directory listing
- unknown findings remain `INFO / web.unclassified`; no severity is guessed
- customer live log is vendor-neutral
- FREE profile remains server-controlled; browser cannot send scanner flags

## Product naming

Customer-facing product wording:

- **SkullHarbor Web Check**
- **Basic web security checks**
- **Web security observation**

The implementation adapter remains documented internally. Do not claim that
SkullHarbor authored third-party scanner code.

## Why

The product value is the complete service: authorization gate, safe profiles,
normalization, knowledge rules, understandable remediation, history, reporting,
and later multi-engine correlation. A customer should not need to understand
which CLI utility produced a raw signal.

## Next

Expand the knowledge base using real authorized scan outputs and add deduplication
so multiple internal engines can map to one customer finding.
