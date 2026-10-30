import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import anyio
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.fixture
def synthetic_api():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = json.dumps({"synthetic": True, "sources": []}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


async def test_real_stdio_discovery_call_and_validation(synthetic_api):
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "lifeos_mcp"],
        env={"LIFEOS_API_BASE_URL": synthetic_api, "LIFEOS_ENABLE_AGENT_READS": "false"},
    )
    with anyio.fail_after(20):
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                initialized = await session.initialize()
                assert initialized.serverInfo.name == "LifeOS"
                tools = await session.list_tools()
                assert len(tools.tools) == 38
                assert all(t.annotations.readOnlyHint for t in tools.tools)
                result = await session.call_tool("get_data_freshness", {})
                assert not result.isError
                assert result.structuredContent["data"]["synthetic"] is True
                invalid = await session.call_tool("get_health_scores", {"days": 0})
                assert invalid.isError
                unknown = await session.call_tool("delete_everything", {})
                assert unknown.isError
