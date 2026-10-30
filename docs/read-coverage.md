# Complete reading coverage

Audit date: 2026-10-31. The live backend has 39 application GET operations. v0.2
exposes 38, including utility reads and binary trip attachments. Twelve were in
v0.1; the 26 additions complete the useful read catalog.

See the README tool table for each route mapping. `tests/fixtures/backend-get-paths.json`
stores only the audited route names, with no personal payloads. Coverage tests
compare every route against the allowlist. The isolated compatibility test also
compares the catalog against the actual LifeOS runtime's registered GET routes.

## Areas added after the initial version

| Area | Added tools |
|---|---|
| Specific-day health and Pulse, state history | `get_health_score`, `get_pulse_checkin`, `get_life_states` |
| Money analysis and transaction browsing | `get_spending_trends`, `get_current_card_cycle`, `list_new_transactions`, `get_repayment_candidates` |
| Categorization explanations | `list_payee_rules`, `preview_payee_category`, `get_payee_match_types` |
| Priority mail | `list_priority_items`, `get_priority_item`, `get_priority_message` |
| Insights and recap | `get_correlations`, `get_insights`, `get_weekly_recap` |
| Trips and files | `list_trips`, `get_trip`, `get_trip_attachment` |
| Movement | `get_movement` |
| Coding history | `get_coding_activity` |
| Ask starters and notifications | `get_ask_suggestions`, `get_notifications` |
| Diagnostics | `get_model_health`, `get_api_info`, `get_api_health` |

The separate, included backend adapter adds two analytical reads: `health_records`
and `query_money`. They are not among the 39 current GET routes, and are advertised
only after an operator installs and enables that adapter.

## Excluded GET operation

`GET /mail/accounts` is misleadingly named for this purpose: its implementation
calls `finance_account(...)`, which can bootstrap a finance account and purpose
assignment into the registry. It also inspects authorization state through the mail
provider. It is therefore excluded from a catalog intended to avoid source/config
changes. Exposing it safely would require a pure-read backend variant first.

`get_data_freshness` continues to provide source health; it is not claimed to be a
complete mail-account inventory.

## Other intentional exclusions

- Source ingestion and sync operations, execution collection, recompute, rebuild,
  insight/recap generation, email authorization, device registration and every
  record edit or deletion.
- `POST /chat` and `/chat/stream`: they ask a model to write an answer rather than
  exposing a data-read capability, and routing Ask back into them risks recursion.
- Documentation/schema framework routes (`/docs`, `/redoc`, `/openapi.json`,
  `/docs/oauth2-redirect`), which are development references, not life-data tools.
- Phone-only raw GPS routes, unsynced trip edits, private source archives and
  spending-history pilot candidates: the live API does not expose those datasets.

The existing `GET /analytics/today` and `GET /chat/suggestions` can refresh their
derived prose caches in the background. Their tools document that behavior;
read-only here means no changes to source records, settings or financial decisions.
`get_repayment_candidates` and category previews are advisory and never apply a
match or edit. Reading Priority's source message can contact Gmail but does not
send, delete or modify mail.
