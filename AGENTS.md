# Working on lifeos-mcp

This is a separate repository from `life_os`. Do not edit or deploy the LifeOS
backend, Raspberry Pi services or Hermes configuration unless the user requests
that work. Creation of this repo was explicitly scoped to connecting Hermes later.

- Keep this a read-only tool catalog. Never expose general HTTP requests, SQL,
  administrative rebuilds, sync, money edits, payment or statement-paid writes.
- Accounting and health aggregation belong to LifeOS. Reuse its services; do not
  reproduce them in this repo or ask an LLM to produce tool data.
- Never commit personal records, source emails, statements, credentials or exports.
  Test fixtures must be synthetic. Do not print tool result bodies during live QA.
- Respect missing data, source freshness, currencies, date windows and the existing
  Ask EMI-included / everyday Money EMI-excluded distinction.
- Thirty-eight tools cover the current API's useful GET operations. The
  `/mail/accounts` GET is excluded because it bootstraps registry entries. Two tools
  require the optional backend
  adapter and must not be advertised when disabled.
- This is client-neutral: ChatGPT, Hermes, future LifeOS Ask and other compatible
  hosts can use the same catalog. Hermes setup is one example, not the architecture.
- Use Python 3.11+. The `server` and `bridge` extras are intentionally separate;
  do not upgrade the backend's pinned Pydantic to install an MCP subprocess.
- Run Ruff and pytest after functional changes. Exercise transport and security
  behavior, not just tool function names. Compatibility checks must use an isolated
  test SQLite database and no production environment, credentials or volumes.
- Ask migration is future work: preserve model-led optional retrieval and existing
  request/token limits, and never add canned factual fallbacks.
