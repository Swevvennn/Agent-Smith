import json
import os
from dotenv import load_dotenv

# gestion d'errueur a revoir ici pas assez robuste

def load_task(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def load_api(env_key):
    load_dotenv()
    api_key = os.getenv(env_key)
    if not api_key:
        print('Something went wrong (api key loader)')
    return api_key


def load_mcp(mcp: str):
    available_mcp = ["stdio", "http"]
    if not mcp:
        raise ValueError("Something went wrong (loading mcp server got none)")
    if mcp not in available_mcp:
        raise ValueError(f"Something went wrong (loading mcp server got {mcp} available {available_mcp})")

    from student.client_mcp import bridge

    if mcp == "stdio":
        # probleme pour le moment les servers se lance toujours avec le meme tools kits (SWE_BENCH)
        client = bridge.SyncMCPClient(command="python3 -m student.client_mcp.server.server_mcp_stdio")
    else:
        client = bridge.SyncMCPClient(command="python3 -m student.client_mcp.server.server_mcp_http")
    return client


def main():
    "la loop agent a faire pour le mbpp"
    pass