from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from mcp_server import server

pytestmark = pytest.mark.unit


def test_default_paths_and_env_overrides(monkeypatch) -> None:
    monkeypatch.delenv("RADAR_DB_PATH", raising=False)
    monkeypatch.delenv("RADAR_SEARCH_DB_PATH", raising=False)
    assert server._db_path().as_posix() == "data/govradar_data.duckdb"
    assert server._search_db_path().as_posix() == "data/search_index.db"

    monkeypatch.setenv("RADAR_DB_PATH", "/tmp/custom.duckdb")
    monkeypatch.setenv("RADAR_SEARCH_DB_PATH", "/tmp/search.db")
    assert server._db_path().as_posix() == "/tmp/custom.duckdb"
    assert server._search_db_path().as_posix() == "/tmp/search.db"


def test_argument_coercion_helpers() -> None:
    assert server._as_int("12", 7) == 12
    assert server._as_int(True, 7) == 7
    assert server._as_int("bad", 7) == 7
    assert server._as_float("1.5", 0.0) == 1.5
    assert server._as_float(False, 2.0) == 2.0
    assert server._as_float("bad", 2.0) == 2.0
    assert server._coerce_args({"query": "지원", 3: "ignored"}) == {"query": "지원"}
    assert server._coerce_args(["not", "dict"]) == {}


def test_list_tool_specs_contains_expected_tools() -> None:
    specs = server._list_tool_specs()

    assert {spec["name"] for spec in specs} == {
        "search",
        "recent_updates",
        "sql",
        "top_trends",
        "price_watch",
    }
    assert specs[0]["inputSchema"]["required"] == ["query"]


def test_call_tool_handler_routes_to_each_handler(monkeypatch) -> None:
    monkeypatch.setattr(server, "handle_search", Mock(return_value="search ok"))
    monkeypatch.setattr(server, "handle_recent_updates", Mock(return_value="recent ok"))
    monkeypatch.setattr(server, "handle_sql", Mock(return_value="sql ok"))
    monkeypatch.setattr(server, "handle_top_trends", Mock(return_value="trends ok"))
    monkeypatch.setattr(server, "handle_price_watch", Mock(return_value="price ok"))

    assert server._call_tool_handler("search", {"query": "청년", "limit": "3"}) == "search ok"
    assert server._call_tool_handler("recent_updates", {"days": "2"}) == "recent ok"
    assert server._call_tool_handler("sql", {"query": "select 1"}) == "sql ok"
    assert server._call_tool_handler("top_trends", {"limit": "4"}) == "trends ok"
    assert server._call_tool_handler("price_watch", {"threshold": "5.5"}) == "price ok"
    assert server._call_tool_handler("missing", {}) == "Unknown tool: missing"

    server.handle_search.assert_called_once()
    server.handle_recent_updates.assert_called_once()
    server.handle_sql.assert_called_once()
    server.handle_top_trends.assert_called_once()
    server.handle_price_watch.assert_called_once_with(threshold=5.5)


class _FakeMcpApp:
    def __init__(self, name: str) -> None:
        self.name = name
        self._list_tools = None
        self._call_tool = None

    def list_tools(self):
        def decorator(func):
            self._list_tools = func
            return func

        return decorator

    def call_tool(self):
        def decorator(func):
            self._call_tool = func
            return func

        return decorator

    def create_initialization_options(self) -> object:
        return {"init": True}

    async def run(self, read_stream: object, write_stream: object, options: object) -> None:
        self.ran_with = (read_stream, write_stream, options)


class _FakeStdio:
    async def __aenter__(self) -> tuple[str, str]:
        return "reader", "writer"

    async def __aexit__(self, exc_type, exc_value, traceback) -> bool:
        return False


def test_create_app_registers_tools_and_call_handler(monkeypatch) -> None:
    fake_app = _FakeMcpApp("radar-template")

    def fake_import_module(name: str):
        if name == "mcp.server":
            return SimpleNamespace(Server=Mock(return_value=fake_app))
        if name == "mcp.types":
            return SimpleNamespace(
                Tool=lambda **kwargs: {"tool": kwargs},
                TextContent=lambda **kwargs: {"content": kwargs},
            )
        raise AssertionError(name)

    monkeypatch.setattr(server, "import_module", fake_import_module)
    monkeypatch.setattr(server, "_call_tool_handler", Mock(return_value="handled"))

    app = server.create_app()

    assert app is fake_app
    assert fake_app._list_tools is not None
    assert fake_app._call_tool is not None
    tools = asyncio.run(fake_app._list_tools())
    result = asyncio.run(fake_app._call_tool("search", {"query": "지원"}))
    assert tools[0]["tool"]["name"] == "search"
    assert result == [{"content": {"type": "text", "text": "handled"}}]


def test_main_runs_stdio_app(monkeypatch) -> None:
    fake_app = _FakeMcpApp("radar-template")
    fake_stdio = Mock(return_value=_FakeStdio())

    def fake_import_module(name: str):
        if name == "mcp.server.stdio":
            return SimpleNamespace(stdio_server=fake_stdio)
        raise AssertionError(name)

    monkeypatch.setattr(server, "create_app", Mock(return_value=fake_app))
    monkeypatch.setattr(server, "import_module", fake_import_module)

    asyncio.run(server.main())

    assert fake_stdio.called
    assert fake_app.ran_with == ("reader", "writer", {"init": True})
