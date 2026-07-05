import asyncio
import threading
from typing import Any

from student.client_mcp.client import MCPClient


class SyncMCPClient:
    def __init__(self, command: str = "", mcp_type: str = "stdio", url: str = ""):
        self.command = command

        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.run_loop, daemon=True)
        self.thread.start()

        self.client = MCPClient()

        if mcp_type == "stdio":
            self.run(self.client.connect_stdio(self.command))
        elif mcp_type == "http" and url:
            self.run(self.client.connect_http(url))
        else:
            raise ValueError(
                f"Invalid MCP config: mcp_type={mcp_type!r}, url={url!r}"
            )

    def run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result()

    def list_tools(self):
        return self.run(self.client.list_tools())

    def call_tool(self, name, args):
        return self.run(self.client.call_tool(name, args))

    def disconnect(self):
        future = asyncio.run_coroutine_threadsafe(
            self._safe_disconnect(),
            self.loop,
        )
        future.result()
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()

    def close(self):
        self.disconnect()

    async def _safe_disconnect(self):
        try:
            await self.client.disconnect()
        except Exception:
            pass


def parse_tools(tools: Any):
    if isinstance(tools, str):
        return tools
    if isinstance(tools, list):
        parts = []
        for block in tools:
            text = getattr(block, "text", None)
            parts.append(text if text is not None else str(block))
        return "\n".join(parts)
    return str(tools)


def make_wrappers_tools(syclient: SyncMCPClient):
    wrappers = {}
    for tool in syclient.list_tools():
        wrappers[tool["name"]] = make_wrapper(syclient, tool["name"])
    return wrappers


def make_wrapper(syclient: SyncMCPClient, tool_name):
    def wrapper(**kwargs):
        result = syclient.call_tool(tool_name, kwargs)
        return parse_tools(result)

    wrapper.__name__ = tool_name
    return wrapper
