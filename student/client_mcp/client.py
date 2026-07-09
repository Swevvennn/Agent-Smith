from typing import Any
from contextlib import AsyncExitStack

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.client.stdio import stdio_client, StdioServerParameters


class MCPClient:

    def __init__(self):
        self.session: ClientSession | None = None
        self._exit_stack = AsyncExitStack()

    async def connect_http(self, url: str) -> None:
        read, write, _ = await self._exit_stack.enter_async_context(
            streamable_http_client(url)
        )
        self.session = await self._exit_stack.enter_async_context(
            ClientSession(read, write)
        )
        await self.session.initialize()

    async def connect_stdio(self, command: str) -> None:
        import os
        parts = command.split()
        # By default, the MCP SDK only forwards HOME/PATH/TERM to the
        # spawned subprocess (for security). We need our custom env vars
        # (SWEBENCH_CONTAINER, SWEBENCH_EVAL_SCRIPT, API keys, ...) to
        # reach it, so we pass the full parent environment explicitly.
        params = StdioServerParameters(
            command=parts[0], args=parts[1:], env=os.environ.copy()
        )
        read, write = await self._exit_stack.enter_async_context(
            stdio_client(params)
        )
        self.session = await self._exit_stack.enter_async_context(
            ClientSession(read, write)
        )
        await self.session.initialize()

    async def list_tools(self) -> list[dict]:
        if not self.session:
            raise RuntimeError("Client not connected")
        result = await self.session.list_tools()
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.inputSchema,
            }
            for t in result.tools
        ]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        if not self.session:
            raise RuntimeError("Client not connected")
        result = await self.session.call_tool(name, arguments)
        return result.content

    async def disconnect(self) -> None:
        await self._exit_stack.aclose()
        self.session = None

    async def __aenter__(self):
        await self._exit_stack.__aenter__()
        return self

    async def __aexit__(self, *args):
        await self._exit_stack.__aexit__(*args)
        self.session = None
