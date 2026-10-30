# Optional backend adapter

Detailed synced health and guarded analytical money queries already exist inside
LifeOS, but are not public HTTP routes in the current backend. This adapter exposes
those existing functions without copying their calculations or sending requests
through `/chat`.

**Not deployed.** Installing it requires a separate LifeOS backend change and
verification. Creating this repository does not rebuild the running API.

## Installation inside LifeOS

Install a pinned `lifeos-mcp` wheel with its `bridge` extra into the LifeOS image,
retaining the backend's existing dependency pins. **Do not install the `server`
extra there**: it is for the MCP client-side subprocess and has a newer Pydantic
requirement. The bridge uses existing FastAPI/SQLAlchemy/Pydantic dependencies.

Add this to LifeOS's FastAPI setup, after constructing `app`:

```python
import os

from lifeos_mcp.bridge import create_lifeos_router

agent_token = os.environ.get("LIFEOS_AGENT_TOKEN")
if agent_token:
    app.include_router(create_lifeos_router(token=agent_token))
```

Configure the dedicated token privately on the backend and MCP process. Pass the
variable into the backend container explicitly; its current Compose file does not
forward it. The adapter refuses tokens shorter than 32 characters. No token is
generated, stored or applied by this repository creation task.

## Added routes

| Method | Path | Implementation |
|---|---|---|
| POST | `/agent-reads/health` | `AgentTools(db).health_records(...)` |
| POST | `/agent-reads/money-query` | `app.services.money_query.query_money(db, ...)` |

POST carries structured read arguments; neither operation changes records.
Both routes require `Authorization: Bearer <dedicated-agent-token>`, even if
ordinary LifeOS API authentication is disabled. A main API token is not accepted
unless an operator deliberately configures the same value (use separate values).

Each request uses a separate SQLAlchemy connection with a read-only transaction.
PostgreSQL uses `SET TRANSACTION READ ONLY` plus a 15-second SQL statement timeout;
SQLite tests use `PRAGMA query_only=ON`. The session is rolled back after the read.
No migration, collector, recompute, phone connection or model call is performed.
Unknown arguments, SQL fields and invalid/broad date windows are rejected.

Errors do not return upstream exception strings or DB errors. The connector does
not silently fall back when the adapter is absent or unavailable.

## Test before deploying

Run the optional compatibility test in a disposable container created from the
existing API image, with no production environment/volumes and no network:

```sh
docker run --rm --network none \
  -e DATABASE_URL=sqlite+pysqlite:///:memory: \
  -e ENVIRONMENT=test \
  -e PYTHONPATH=/mcp-src/src:/app \
  -v /path/to/lifeos-mcp:/mcp-src:ro \
  --entrypoint python <existing-lifeos-api-image> \
  -m pytest /mcp-src/tests/test_lifeos_compat.py -q -p no:cacheprovider
```

The image needs its existing pytest and backend dependencies, but no MCP SDK
upgrade. The test creates synthetic records in SQLite only. The transport and
guard tests run separately through the regular repository test suite.
