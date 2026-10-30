# Boundaries

- **LifeOS backend:** owns records, domain rules and read services.
- **Optional backend adapter:** exposes only the existing health/money readers,
  under dedicated authentication and database read-only transactions.
- **MCP subprocess:** owns named tools, validated arguments, fixed HTTP routes,
  response limits and error mapping. It has no database credentials.
- **Compatible MCP clients (ChatGPT, Hermes, future Ask and others):** own the
  conversation and model interpretation.

The tool catalog is curated, not generated from every route in OpenAPI. Maintenance
and mutation endpoints must never become discoverable just because the backend
adds them. The HTTP client has no arbitrary URL/method tool; the two POST reads
are separately allowlisted and require explicit configuration.

Requests do not follow redirects or use ambient HTTP proxies. Main API credentials
are attached only to existing API reads; adapter credentials only to adapter reads.
Errors expose status/categories rather than response bodies or request URLs.

The package starts no network listener. Its supported MCP transport in v0.2
is stdio, allowing a compatible client to manage process lifetime. It makes outbound HTTP
requests to the configured LifeOS origin. An HTTP MCP transport can be added later
with deliberate authentication and network binding, not by exposing port 8000.
ChatGPT can instead connect through Secure MCP Tunnel forwarding to the stdio
process; see [client compatibility](clients.md). Neither connection is deployed.

Health/money adapter dependencies are separate from the MCP SDK to preserve the
backend's pinned runtime. Tool responses have a shared metadata envelope; numerical
payloads remain owned by LifeOS. The historical spending pilot is never read.
