import sys
from mcp.server.fastmcp import FastMCP
from client_mcp.server.tools_MBPP import tools_kit

mcp = FastMCP("mbpp_tools")
tools_kit(mcp)

if __name__ == "__main__":
    transport = "streamable-http" if "--http" in sys.argv else "stdio"
    mcp.run(transport=transport)
