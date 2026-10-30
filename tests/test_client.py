import httpx
import pytest

from lifeos_mcp.client import LifeOSClient, LifeOSError
from lifeos_mcp.config import Settings


async def test_native_reads_use_normal_api_auth_and_values_pass_through():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"amount": "123.45", "currency": "INR", "missing": None})

    client = LifeOSClient(
        Settings(
            api_base_url="https://lifeos.test",
            api_token="main-token",
        ),
        httpx.MockTransport(handler),
    )
    try:
        normal = await client.read("profile")
        await client.query_money({"limit": 1})
        assert seen[0].url.path == "/money/profile"
        assert seen[0].headers["Authorization"] == "Bearer main-token"
        assert seen[1].url.path == "/expenses/query"
        assert seen[1].headers["Authorization"] == "Bearer main-token"
        assert normal["data"] == {"amount": "123.45", "currency": "INR", "missing": None}
        assert normal["meta"]["timezone"] == "Asia/Kolkata"
        assert normal["meta"]["retrieved_at"]
    finally:
        await client.aclose()


@pytest.mark.parametrize("route", ["/expenses/sync", "https://attacker.test", "rebuild", "unknown"])
async def test_unknown_routes_never_make_requests(route):
    def handler(request):
        pytest.fail("Blocked route attempted network access")

    client = LifeOSClient(Settings(), httpx.MockTransport(handler))
    try:
        with pytest.raises(LifeOSError, match="Unsupported"):
            await client.read(route)
    finally:
        await client.aclose()


async def test_private_request_primitive_cannot_write():
    client = LifeOSClient(Settings(), httpx.MockTransport(lambda r: pytest.fail("write attempted")))
    try:
        with pytest.raises(LifeOSError):
            await client._request("DELETE", "/movement")
        with pytest.raises(LifeOSError):
            await client._request("POST", "/expenses/rebuild-llm")
        with pytest.raises(LifeOSError):
            await client._request("POST", "/agent-reads/money-query")
        with pytest.raises(LifeOSError):
            await client.statement("../sync")
        with pytest.raises(LifeOSError):
            await client._request("GET", "/mail/accounts")
        with pytest.raises(LifeOSError):
            await client.read_path("priority_message", item_id=True)
    finally:
        await client.aclose()


@pytest.mark.parametrize("status", [302, 401, 403, 404, 429, 500])
async def test_errors_do_not_echo_sensitive_bodies_or_follow_redirects(status):
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(
            status, text="private-health-and-token", headers={"Location": "https://attacker.test"}
        )

    client = LifeOSClient(Settings(), httpx.MockTransport(handler))
    try:
        with pytest.raises(LifeOSError) as error:
            await client.read("today")
        assert "private-health-and-token" not in str(error.value)
        assert len(seen) == 1
    finally:
        await client.aclose()


@pytest.mark.parametrize("body", [b"not json", b"42", b"null", b'{"error":"private-value"}'])
async def test_bad_data_is_an_error_not_a_success(body):
    client = LifeOSClient(
        Settings(), httpx.MockTransport(lambda r: httpx.Response(200, content=body))
    )
    try:
        with pytest.raises(LifeOSError) as error:
            await client.read("profile")
        assert "private-value" not in str(error.value)
    finally:
        await client.aclose()


async def test_response_limit_is_enforced():
    client = LifeOSClient(
        Settings(max_response_bytes=1024),
        httpx.MockTransport(lambda r: httpx.Response(200, content=b"x" * 1025)),
    )
    try:
        with pytest.raises(LifeOSError, match="too large"):
            await client.read("transactions")
    finally:
        await client.aclose()


@pytest.mark.parametrize(
    "exception", [httpx.ReadTimeout("secret-url"), httpx.ConnectError("secret-url")]
)
async def test_network_errors_are_sanitized(exception):
    def handler(request):
        raise exception

    client = LifeOSClient(Settings(), httpx.MockTransport(handler))
    try:
        with pytest.raises(LifeOSError) as error:
            await client.read("freshness")
        assert "secret-url" not in str(error.value)
    finally:
        await client.aclose()
