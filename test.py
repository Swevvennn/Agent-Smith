
from student.client_mcp.bridge import SyncMCPClient, make_wrappers_tools

client = SyncMCPClient(command="inutile en http", mcp_type="http", url="http://127.0.0.1:8000/mcp")

print("Tools:", [t["name"] for t in client.list_tools()])

wrappers = make_wrappers_tools(client)
namespace = {}
namespace.update(wrappers)

exec('print(run_command(command="pwd", workdir="/home/erifflar/TOUCH/Projet_42/Agent-Smith"))', namespace)

client.disconnect()
print("OK - le pont fonctionne")
