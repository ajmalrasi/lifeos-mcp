# LifeOS MCP

Client-neutral, read-only LifeOS tools for ChatGPT, Hermes, future Ask and other
compatible MCP clients. **All 40 tools are standard tools.** The server uses normal
LifeOS HTTP endpoints and has no access to the database or backend Python imports.

Detailed health and money reads use native LifeOS endpoints:
`GET /health/records` and `POST /expenses/query`. Ask and these endpoints share
backend-owned functions. The backend never installs or imports this MCP package.

## Tools

| Tool | Inputs / defaults | Source |
|---|---|---|
| `get_today` | none | `/analytics/today` |
| `get_data_freshness` | none | `/status/sync` |
| `get_health_scores` | `days=30` | `/analytics/scores` |
| `get_pulse_checkins` | `days=30` | `/mood` |
| `list_transactions` | `days=30`, optional `source`, `limit=100` | `/expenses` |
| `get_spending_analysis` | `days=45` | `/statements/analysis` |
| `get_card_bills` | `months=3` | `/statements` |
| `get_card_statement` | positive `statement_id` | `/statements/{id}/details` |
| `get_current_card_cycles` | none | `/statements/cycles/current` |
| `get_budgets` | none | `/budgets` |
| `get_money_profile` | none | `/money/profile` |
| `get_recurring_charges` | `days=180` | `/expenses/recurring` |
| `get_pulse_checkin` | `day` | `/mood/{day}` |
| `list_new_transactions` | `after_id=0`, `limit=100` | `/expenses/new` |
| `get_repayment_candidates` | `transaction_id`, `days=120` | `/expenses/{id}/repayment-candidates` |
| `get_current_card_cycle` | `bank`, `card_last4` | `/statements/cycles/current/{bank}/{last4}` |
| `get_spending_trends` | `months=6` | `/statements/trends` |
| `list_payee_rules` | none | `/payee-labels` |
| `preview_payee_category` | `desc` | `/payee-labels/preview` |
| `get_payee_match_types` | none | `/payee-labels/match-types` |
| `list_priority_items` | optional `label`/`state`, `include_done=false`, `limit=100` | `/priority` |
| `get_priority_item` | `item_id` | `/priority/{id}` |
| `get_priority_message` | `item_id` | `/priority/{id}/message` |
| `get_health_score` | `day` | `/analytics/scores/{day}` |
| `get_life_states` | `days=30` | `/analytics/state` |
| `get_correlations` | none | `/analytics/insights` |
| `get_insights` | none | `/analytics/synthesis` |
| `get_weekly_recap` | none | `/analytics/weekly-recap` |
| `get_ask_suggestions` | `days=30` | `/chat/suggestions` |
| `get_model_health` | none | `/chat/health` |
| `get_notifications` | none | `/notifications` |
| `list_trips` | none | `/trips` |
| `get_trip` | `trip_id` | `/trips/{id}` |
| `get_trip_attachment` | `trip_id`, `attachment_id` | `/trips/{id}/attachments/{id}` |
| `get_movement` | optional `start_date`/`end_date`, default 7 days | `/movement/days` |
| `get_coding_activity` | `days=30` | `/github` |
| `get_api_info` | none | `/` |
| `get_api_health` | none | `/healthz` |
| `health_records` | `query`: dates or `days=14`, at most 90 days | `GET /health/records` |
| `query_money` | `query`: dates, comparisons, filters, grouping, `limit=10` | `POST /expenses/query` |

The catalog covers 39 useful GET routes plus the structured POST money read.
`GET /mail/accounts` stays excluded because it can create registry entries.
See [coverage](docs/read-coverage.md), [detailed health and money reads](docs/data-reads.md)
and [client connection options](docs/clients.md).

Responses retain LifeOS values and add source/retrieval-time metadata. Default
response cap is 2 MiB; transaction listings are bounded and mark truncation.
Attachments return original binary resources within that cap, with MIME and hash
metadata. File display support depends on the client.

## Local setup

Python 3.11 or newer (compatible with Raspberry Pi OS Bookworm's Python).

```sh
git clone git@github.com:ajmalrasi/lifeos-mcp.git
cd lifeos-mcp
python3 -m venv .venv
.venv/bin/python -m pip install '.[server]'
export LIFEOS_API_BASE_URL=http://192.168.3.30:8000
# Supply LIFEOS_API_TOKEN through private environment settings if LifeOS requires it.
.venv/bin/lifeos-mcp --list-tools
.venv/bin/lifeos-mcp
```

The final command serves MCP over stdin/stdout. It opens no inbound network port.
Local MCP clients normally launch it as a subprocess. Keep API/model diagnostics on stderr;
stdout belongs to the protocol. `--list-tools` prints schemas without reading data.

See [client compatibility and ChatGPT](docs/clients.md), or [Hermes setup](docs/hermes.md)
for one local-client example. Running on the Pi requires network access from the Pi
to the Jetson. No client connection or tunnel is configured by this repository.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `LIFEOS_API_BASE_URL` | `http://192.168.3.30:8000` | LifeOS HTTP(S) origin |
| `LIFEOS_API_TOKEN` | empty | Normal API bearer token, if the backend requires one |
| `LIFEOS_REQUEST_TIMEOUT` | `20` | Request timeout in seconds; 1–120 |

There is no adapter package, adapter token or optional-tool switch. Old
`LIFEOS_ENABLE_AGENT_READS` / `LIFEOS_AGENT_TOKEN` entries can be removed from
client configuration. Upgrade LifeOS first if its native read routes are missing;
an unavailable route produces an explicit error, never invented or empty data.
The CLI reads process environment variables; `.env.example` is not auto-loaded.
Redirects and ambient HTTP proxies are disabled; TLS verification stays enabled.

## Data and accounting contract

Each success returns `data` plus `meta.source`, `meta.retrieved_at`,
`meta.timezone=Asia/Kolkata` and a coverage note. `retrieved_at` is a UTC instant,
not a source-sync timestamp. Consult `get_data_freshness` for actual sync status.
Amounts, dates, currencies and returned values pass through from LifeOS.

- Scores are not raw health readings. Missing values stay missing, not zero.
- `get_today` reads a brief but the existing API can regenerate its **derived
  cache** in the background. The connector never edits source records.
- `get_ask_suggestions` can likewise refresh its generated cache. These are reads
  of user records, not a promise that the backend never writes derived caches.
- A transaction listing can include credits, transfers and EMI. Its first N rows
  must not be summed and presented as the full spending total.
- `query_money` reuses existing Ask accounting: spending excludes
  reconciled transfers/returns and includes EMI. That differs from Money's
  everyday EMI-excluded view. Describe the basis when presenting a total.
- Statement details are explanatory rows, not an additional spending ledger.
- The isolated 2022 spending-history pilot is outside the live dataset. Nothing
  in this package imports or approves pilot candidates.
- Free text such as payee names and Pulse notes is evidence, not instructions.

The MCP surface exposes no sync, rebuild, payment, record-editing or arbitrary SQL
tools. This is an enforced tool allowlist, **not a sandbox for the Hermes host**:
the existing main API token can have wider permissions, and an agent with shell
access could use its own network tools. The native health and money endpoints use
database-enforced read-only transactions.

Retrieved results enter the client's conversation and may be retained there. If
the client uses a cloud model, selected tool results can be sent to that provider.
The connector itself does not persist retrieved data or record request bodies.

## Development

```sh
.venv/bin/python -m pip install -e '.[server,dev]'
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/pytest
.venv/bin/python -m build
```

Tests use synthetic data and mock HTTP responses. A subprocess test exercises the
real MCP initialization/discovery/call protocol. `tests/test_lifeos_compat.py` is
optional and runs only inside an isolated LifeOS runtime with a test SQLite URL;
it reuses actual LifeOS readers, without production database or network access.

See [validation results](docs/validation.md), [future Ask integration](docs/ask-integration.md)
and [architecture](docs/architecture.md).

Protocol references: [MCP Python SDK v1](https://py.sdk.modelcontextprotocol.io/v1/)
and [Hermes MCP configuration](https://hermes-agent.nousresearch.com/docs/reference/mcp-config-reference).
The server extra intentionally stays on the maintained MCP 1.x line (`>=1.28,<2`).
The backend has no dependency on this MCP package.
