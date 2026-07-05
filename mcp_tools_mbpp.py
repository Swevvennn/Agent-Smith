from mcp.server.fastmcp import FastMCP
from student.client_mcp.server.tools_MBPP import tools_kit


mcp = FastMCP("mbpp_tools")
tools_kit(mcp)


if __name__ == "__main__":
    mcp.run(transport="stdio")