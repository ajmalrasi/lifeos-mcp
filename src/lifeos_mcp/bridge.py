"""Optional FastAPI adapter installed inside LifeOS, never on the Pi by itself.

The base package and bridge extras do not depend on the MCP SDK. This avoids
upgrading the live backend's pinned Pydantic merely to add the adapter.
"""

import hmac
from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from lifeos_mcp.contracts import HealthQuery, MoneyQuery


def create_read_router(
    *, engine, health_reader: Callable, money_reader: Callable, token: str
) -> APIRouter:
    """Create exactly two guarded reads, using caller-supplied LifeOS services."""
    if len(token) < 32:
        raise ValueError("A dedicated agent token of at least 32 characters is required")

    def authenticate(authorization: str | None = Header(default=None)):
        if authorization is None or not hmac.compare_digest(
            authorization.encode(), ("Bearer " + token).encode()
        ):
            raise HTTPException(401, "Invalid agent token", headers={"WWW-Authenticate": "Bearer"})

    def read_session():
        with engine.connect() as connection:
            dialect = connection.dialect.name
            if dialect not in {"postgresql", "sqlite"}:
                raise HTTPException(503, "Unsupported read-only database dialect")
            transaction = connection.begin()
            try:
                if dialect == "postgresql":
                    connection.exec_driver_sql("SET TRANSACTION READ ONLY")
                    connection.exec_driver_sql("SET LOCAL statement_timeout = '15000ms'")
                else:
                    connection.exec_driver_sql("PRAGMA query_only = ON")
                with Session(bind=connection, autoflush=False) as db:
                    yield db
            finally:
                if transaction.is_active:
                    transaction.rollback()
                if dialect == "sqlite":
                    # Reset the connection-local testing guard before returning to the pool.
                    connection.exec_driver_sql("PRAGMA query_only = OFF")
                    connection.rollback()

    router = APIRouter(
        prefix="/agent-reads", tags=["agent-reads"], dependencies=[Depends(authenticate)]
    )

    def dispatch(reader, db, query):
        try:
            result = reader(db, **query.model_dump(mode="json", exclude_none=True))
        except ValueError:
            raise HTTPException(422, "LifeOS rejected the analytical query") from None
        except Exception:
            # Never return raw DB errors, credentials or personal source data as an error.
            raise HTTPException(502, "LifeOS could not complete this read") from None
        if not isinstance(result, dict) or "error" in result:
            raise HTTPException(502, "LifeOS could not complete this read")
        return result

    @router.post("/health")
    def health(query: HealthQuery, db: Annotated[Session, Depends(read_session)]):
        return dispatch(health_reader, db, query)

    @router.post("/money-query")
    def money(query: MoneyQuery, db: Annotated[Session, Depends(read_session)]):
        return dispatch(money_reader, db, query)

    return router


def create_lifeos_router(*, token: str) -> APIRouter:
    """Wire the adapter to existing LifeOS code; import only inside its runtime."""
    from app.database import engine
    from app.services.agent_tools import AgentTools
    from app.services.money_query import query_money

    def health_reader(db, **kwargs):
        return AgentTools(db).health_records(**kwargs)

    return create_read_router(
        engine=engine, health_reader=health_reader, money_reader=query_money, token=token
    )
