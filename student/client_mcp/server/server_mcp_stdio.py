from mcp.server.fastmcp import FastMCP
from student.client_mcp.server.tools_SWE_bench import tools_kit


mcp = FastMCP("my_mcp")
tools_kit(mcp)

if __name__ == "__main__":
    mcp.run(transport="stdio")
