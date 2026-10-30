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
    "get_pulse_checkin",
    "list_new_transactions",
    "get_repayment_candidates",
    "get_current_card_cycle",
    "get_spending_trends",
    "list_payee_rules",
    "preview_payee_category",
    "get_payee_match_types",
    "list_priority_items",
    "get_priority_item",
    "get_priority_message",
    "get_health_score",
    "get_life_states",
    "get_correlations",
    "get_insights",
    "get_weekly_recap",
    "get_ask_suggestions",
    "get_model_health",
    "get_notifications",
    "list_trips",
    "get_trip",
    "get_trip_attachment",
    "get_movement",
    "get_coding_activity",
    "get_api_info",
    "get_api_health",
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
        ("get_trip", {"trip_id": "../mail/accounts"}),
        ("get_trip_attachment", {"trip_id": "valid", "attachment_id": "x%2Fy"}),
        ("get_current_card_cycle", {"bank": "HDFC/../sync", "card_last4": "1234"}),
        ("get_priority_item", {"item_id": 0}),
        ("get_movement", {"start_date": "2025-09-03", "end_date": "2025-09-01"}),
        ("get_movement", {"start_date": "2020-01-01", "end_date": "2025-09-01"}),
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
        ("get_pulse_checkin", {"day": "2025-09-02"}, "/mood/2025-09-02", {}),
        (
            "get_repayment_candidates",
            {"transaction_id": 8},
            "/expenses/8/repayment-candidates",
            {"window_days": "120"},
        ),
        (
            "get_current_card_cycle",
            {"bank": "SBI", "card_last4": "12"},
            "/statements/cycles/current/SBI/12",
            {},
        ),
        ("get_spending_trends", {}, "/statements/trends", {"months": "6"}),
        ("list_payee_rules", {}, "/payee-labels", {}),
        (
            "preview_payee_category",
            {"desc": "Synthetic shop"},
            "/payee-labels/preview",
            {"desc": "Synthetic shop"},
        ),
        ("get_payee_match_types", {}, "/payee-labels/match-types", {}),
        (
            "list_priority_items",
            {"label": "job", "state": "done", "include_done": True, "limit": 7},
            "/priority",
            {"label": "job", "state": "done", "include_done": "true", "limit": "7"},
        ),
        ("get_priority_item", {"item_id": 9}, "/priority/9", {}),
        ("get_priority_message", {"item_id": 9}, "/priority/9/message", {}),
        ("get_health_score", {"day": "2025-09-02"}, "/analytics/scores/2025-09-02", {}),
        ("get_life_states", {}, "/analytics/state", {"days": "30"}),
        ("get_correlations", {}, "/analytics/insights", {}),
        ("get_insights", {}, "/analytics/synthesis", {}),
        ("get_weekly_recap", {}, "/analytics/weekly-recap", {}),
        ("get_ask_suggestions", {}, "/chat/suggestions", {"days": "30"}),
        ("get_model_health", {}, "/chat/health", {}),
        ("get_notifications", {}, "/notifications", {}),
        ("list_trips", {}, "/trips", {}),
        ("get_trip", {"trip_id": "synthetic-trip"}, "/trips/synthetic-trip", {}),
        (
            "get_movement",
            {"start_date": "2025-09-01", "end_date": "2025-09-03"},
            "/movement/days",
            {"start": "2025-09-01", "end": "2025-09-03"},
        ),
        ("get_coding_activity", {}, "/github", {"days": "30"}),
        ("get_api_info", {}, "/", {}),
        ("get_api_health", {}, "/healthz", {}),
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


async def test_new_transaction_cursor_reports_possible_further_pages():
    client = LifeOSClient(
        Settings(),
        httpx.MockTransport(lambda r: httpx.Response(200, json=[{"id": 11}, {"id": 12}])),
    )
    try:
        result = structured(
            await create_server(Settings(), client).call_tool(
                "list_new_transactions", {"after_id": 10, "limit": 2}
            )
        )
        assert result["data"] == [{"id": 11}, {"id": 12}]
        assert result["meta"]["may_have_more"] is True
    finally:
        await client.aclose()
