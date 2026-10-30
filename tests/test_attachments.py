import base64
import hashlib
import json

import httpx
import pytest
from mcp.types import CallToolResult

from lifeos_mcp.client import LifeOSClient, LifeOSError
from lifeos_mcp.config import Settings
from lifeos_mcp.server import create_server


async def test_attachment_returns_the_original_bytes_as_an_embedded_resource():
    original = b"%PDF-1.4\nsynthetic test document\n"
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, content=original, headers={"Content-Type": "application/pdf"})

    client = LifeOSClient(Settings(), httpx.MockTransport(handler))
    try:
        result = await create_server(Settings(), client).call_tool(
            "get_trip_attachment", {"trip_id": "synthetic-trip", "attachment_id": "document-1"}
        )
        assert isinstance(result, CallToolResult)
        resource = result.content[1].resource
        assert base64.b64decode(resource.blob) == original
        assert resource.mimeType == "application/pdf"
        info = json.loads(result.content[0].text)
        assert info["data"]["sha256"] == hashlib.sha256(original).hexdigest()
        assert info["data"]["size_bytes"] == len(original)
        assert seen[0].url.path == "/trips/synthetic-trip/attachments/document-1"
    finally:
        await client.aclose()


async def test_large_attachment_fails_without_a_partial_success():
    client = LifeOSClient(
        Settings(max_response_bytes=1024),
        httpx.MockTransport(lambda r: httpx.Response(200, content=b"x" * 1025)),
    )
    try:
        with pytest.raises(LifeOSError, match="too large"):
            await client.attachment("trip", "attachment")
    finally:
        await client.aclose()


@pytest.mark.parametrize(
    "trip_id,attachment_id",
    [
        ("../private", "ok"),
        ("ok", "x%2Fy"),
        ("https://other.test", "ok"),
    ],
)
async def test_attachment_identifiers_cannot_redirect_or_traverse(trip_id, attachment_id):
    client = LifeOSClient(Settings(), httpx.MockTransport(lambda r: pytest.fail("Unsafe request")))
    try:
        with pytest.raises(LifeOSError):
            await client.attachment(trip_id, attachment_id)
    finally:
        await client.aclose()
