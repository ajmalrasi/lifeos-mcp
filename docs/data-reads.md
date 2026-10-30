# Detailed health and money reads

Both are standard MCP tools. They call native LifeOS endpoints with the normal
API credentials. The backend owns their validation and calculations; Ask uses
the same services. The MCP server performs no model call, direct database read,
phone connection, collector or data import.

| MCP tool | Native API |
|---|---|
| `health_records` | `GET /health/records` |
| `query_money` | `POST /expenses/query` (a structured read) |

## `health_records`

Read **synced measurements and workout details**, rather than the processed scores
returned by `get_health_scores` or the prose returned by `get_today`.

Inputs: a `query` object containing `days` (default 14, maximum 90), or inclusive
`start_date` and `end_date`. Historical windows are supported. End dates cannot be
in the future. End-only queries are resolved to explicit start/end dates before
calling the existing health reader.

Current returned information:

- Per-day total sleep, deep sleep and REM sleep, in hours.
- Per-day resting heart rate, HRV, steps, active energy and exercise minutes.
- Workouts with recorded type, start time, duration, energy and average heart rate.
- Workout summaries for the requested window, monthly groupings and last-workout
  context. The last workout may precede the requested window and is labeled as such.
- Health receipt time and whether workout exports have been seen.

Example question: “Show my sleep and workouts for the last two weeks.”

This is not an unrestricted export of every Apple Health sample/type. It exposes
the existing LifeOS reader's supported measurements and summaries. Overlap handling,
sleep wake-up-day assignment, revision handling and units remain LifeOS's domain
logic. A missing reading stays unknown, not zero. Workout effort is not judged by
a new threshold in this package.

Example request (synthetic dates):

```json
{"query": {"start_date": "2025-09-01", "end_date": "2025-09-14"}}
```

## `query_money`

Read exact money analytics over live stored transactions. Unlike a limited
transaction listing, it can calculate a complete-window summary, filter and group
the matching data, and compute a comparison in the same operation.

Inputs inside `query` include:

- `mode`: spending, income or all rows; defaults to spending.
- Inclusive primary dates; defaults to the latest 30-day window.
- Optional baseline dates for comparisons; both baseline dates are required.
- Category, payee text, account text, source and minimum/maximum amount filters.
- Grouping by day, week, month, category, payee, account, source or direction.
- Sorting and a detail/group row limit of 1–50; default 10. Each date window is
  limited to 3660 days. The full summary is calculated before the row limit.

Returns LifeOS's summary, requested rows/groups, window/filter metadata, available
coverage and, when requested, baseline totals, difference and percentage change.
The connector preserves backend amounts and uses no model-written SQL.

Example question: “Compare food spending in September with August, by merchant.”

```json
{
  "query": {
    "start_date": "2025-09-01",
    "end_date": "2025-09-30",
    "compare_start_date": "2025-08-01",
    "compare_end_date": "2025-08-31",
    "category": "food",
    "group_by": "counterparty"
  }
}
```

The existing Ask spending definition excludes reconciled transfers and returns
but **includes EMI**. Money's everyday view excludes EMI. State this difference
when presenting results. Statement line items are not added as a second set of
transactions, and the isolated spending-history pilot is not part of this query.

Neither tool changes budgets, refunds, categories, repayments, bill-paid flags or
any other record. See the native [LifeOS API documentation](https://github.com/ajmalrasi/life_os/blob/main/backend/docs/data-reads.md).
