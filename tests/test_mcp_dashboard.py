import json

from starlette.testclient import TestClient

from kitconc.agent.dashboard import build_dashboard


def test_dashboard_serves_catalog_and_calls_tools(tmp_path):
    app = build_dashboard(str(tmp_path), read_only=True)
    headers = {"Accept": "application/json, text/event-stream"}

    with TestClient(app, base_url="http://127.0.0.1:8787") as client:
        page = client.get("/")
        assert page.status_code == 200
        assert "Kitconc · MCP Console" in page.text
        assert 'data-theme="dark"' in page.text
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


def test_dashboard_rest_api(tmp_path):
    app = build_dashboard(str(tmp_path), read_only=True)

    with TestClient(app, base_url="http://127.0.0.1:8787") as client:
        info = client.get("/api/info").json()
        assert info["read_only"] is True
        assert info["endpoints"] == {"streamable_http": "/mcp", "sse": "/sse", "rest": "/api"}
        assert info["commands"]["stdio"][-1] == "--read-only"
        assert info["tool_count"] > 0

        catalog = client.get("/api/tools").json()["tools"]
        groups = {tool["name"]: tool["group"] for tool in catalog}
        assert groups["workspace_info"] == "workspace"
        assert groups["analyze_kwic"] == "analysis"
        assert "corpus_delete" not in groups  # read-only catalog

        assert client.get("/api/tools/analyze_kwic").json()["name"] == "analyze_kwic"
        assert client.get("/api/tools/nope").status_code == 404

        ok = client.post("/api/tools/workspace_info", json={})
        assert ok.status_code == 200
        assert ok.json()["corpora"] == []

        failed = client.post("/api/tools/corpus_info", json={"corpus": "missing"})
        assert failed.status_code == 422

        assert client.post("/api/tools/workspace_info", content="{}",
                           headers={"Content-Type": "text/plain"}).status_code == 415
        assert client.post("/api/tools/workspace_info", content="[1]",
                           headers={"Content-Type": "application/json"}).status_code == 400
        assert client.post("/api/tools/corpus_delete", json={}).status_code == 404


def test_dashboard_exposes_sse_transport(tmp_path):
    app = build_dashboard(str(tmp_path), read_only=True)
    paths = {getattr(route, "path", None) for route in app.router.routes}
    assert {"/mcp", "/sse", "/messages"} <= paths
