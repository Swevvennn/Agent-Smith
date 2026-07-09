import sys
from mcp.server.fastmcp import FastMCP
from student.client_mcp.server.tools_SWE_bench import tools_kit

mcp = FastMCP("swebench_tools")
tools_kit(mcp)

if __name__ == "__main__":
    try:
        transport = "streamable-http" if "--http" in sys.argv else "stdio"
        mcp.run(transport=transport)
    except (KeyboardInterrupt, Exception) as e:
        print("ERROR:", e)
