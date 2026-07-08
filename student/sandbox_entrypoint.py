import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_cli import main as agent_cli_main  # noqa: E402


def main() -> None:
    raise SystemExit(agent_cli_main("sandbox"))


if __name__ == "__main__":
    main()
