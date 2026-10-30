import json

import httpx
import pytest
from mcp.server.fastmcp.exceptions import ToolError

from lifeos_mcp.client import LifeOSClient
from lifeos_mcp.config import Settings
from lifeos_mcp.server import create_server

EXPECTED = {
    "get_today",
    "get_data_freshness",
    "get_health_scores",
    "get_pulse_checkins",
    "list_transactions",
    "get_spending_analysis",
    "get_card_bills",
    "get_card_statement",
    "get_current_card_cycles",
    "get_budgets",
    "get_money_profile",
    "get_recurring_charges",
}


def structured(result):
    if isinstance(result, tuple):
        return result[1]
    if isinstance(result, dict):
        return result
    return json.loads(result[0].text)


async def test_catalog_is_curated_and_read_only():
    client = LifeOSClient(
        Settings(), httpx.MockTransport(lambda r: pytest.fail("Discovery fetched data"))
    )
    try:
        tools = await create_server(Settings(), client).list_tools()
        assert {t.name for t in tools} == EXPECTED
        assert all(t.annotations.readOnlyHint and not t.annotations.destructiveHint for t in tools)
        assert not {"health_records", "query_money"} & {t.name for t in tools}
    finally:
        await client.aclose()


async def test_transaction_truncation_is_explicit():
    rows = [{"id": i, "amount": "10.00"} for i in range(5)]
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json=rows)

    client = LifeOSClient(Settings(), httpx.MockTransport(handler))
    try:
        result = structured(
            await create_server(Settings(), client).call_tool(
                "list_transactions", {"days": 7, "source": "upi", "limit": 2}
            )
        )
        assert result["data"] == rows[:2]
        assert result["meta"]["truncated"] is True
        assert result["meta"]["fetched_count"] == 5
        assert result["meta"]["returned_count"] == 2
        assert dict(seen[0].url.params) == {"days": "7", "source": "upi"}
    finally:
        await client.aclose()


@pytest.mark.parametrize(
    "name,args",
    [
        ("get_health_scores", {"days": 0}),
        ("get_health_scores", {"days": True}),
        ("list_transactions", {"limit": 501}),
        ("get_card_statement", {"statement_id": "../sync"}),
        ("get_card_bills", {"months": 25}),
    ],
)
async def test_tool_validation_happens_before_network(name, args):
    client = LifeOSClient(
        Settings(), httpx.MockTransport(lambda r: pytest.fail("Invalid tool fetched data"))
    )
    try:
        with pytest.raises(ToolError):
            await create_server(Settings(), client).call_tool(name, args)
    finally:
        await client.aclose()


async def test_optional_reads_have_actual_schemas_and_use_post_only_for_the_bridge():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"window": {}, "summary": {"total": "12.34"}})

    settings = Settings(enable_agent_reads=True, agent_token="a" * 32)
    client = LifeOSClient(settings, httpx.MockTransport(handler))
    try:
        server = create_server(settings, client)
        tools = await server.list_tools()
        assert {t.name for t in tools} == EXPECTED | {"health_records", "query_money"}
        schema = next(t.inputSchema for t in tools if t.name == "query_money")
        assert "query" in schema["properties"]
        await server.call_tool("query_money", {"query": {"min_amount": "12.34", "limit": 1}})
        assert seen[0].method == "POST"
        assert seen[0].url.path == "/agent-reads/money-query"
        assert json.loads(seen[0].content)["min_amount"] == "12.34"
    finally:
        await client.aclose()


@pytest.mark.parametrize(
    "name,args,path,params",
    [
        ("get_today", {}, "/analytics/today", {}),
        ("get_data_freshness", {}, "/status/sync", {}),
        ("get_health_scores", {}, "/analytics/scores", {"days": "30"}),
        ("get_pulse_checkins", {}, "/mood", {"days": "30"}),
        ("get_spending_analysis", {}, "/statements/analysis", {"days": "45"}),
        ("get_card_bills", {}, "/statements", {"months": "3"}),
        ("get_card_statement", {"statement_id": 7}, "/statements/7/details", {}),
        ("get_current_card_cycles", {}, "/statements/cycles/current", {}),
        ("get_budgets", {}, "/budgets", {}),
        ("get_money_profile", {}, "/money/profile", {}),
        ("get_recurring_charges", {}, "/expenses/recurring", {"window_days": "180"}),
    ],
)
async def test_tools_route_to_the_existing_api_contract(name, args, path, params):
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"recorded": None})

    client = LifeOSClient(Settings(), httpx.MockTransport(handler))
    try:
        result = structured(await create_server(Settings(), client).call_tool(name, args))
        assert result["data"] == {"recorded": None}
        assert seen[0].method == "GET"
        assert seen[0].url.path == path
        assert dict(seen[0].url.params) == params
    finally:
        await client.aclose()
