# -*- coding: utf-8 -*-
"""Regression tests for the Kitconc MCP server tool registration."""

import asyncio
import re
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from kitconc.agent.mcp_server import build_server


def test_build_server_registers_tool_schema_without_kwargs_field():
    async def _run():
        server = build_server()
        tools = await server.list_tools()
        app_version = next(tool for tool in tools if tool.name == "app_version")
        assert "kwargs" not in app_version.inputSchema.get("properties", {})
        assert "kwargs" not in app_version.inputSchema.get("required", [])

    asyncio.run(_run())


def test_call_tool_app_version_via_fastmcp_server():
    async def _run():
        server = build_server()
        result = await server.call_tool("app_version", {})
        assert result
        assert hasattr(result[0], "text")
        assert re.match(r"^\d+\.\d+\.\d+$", result[0].text)

    asyncio.run(_run())


def test_call_tool_via_stdio_transport():
    async def _run():
        params = StdioServerParameters(
            command="./venv/bin/kitconc-mcp",
            args=["--transport", "stdio"],
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("app_version", {})
                assert result.content
                assert re.match(r"^\d+\.\d+\.\d+$", result.content[0].text)

    asyncio.run(_run())


def test_call_tool_workspace_with_arguments(tmp_path):
    async def _run():
        server = build_server()
        new_workspace = str((Path(tmp_path) / "mcp_ws").resolve())
        result = await server.call_tool("workspace", {"path": new_workspace})
        assert result
        assert hasattr(result[0], "text")
        assert result[0].text == new_workspace
        assert Path(new_workspace).exists()

    asyncio.run(_run())
