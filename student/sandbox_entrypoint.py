"""
Point d'entree pour la commande `uv run sandbox`.

Le reste du code (agent_cli.py, sandbox/sandbox.py, client_mcp/bridge.py)
utilise des imports "nus" (ex: `from sandbox.sandbox import run_code`),
qui ne fonctionnent que si le dossier `student/` est sur sys.path.
Ce fichier ajoute `student/` a sys.path avant d'importer quoi que ce
soit d'autre, pour que `uv run sandbox` fonctionne peu importe le
repertoire depuis lequel il est appele.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_cli import main as agent_cli_main  # noqa: E402


def main() -> None:
    raise SystemExit(agent_cli_main("sandbox"))


if __name__ == "__main__":
    main()
