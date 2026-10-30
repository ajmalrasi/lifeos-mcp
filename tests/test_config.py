import pytest
from pydantic import ValidationError

from lifeos_mcp.config import Settings
from lifeos_mcp.contracts import HealthQuery, MoneyQuery


@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.test",
        "http://user:password@example.test",
        "http://example.test/api",
        "http://example.test?token=x",
        "http://example.test#x",
        "http://",
        "http://x:99999",
    ],
)
def test_config_rejects_non_origin_urls(url):
    with pytest.raises(ValidationError):
        Settings(api_base_url=url)


def test_secrets_are_redacted_and_url_normalized():
    settings = Settings(api_base_url="https://example.test/", api_token="private-test-value")
    assert settings.api_base_url == "https://example.test"
    assert "private-test-value" not in repr(settings)


@pytest.mark.parametrize(
    "payload",
    [
        {"days": 0},
        {"days": True},
        {"days": 91},
        {"sql": "select 1"},
        {"start_date": "2025-09-03", "end_date": "2025-09-01"},
        {"start_date": "2025-01-01", "end_date": "2025-09-01"},
    ],
)
def test_health_contract_rejects_invalid_arguments(payload):
    with pytest.raises(ValidationError):
        HealthQuery(**payload)


def test_health_end_only_resolves_both_dates():
    query = HealthQuery(days=3, end_date="2025-09-03")
    assert query.model_dump(mode="json") == {
        "days": 3,
        "start_date": "2025-09-01",
        "end_date": "2025-09-03",
    }


@pytest.mark.parametrize(
    "payload",
    [
        {"sql": "drop table transactions"},
        {"mode": "sql"},
        {"limit": 51},
        {"limit": True},
        {"min_amount": "NaN"},
        {"max_amount": "Infinity"},
        {"compare_start_date": "2025-09-01"},
        {"start_date": "2025-10-01", "end_date": "2025-09-01"},
        {"min_amount": "20", "max_amount": "10"},
    ],
)
def test_money_contract_is_guarded(payload):
    with pytest.raises(ValidationError):
        MoneyQuery(**payload)


def test_money_amount_keeps_decimal_precision():
    query = MoneyQuery(min_amount="123.45")
    assert query.model_dump(mode="json")["min_amount"] == "123.45"
