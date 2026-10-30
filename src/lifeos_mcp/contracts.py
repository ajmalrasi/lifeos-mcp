"""Versioned arguments for the optional backend reads. No model-authored SQL."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing_extensions import TypedDict


class ToolResult(TypedDict):
    data: dict[str, Any] | list[Any]
    meta: dict[str, Any]


class HealthQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    days: int = Field(default=14, ge=1, le=90, strict=True)
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode="after")
    def validate_window(self):
        end = self.end_date or datetime.now(ZoneInfo("Asia/Kolkata")).date()
        start = self.start_date or end - timedelta(days=self.days - 1)
        if start > end or (end - start).days >= 90:
            raise ValueError("Health windows must be ordered and contain at most 90 days")
        if end > datetime.now(ZoneInfo("Asia/Kolkata")).date():
            raise ValueError("Health end_date cannot be in the future")
        # Send both dates: the legacy health function's end-only default starts at today.
        self.start_date, self.end_date, self.days = start, end, (end - start).days + 1
        return self


class MoneyQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["spending", "income", "all"] = "spending"
    start_date: date | None = None
    end_date: date | None = None
    compare_start_date: date | None = None
    compare_end_date: date | None = None
    group_by: Literal[
        "none", "day", "week", "month", "category", "counterparty", "account", "source", "direction"
    ] = "none"
    category: str | None = Field(default=None, max_length=200)
    counterparty_contains: str | None = Field(default=None, max_length=200)
    account_contains: str | None = Field(default=None, max_length=200)
    source: str | None = Field(default=None, max_length=200)
    min_amount: Decimal | None = Field(default=None, ge=0, allow_inf_nan=False)
    max_amount: Decimal | None = Field(default=None, ge=0, allow_inf_nan=False)
    sort_by: Literal["total", "count", "average", "max", "date", "amount", "name"] | None = None
    sort_order: Literal["asc", "desc"] = "desc"
    limit: int = Field(default=10, ge=1, le=50, strict=True)

    @model_validator(mode="after")
    def validate_windows(self):
        end = self.end_date or datetime.now(ZoneInfo("Asia/Kolkata")).date()
        start = self.start_date or end - timedelta(days=29)
        if start > end or (end - start).days >= 3660:
            raise ValueError("Money windows must be ordered and contain at most 3660 days")
        if (self.compare_start_date is None) != (self.compare_end_date is None):
            raise ValueError("Supply both comparison dates")
        if self.compare_start_date and self.compare_end_date:
            if (
                self.compare_start_date > self.compare_end_date
                or (self.compare_end_date - self.compare_start_date).days >= 3660
            ):
                raise ValueError("Comparison windows must be ordered and contain at most 3660 days")
        if self.min_amount is not None and self.max_amount is not None:
            if self.min_amount > self.max_amount:
                raise ValueError("min_amount exceeds max_amount")
        return self
