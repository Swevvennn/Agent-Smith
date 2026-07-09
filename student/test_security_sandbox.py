from sandbox.sandbox import run_code
from sandbox.sandbox_config import SandboxConfig
config = SandboxConfig()

tests = [
    ("1. Import bloque (os)",        "import os"),
    ("2. Import bloque (sys)",       "import sys"),
    ("3. Import bloque (subprocess)", "import subprocess"),
    ("4. Builtin bloque (eval)",     "eval('1+1')"),
    ("5. Builtin bloque (exec)",     "exec('x=1')"),
    ("6. Builtin bloque (__import__)", "__import__('os')"),
    ("7. Path restreint",            "open('/etc/passwd').read()"),
    ("8. Import autorise (math)",    "import math; print(math.pi)"),
]

for label, code in tests:
    r = run_code(code, config)
    ok = r["success"]
    out = str(r["output"])[:55].replace("\n", " ")
    expected_block = not label.startswith("8")
    if expected_block and not ok:
        verdict = "BLOQUE OK"
    elif not expected_block and ok:
        verdict = "AUTORISE OK"
    else:
        verdict = "!!! PROBLEME !!!"
    print(f"{label:35} {verdict:18} {out}")
