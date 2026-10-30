import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from lifeos_mcp.bridge import create_read_router

TOKEN = "synthetic-agent-token-1234567890123456"
HEADERS = {"Authorization": "Bearer " + TOKEN}


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    with engine.begin() as db:
        db.execute(text("CREATE TABLE synthetic_records (value INTEGER)"))
        db.execute(text("INSERT INTO synthetic_records VALUES (7)"))
    yield engine
    engine.dispose()


def app_for(engine, reader):
    app = FastAPI()
    app.include_router(
        create_read_router(engine=engine, health_reader=reader, money_reader=reader, token=TOKEN)
    )
    return app


def test_adapter_requires_its_own_authentication_before_reading(engine):
    calls = []

    def reader(db, **kwargs):
        calls.append(kwargs)
        return {"value": db.scalar(text("SELECT value FROM synthetic_records"))}

    with TestClient(app_for(engine, reader)) as client:
        assert client.post("/agent-reads/health", json={}).status_code == 401
        assert (
            client.post(
                "/agent-reads/health", json={}, headers={"Authorization": "Bearer main-api-token"}
            ).status_code
            == 401
        )
        assert calls == []
        response = client.post(
            "/agent-reads/health", json={"days": 3, "end_date": "2025-09-03"}, headers=HEADERS
        )
        assert response.status_code == 200
        assert response.json() == {"value": 7}
        assert calls[0] == {"days": 3, "start_date": "2025-09-01", "end_date": "2025-09-03"}


def test_adapter_enforces_database_read_only_even_if_reader_attempts_a_write(engine):
    def reader(db, **kwargs):
        db.execute(text("INSERT INTO synthetic_records VALUES (99)"))
        return {"unexpected": True}

    with TestClient(app_for(engine, reader)) as client:
        response = client.post("/agent-reads/money-query", json={}, headers=HEADERS)
        assert response.status_code == 502
        assert "INSERT" not in response.text
    with engine.begin() as db:
        assert db.scalar(text("SELECT count(*) FROM synthetic_records")) == 1
        # The SQLite testing guard must not leak back into the pooled connection.
        db.execute(text("INSERT INTO synthetic_records VALUES (8)"))


def test_unknown_query_arguments_are_rejected_and_no_extra_routes_exist(engine):
    app = app_for(engine, lambda db, **kwargs: pytest.fail("Invalid query reached reader"))
    with TestClient(app) as client:
        assert (
            client.post(
                "/agent-reads/money-query", json={"sql": "select private"}, headers=HEADERS
            ).status_code
            == 422
        )
        assert client.delete("/agent-reads/money-query", headers=HEADERS).status_code == 405
    paths = set(app.openapi()["paths"])
    assert paths == {"/agent-reads/health", "/agent-reads/money-query"}


def test_reader_error_payload_is_not_a_success_or_a_leak(engine):
    with TestClient(app_for(engine, lambda db, **kwargs: {"error": "sensitive-source"})) as client:
        response = client.post("/agent-reads/health", json={}, headers=HEADERS)
        assert response.status_code == 502
        assert "sensitive-source" not in response.text


def test_short_adapter_token_is_rejected(engine):
    with pytest.raises(ValueError):
        create_read_router(
            engine=engine, health_reader=lambda: None, money_reader=lambda: None, token="short"
        )
