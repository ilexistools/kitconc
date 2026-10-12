# -*- coding: utf-8 -*-
"""Regression tests for the Kitconc MCP server tool registration."""

import asyncio
import json
import re
import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.memory import create_connected_server_and_client_session

from kitconc.agent.mcp_server import build_server
from kitconc.agent.tools import DEFAULT_PAGE_SIZE, TOOL_SPECS
from kitconc.kit_corpus import Corpus


# ---------------------------------------------------------------------------
# Legacy tool set
# ---------------------------------------------------------------------------


def test_build_server_registers_tool_schema_without_kwargs_field():
    async def _run():
        server = build_server(tool_set="legacy")
        tools = await server.list_tools()
        app_version = next(tool for tool in tools if tool.name == "app_version")
        assert "kwargs" not in app_version.inputSchema.get("properties", {})
        assert "kwargs" not in app_version.inputSchema.get("required", [])

    asyncio.run(_run())


def test_call_tool_app_version_via_fastmcp_server():
    async def _run():
        server = build_server(tool_set="legacy")
        result = await server.call_tool("app_version", {})
        assert result
        assert hasattr(result[0], "text")
        assert re.match(r"^\d+\.\d+\.\d+$", result[0].text)

    asyncio.run(_run())


def test_call_tool_workspace_with_arguments(tmp_path):
    async def _run():
        server = build_server(tool_set="legacy")
        new_workspace = str((Path(tmp_path) / "mcp_ws").resolve())
        result = await server.call_tool("workspace", {"path": new_workspace})
        assert result
        assert hasattr(result[0], "text")
        assert result[0].text == new_workspace
        assert Path(new_workspace).exists()

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# Curated tool set
# ---------------------------------------------------------------------------

TEXTS = {
    "t1.txt": "The new model is working well . The new model is fast .",
    "t2.txt": "A new idea is working . We like the idea of the new model .",
    "t3.txt": "Teachers are teaching new students in the new school .",
}


@pytest.fixture(scope="module")
def workspace(tmp_path_factory):
    base = tmp_path_factory.mktemp("mcp_curated")
    src = base / "src"
    src.mkdir()
    for filename, text in TEXTS.items():
        (src / filename).write_text(text, encoding="utf-8")
    Corpus(str(base / "ws"), "demo", "no-tagging").add_texts(str(src))
    return str(base / "ws")


def _run_session(workspace, scenario, **server_kwargs):
    async def _run():
        server = build_server(workspace=workspace, **server_kwargs)
        async with create_connected_server_and_client_session(server._mcp_server) as session:
            async def call(name, arguments=None):
                result = await session.call_tool(name, arguments or {})
                return result.isError, json.loads(result.content[0].text)

            return await scenario(session, call)

    return asyncio.run(_run())


def test_call_tool_via_stdio_transport(workspace):
    async def _run():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "kitconc.agent.mcp_server", "--transport", "stdio", "--workspace", workspace],
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                init = await session.initialize()
                assert "result_id" in (init.instructions or "")
                result = await session.call_tool("workspace_info", {})
                assert not result.isError
                payload = json.loads(result.content[0].text)
                assert re.match(r"^\d+\.\d+\.\d+$", payload["version"])
                assert [c["id"] for c in payload["corpora"]] == ["demo"]

    asyncio.run(_run())


def test_curated_catalog_is_described_and_annotated(workspace):
    async def scenario(session, call):
        return (await session.list_tools()).tools

    tools = _run_session(workspace, scenario)
    names = {tool.name for tool in tools}
    assert names == {spec.name for spec in TOOL_SPECS}
    assert "app_version" not in names and "create_typed" not in names
    for tool in tools:
        assert tool.description and not tool.description.startswith("Execute action")
        assert tool.annotations is not None
        assert "kwargs" not in tool.inputSchema.get("properties", {})
    delete = next(tool for tool in tools if tool.name == "corpus_delete")
    assert delete.annotations.destructiveHint is True
    collocates = next(tool for tool in tools if tool.name == "analyze_collocates")
    assert "mutual information" in collocates.inputSchema["properties"]["measure"]["enum"]
    assert collocates.inputSchema["properties"]["corpus"]["description"]


def test_read_only_mode_hides_writing_tools(workspace):
    async def scenario(session, call):
        return {tool.name for tool in (await session.list_tools()).tools}

    names = _run_session(workspace, scenario, read_only=True)
    assert "analyze_kwic" in names and "result_page" in names
    assert not names & {"corpus_delete", "corpus_create", "result_export", "workspace_set"}


def test_analysis_is_paged_and_stored(workspace):
    async def scenario(session, call):
        error, first = await call("analyze_wordlist", {"corpus": "demo", "limit": 2})
        assert not error
        _, page = await call("result_page", {"result_id": first["result_id"], "offset": 2, "limit": 2,
                                             "format": "records"})
        _, sorted_page = await call("result_page", {"result_id": first["result_id"], "sort_by": "WORD",
                                                    "descending": False, "fields": ["WORD"], "limit": 1})
        return first, page, sorted_page

    first, page, sorted_page = _run_session(workspace, scenario)
    assert first["returned"] == 2 and first["next_offset"] == 2
    assert first["total"] > 2
    assert first["columns"][:3] == ["N", "WORD", "FREQUENCY"]
    assert isinstance(first["rows"][0], list)
    assert page["offset"] == 2 and isinstance(page["rows"][0], dict)
    assert sorted_page["columns"] == ["WORD"]
    assert sorted_page["rows"] == [["a"]]


def test_analysis_default_limit(workspace):
    async def scenario(session, call):
        return await call("analyze_kwic", {"corpus": "demo", "node": "new"})

    error, payload = _run_session(workspace, scenario)
    assert not error
    assert payload["total"] == 6
    assert payload["returned"] == min(6, DEFAULT_PAGE_SIZE)
    assert payload["next_offset"] is None


def test_result_export_writes_all_rows(workspace, tmp_path):
    target = tmp_path / "out" / "words.tsv"

    async def scenario(session, call):
        _, first = await call("analyze_wordlist", {"corpus": "demo", "limit": 1})
        return first, await call("result_export", {"result_id": first["result_id"], "output_path": str(target)})

    first, (error, exported) = _run_session(workspace, scenario)
    assert not error
    assert exported["rows_written"] == first["total"]
    assert target.exists()


def test_structured_errors(workspace):
    async def scenario(session, call):
        return (
            await call("analyze_kwic", {"corpus": "missing", "node": "new"}),
            await call("result_page", {"result_id": "nope"}),
            await call("corpus_delete", {"corpus": "demo"}),
        )

    (e1, missing), (e2, no_result), (e3, delete) = _run_session(workspace, scenario)
    assert e1 and missing["error"]["code"] == "CORPUS_NOT_FOUND"
    assert missing["error"]["candidates"] == ["demo"]
    assert e2 and no_result["error"]["code"] == "RESULT_NOT_FOUND"
    assert e3 and delete["error"]["code"] == "CONFIRMATION_REQUIRED"


def test_corpus_files_and_read_file(workspace):
    async def scenario(session, call):
        _, files = await call("corpus_files", {"corpus": "demo"})
        _, text = await call("corpus_read_file", {"corpus": "demo", "filename": files["files"][0], "node": "new"})
        return files, text

    files, text = _run_session(workspace, scenario)
    assert files["files"] == sorted(TEXTS)
    assert text["hits"] == 2
    assert "[[new]]" in text["text"].lower()


def test_results_outlive_memory_cache_via_disk(workspace):
    async def scenario(session, call):
        _, first = await call("analyze_wordlist", {"corpus": "demo", "limit": 1})
        await call("analyze_ngrams", {"corpus": "demo", "size": 2, "limit": 1})
        await call("analyze_ngrams", {"corpus": "demo", "size": 3, "limit": 1})
        return first, await call("result_page", {"result_id": first["result_id"], "limit": 1})

    first, (error, payload) = _run_session(workspace, scenario, result_capacity=1)
    assert not error and payload["total"] == first["total"]


def test_results_are_pruned_beyond_disk_capacity(tmp_path):
    ws = tmp_path / "ws"
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_text("one two three two one .", encoding="utf-8")
    Corpus(str(ws), "tiny", "no-tagging").add_texts(str(src))

    async def scenario(session, call):
        _, first = await call("analyze_wordlist", {"corpus": "tiny", "limit": 1})
        for size in (2, 3, 1):
            await call("analyze_ngrams", {"corpus": "tiny", "size": size, "limit": 1})
        return await call("result_page", {"result_id": first["result_id"]})

    error, payload = _run_session(str(ws), scenario, result_capacity=1, disk_capacity=2)
    assert error and payload["error"]["code"] == "RESULT_NOT_FOUND"
