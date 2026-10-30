"""Optional isolated test against the real LifeOS code, never its live database."""

import os
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

if os.environ.get("DATABASE_URL") != "sqlite+pysqlite:///:memory:":
    pytest.skip("Requires an explicitly isolated LifeOS SQLite runtime", allow_module_level=True)
pytest.importorskip("app")

from app.database import Base
from app.models.health import HealthRecord
from app.models.transaction import Transaction
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from lifeos_mcp.bridge import create_lifeos_router
from lifeos_mcp.client import DYNAMIC_ROUTES, READ_ROUTES

TOKEN = "synthetic-isolated-compat-token-12345"


def test_catalog_covers_the_actual_backend_get_routes():
    from app.main import app as lifeos_app

    actual = {
        r.path
        for r in lifeos_app.routes
        if "GET" in (getattr(r, "methods", None) or []) and getattr(r, "include_in_schema", False)
    }
    covered = set(READ_ROUTES.values()) | set(DYNAMIC_ROUTES.values())
    assert actual - covered == {"/mail/accounts"}
    assert covered <= actual


@pytest.fixture
def fixture_app(monkeypatch):
    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    monkeypatch.setattr("app.database.engine", engine)
    with Session(engine) as db:
        db.add(
            HealthRecord(
                source_id="synthetic-health-1",
                type="steps",
                value=1234,
                unit="count",
                start_time=datetime(2025, 9, 2, tzinfo=UTC),
                end_time=datetime(2025, 9, 2, 23, tzinfo=UTC),
            )
        )
        for i, amount in enumerate(["10.10", "20.20"]):
            db.add(
                Transaction(
                    txn_date=date(2025, 9, 2),
                    amount=Decimal(amount),
                    currency="INR",
                    direction="debit",
                    source="upi",
                    gmail_message_id=f"synthetic-{i}",
                    dedup_key=f"synthetic-{i}",
                    counterparty="Synthetic merchant",
                    spend_category_override="food",
                )
            )
        db.commit()
    api = FastAPI()
    api.include_router(create_lifeos_router(token=TOKEN))
    with TestClient(api) as client:
        yield client, engine
    engine.dispose()


def test_actual_health_reader_keeps_missing_values_unknown(fixture_app):
    client, engine = fixture_app
    response = client.post(
        "/agent-reads/health",
        headers={"Authorization": "Bearer " + TOKEN},
        json={"start_date": "2025-09-01", "end_date": "2025-09-03"},
    )
    assert response.status_code == 200
    payload = response.json()
    rows = {r["day"]: r for r in payload["daily"]}
    assert rows["2025-09-02"]["steps"] == 1234
    assert rows["2025-09-01"]["steps"] is None
    with Session(engine) as db:
        assert len(list(db.scalars(select(HealthRecord)))) == 1


def test_actual_money_query_preserves_totals_and_categories(fixture_app):
    client, engine = fixture_app
    response = client.post(
        "/agent-reads/money-query",
        headers={"Authorization": "Bearer " + TOKEN},
        json={
            "start_date": "2025-09-01",
            "end_date": "2025-09-03",
            "group_by": "category",
            "limit": 1,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["total"] == 30.3
    assert payload["rows"][0]["group"] == "food"
    with Session(engine) as db:
        assert len(list(db.scalars(select(Transaction)))) == 2


def test_actual_money_accounting_includes_emi_and_excludes_transfers_and_credits(fixture_app):
    client, engine = fixture_app
    with Session(engine) as db:
        for i, (amount, direction, category) in enumerate(
            [
                ("50.00", "debit", "emi"),
                ("100.00", "debit", "transfer"),
                ("20.00", "debit", "reversed_debit"),
                ("200.00", "credit", None),
            ]
        ):
            db.add(
                Transaction(
                    txn_date=date(2025, 9, 2),
                    amount=Decimal(amount),
                    currency="INR",
                    direction=direction,
                    category=category,
                    source="upi",
                    gmail_message_id=f"synthetic-accounting-{i}",
                    dedup_key=f"synthetic-accounting-{i}",
                    counterparty="Synthetic accounting",
                )
            )
        db.commit()
    response = client.post(
        "/agent-reads/money-query",
        headers={"Authorization": "Bearer " + TOKEN},
        json={"start_date": "2025-09-01", "end_date": "2025-09-03", "limit": 1},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["total"] == 80.3
    assert payload["summary"]["count"] == 3
    assert len(payload["rows"]) == 1  # Full summary is independent of the row limit.
