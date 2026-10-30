# Boundaries

- LifeOS owns records, request validation, health aggregation and accounting.
- Native `GET /health/records` and `POST /expenses/query` share backend services
  with Ask. They follow normal API authentication and use read-only DB transactions.
- The separate MCP repo owns tool schemas and HTTP/protocol transport. It imports
  no backend code, has no database credentials and exposes no arbitrary SQL/HTTP tool.
- Compatible clients own conversation/model interpretation. See `clients.md`.

All 40 tools are standard. Thirty-nine wrap GET operations; one POST carries a
structured money read. The source-mutating `/mail/accounts` GET is excluded.
Backend schema and MCP wire models have contract-parity tests in an isolated runtime.
Only the backend owns calculations. The backend has no dependency on this package.

Stdio is the supported MCP transport; no inbound listener is opened. ChatGPT may
connect through Secure MCP Tunnel. Source records stay in LifeOS, while selected
results enter the client's conversation and may reach its model provider.

HTTP routes and methods are allowlisted, redirects/proxies are disabled, response
sizes/timeouts are bounded, and errors omit upstream bodies and secrets. The
historical spending pilot is not accessed. Today/suggestion reads can refresh the
backend's derived caches; no MCP tool edits source records, settings or financial flags.
