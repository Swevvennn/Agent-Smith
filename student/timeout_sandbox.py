from sandbox.sandbox import run_code
from sandbox.sandbox_config import SandboxConfig
config = SandboxConfig()

print("=== Test timeout (boucle infinie) ===")
r = run_code("while True: pass", config)
print("timed_out:", r.get("timed_out"), "| success:", r["success"])

print()
print("=== Test memoire (grosse allocation) ===")
r = run_code("x = [0] * (10**9)", config)
print("success:", r["success"], "| output:", str(r["output"])[:80])
