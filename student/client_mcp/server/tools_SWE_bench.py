from pathlib import Path
from typing import Dict, List, Any
import subprocess
import fnmatch
import re


## MESSAGE D'ERREUR A REVOIR ICI POUR LES TOOLS KIT J'ATTEND D'AVANCER UN PEU POUR VOIR LEQUEL SERAIT LE MIEUX

def tools_kit(mcp):
    # Files system
    @mcp.tool()
    def read_file(filepath: str, start_line: int = None,
                  end_line: int = None) -> List[str]:
        """
        Read the content of a file with line numbers
        """
        result = []
        if not Path(filepath).exists():
            return f"ERROR: file not found: {filepath}"
        try:
            with open(filepath, "r") as file:
                for i, line in enumerate(file, start=1):
                    if start_line is not None and i < start_line:
                        continue

                    if end_line is not None and i > end_line:
                        break

                    result.append(f"{i}: {line.rstrip()}")
            return result
        except Exception:
            return f"ERROR: '{filepath}'"

    @mcp.tool()
    def edit_file(filepath: str, old_str: str, new_str: str) -> None:
        """
        Replace an exact string in a file with a new string
        """
        try:
            with open(filepath, "r") as file:
                content = file.read()

            occurrences = content.count(old_str)
            if occurrences > 1:
                return f"ERROR: old_str appears {occurrences} times"
            if occurrences == 0:
                return f"ERROR: old_str appears {occurrences} times"
            new_content = content.replace(old_str, new_str, 1)

            with open(filepath, "w") as file:
                file.write(new_content)
            return f"SUCESS: old_str has been changed in {file.name} by {new_str}"
        except Exception as e:
            print(e)

    @mcp.tool()
    def list_files(directory: str, pattern: str) -> List[Path]:
        """
        List files in a directory matching a given pattern
        """
        try:
            root = Path(directory)

            if root.exists():

                files = [
                    file
                    for file in root.rglob("*")
                    if fnmatch.fnmatch(file.name, pattern)
                    ]
                print(files)
                return files
        except Exception as e:
            print(e)

    # Code search
    @mcp.tool()
    def search_code(pattern: str, file_pattern: str) -> List[str]:
        """
        Perform a grep-like search in the codebase
        """
        result = []
        try:
            for file in Path("/testbed").rglob(file_pattern):
                if not file.is_file():
                    continue

                with open(file, "r") as f:
                    for i, line in enumerate(f, start=1):
                        if pattern in line:
                            result.append(
                                f"{file.resolve()}:{i} {line.rstrip()}")
            return "\n".join(result)
        except Exception as e:
            print(e)

    @mcp.tool()
    def search_function_or_class_definition_in_code(name: str
                                                    ) -> List[str]:
        """
        Find the definition of a function or a class
        """
        result = []
        def_re = re.compile(rf"^\s*(def|class)\s+{name}[(:]")
        try:
            for file in Path("/testbed").rglob("*.py"):
                if not file.is_file():
                    continue

                with open(file, "r") as f:
                    for i, line in enumerate(f, start=1):
                        if def_re.match(line):
                            result.append(
                                f"{file.resolve()}:{i} {line.rstrip()}")
            return result
        except Exception as e:
            print(e)

    @mcp.tool()
    def find_references(
        name: str, filepath: str = "", line: int = 0
    ) -> Dict[str, Any]:
        """
        Find all usages of a symbol (function or class).
        """
        result = []
        try:
            for file in Path("/testbed").rglob("*.py"):
                if not file.is_file():
                    continue

                with open(file, "r") as f:
                    for i, line in enumerate(f, start=1):
                        if name in line:
                            result.append(
                                f"{file.resolve()}:{i} {line.rstrip()}")
            return "\n".join(result)
        except Exception as e:
            print(e)

    # Execution Tools
    @mcp.tool()
    def run_tests() -> Dict[str, Any]:
        """
        Execute the evaluation script.
        """
        try:
            if not Path("/eval.sh").exists():
                return "ERROR: no eval script found"
            sub = subprocess.run("bash /eval.sh",
                                 shell=True,
                                 cwd="/testbed",
                                 capture_output=True,
                                 text=True,
                                 timeout=600
                                 )
            result = {
                "stdout": sub.stdout,
                "stderr": sub.stderr,
                "finish": sub.returncode
            }
            return result
        except Exception as e:
            print(e)

    @mcp.tool()
    def get_patch() -> Dict[str, Any]:
        """
        Retrieve the unified git diff of all changes made to the repository
        """
        try:
            sub = subprocess.run("git -c core.fileMode=false diff",
                                 shell=True,
                                 cwd="/testbed",
                                 capture_output=True,
                                 text=True,
                                 timeout=600
                                 )
            result = {
                "stdout": sub.stdout,
                "stderr": sub.stderr,
                "finish": sub.returncode
            }
            return result
        except Exception as e:
            print(e)

    @mcp.tool()
    def run_command(command: str, workdir: str) -> Dict[str, Any]:
        """
        Execute a shell command in the specified working directory.
        """
        try:
            if not Path(workdir).exists():
                return f"ERROR: file not found: {workdir}"
            sub = subprocess.run(command,
                                 shell=True,
                                 cwd=workdir,
                                 capture_output=True,
                                 text=True,
                                 timeout=600
                                 )
            result = {
                "stdout": sub.stdout,
                "stderr": sub.stderr,
                "finish": sub.returncode
            }
            return result
        except Exception as e:
            print(e)
