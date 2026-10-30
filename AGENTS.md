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
- All 40 tools are standard. Detailed health/money calls use native LifeOS routes,
  normal API credentials and backend-owned validation. No adapter or backend imports.
- Always push directly to main. Do not create branches or PRs unless the user changes
  this instruction. This applies to both repositories.
- This is client-neutral: ChatGPT, Hermes, future LifeOS Ask and other compatible
  hosts can use the same catalog. Hermes setup is one example, not the architecture.
- Use Python 3.11+. The MCP subprocess has its own dependencies; do not install this package
  in the backend or alter backend pins for MCP.
- Run Ruff and pytest after functional changes. Exercise transport and security
  behavior, not just tool function names. Compatibility checks must use an isolated
  test SQLite database and no production environment, credentials or volumes.
- Ask migration is future work: preserve model-led optional retrieval and existing
  request/token limits, and never add canned factual fallbacks.
