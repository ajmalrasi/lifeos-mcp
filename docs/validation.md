# Validation — 2026-10-31

v0.3 uses native LifeOS endpoints; the adapter package and feature flag are removed.

- MCP local Python 3.12: **101 tests passed**, one optional cross-repository test
  module skipped outside the isolated LifeOS runtime.
- Real MCP stdio initialization, discovery of all 40 standard tools, structured
  results and input/error handling pass.
- Isolated actual LifeOS runtime, synthetic SQLite, no network: **5 cross-repository
  tests passed**, including health/money results, API coverage and exact wire-schema
  parity. This uses the native routes rather than installing an adapter.
- Backend focused tests: **49 passed**, covering the new APIs, authentication and
  existing Ask behavior.
- Backend full suite: **440 passed, 5 failed**. All five failures reproduce on the
  unchanged baseline (card-cycle date, two Priority tests and two statement-date
  tests); no new failure was introduced.
- Ruff lint/format checks and wheel/sdist build pass.
- Live Jetson API is healthy after deployment of LifeOS commit `5fc64d3`.
- Actual MCP calls to `GET /health/records` and `POST /expenses/query` succeeded
  against the live API, with all 40 tools advertised and no adapter configuration.
- PostgreSQL's `transaction_read_only=on` and the 15-second SQL statement timeout
  were verified on the production read-session dependency, without attempting writes.

Both repositories use direct pushes to main per the user's instruction. No Hermes
or ChatGPT connection has been configured. No source-data import, financial edit,
collector change, schema change or Ask-to-MCP transport migration was performed.
