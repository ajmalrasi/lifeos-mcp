# Validation — 2026-10-31

- Local Python 3.12: **71 tests passed**, one optional LifeOS-runtime test module
  skipped as intended outside that runtime.
- Real MCP stdio subprocess: initialization, discovery of 12 annotated tools,
  structured successful response, invalid arguments and unknown-tool errors pass.
- HTTP guard tests: fixed routes, blocked mutations, scoped credentials, refused
  redirects, bounded responses and sanitized errors pass.
- Adapter tests: dedicated authentication, rejected SQL/unknown arguments,
  database-enforced rejection of a write and pooled-connection cleanup pass.
- Actual current LifeOS API image, disposable container, no network or production
  environment/volumes, synthetic SQLite: **3 compatibility tests passed**. Confirmed
  health missingness, health values, categories, totals independent of detail-row
  limits, EMI inclusion and exclusion of transfers/reversed debits/credits.
- Ruff lint/format checks, dependency consistency and wheel/sdist build pass.

The repository also configures GitHub Actions for Python 3.11 and 3.12. See the
repository's Actions page for remote run results, which are separate from the
checks above.

These checks are not a deployment or financial audit. No production API mutation,
database import, collector, backend rebuild, Ask migration or Hermes configuration
change was performed. The optional adapter is not present on the running API.
