import json

from starlette.testclient import TestClient

from kitconc.agent.dashboard import build_dashboard


def test_dashboard_serves_catalog_and_calls_tools(tmp_path):
    app = build_dashboard(str(tmp_path), read_only=True)
    headers = {"Accept": "application/json, text/event-stream"}

    with TestClient(app, base_url="http://127.0.0.1:8787") as client:
        page = client.get("/")
        assert page.status_code == 200
        assert "Kitconc · MCP tools" in page.text
        assert client.get("/", headers={"Host": "external.example"}).status_code == 400

        def rpc(method, params):
            response = client.post("/mcp", headers=headers, json={
                "jsonrpc": "2.0", "id": 1, "method": method, "params": params,
            })
            assert response.status_code == 200, response.text
            return response.json()["result"]

        init = rpc("initialize", {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "dashboard-test", "version": "1"},
        })
        headers["MCP-Protocol-Version"] = init["protocolVersion"]
        tools = rpc("tools/list", {})["tools"]
        assert "workspace_info" in {tool["name"] for tool in tools}
        assert all(tool["annotations"]["readOnlyHint"] for tool in tools)
        result = rpc("tools/call", {"name": "workspace_info", "arguments": {}})
        assert not result["isError"]
        assert json.loads(result["content"][0]["text"])["corpora"] == []
