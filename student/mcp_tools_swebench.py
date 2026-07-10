# MCP tools file pour la moulinette, posez pas trop de question, sachez juste que ca marche

import sys
from mcp.server.fastmcp import FastMCP
from client_mcp.server.tools_SWE_bench import tools_kit

mcp = FastMCP("swebench_tools")
tools_kit(mcp)

if __name__ == "__main__":
    try:
        transport = "streamable-http" if "--http" in sys.argv else "stdio"
        mcp.run(transport=transport)
    except (KeyboardInterrupt, Exception) as e:
        print("ERROR:", e)
