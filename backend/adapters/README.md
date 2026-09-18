# Internal adapters

Concrete scanner executables are private backend implementation details. The
orchestrator addresses them only through neutral slots (`primary`, `secondary`,
`surface`). Customer APIs and UI must never expose vendor names or raw flags.

The executable adapters currently remain compatibility-exported by `scanner.py`;
new adapter work belongs in this package and plan-specific knobs belong under
`services/plans/`, not in API routes.
