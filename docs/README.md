# SkullHarbor UI-Scanner — Development Roadmap

This folder is the development log and source of truth for the current project status.

## Working rules

1. KISS first.
2. Finish the current sprint before starting the next one.
3. Every meaningful development step is documented.
4. Scanner findings and target data stay local on the customer's installation.
5. Customer/licensing infrastructure is kept separate from local scan data.
6. No verified customer -> no license.
7. No authorized scope -> no scan.

## Roadmap

| Sprint | Goal | Status |
|---|---|---|
| S1 | Nikto MVP | IN PROGRESS |
| S2 | Multi Scanner: Nikto + Nmap + Nuclei | PLANNED |
| S3 | Product UX | PLANNED |
| S4 | Customer Verification | PLANNED |
| S5 | License Server | PLANNED |
| S6 | Scope / Engagement Authorization | PLANNED |
| S7 | App Licensing | PLANNED |
| S8 | Release & Security Hardening | PLANNED |

## Product architecture

```text
Customer PC                         SkullHarbor services
---------------------------         ---------------------------
UI-Scanner                          Customer
Local scanner binaries              Verification
Local targets                       Products
Local findings                      Licenses
Local scan history                  Seats
                                    Subscriptions
                                    Installations
                                    Authorized scopes
```

The central service must not require scan findings or target results simply to enforce licensing.
