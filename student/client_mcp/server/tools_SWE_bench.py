import subprocess
import fnmatch
import re

from pathlib import Path
from typing import Dict, Any, Optional

REPO_ROOT = Path.cwd() / "testbed"


def repo_root():
    candidates = [
        Path("/testbed"),
        Path.cwd() / "testbed",
        Path.cwd(),
    ]

    for path in candidates:
        if path.exists() and (path / ".git").exists():
            return path

    for path in candidates:
        if path.exists():
            return path

    return Path.cwd()


def get_real_path(requested_path: str) -> Path:
    request = Path(requested_path)

    if (
        request.parts
        and len(request.parts) > 1
        and request.parts[0] == '/'
        and request.parts[1] == 'testbed'
    ):
        rel_path = request.relative_to('/testbed')
        return (repo_root() / rel_path).resolve()
    return (repo_root() / requested_path).resolve()


def get_virtual_path(real_path: Path) -> str:
    try:
        rel = real_path.resolve().relative_to(repo_root().resolve())
        return f"/testbed/{rel}"
    except ValueError:
        return str(real_path)


def tools_kit(mcp):
    # Files system
    @mcp.tool()
    def read_file(
        filepath: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Read the content of a file with line numbers.
        Returns a dict with 'success' and 'result' or 'error'.
        """
        real_filepath = get_real_path(filepath)
        if not real_filepath.exists():
            return {"success": False, "error": f"File not found: {filepath}"}
        try:
            result = []
            with open(real_filepath, "r") as file:
                for i, line in enumerate(file, start=1):
                    if start_line is not None and i < start_line:
                        continue
                    if end_line is not None and i > end_line:
                        break
                    result.append(f"{i}: {line.rstrip()}")
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def edit_file(filepath: str, old_str: str, new_str: str) -> Dict[str, Any]:
        """
        Replace an exact string in a file with a new string.
        Returns a dict with 'success' and 'result' or 'error'.
        """
        try:
            real_filepath = get_real_path(filepath)
            with open(real_filepath, "r") as file:
                content = file.read()

            occurrences = content.count(old_str)
            if occurrences == 0:
                return {
                    "success": False,
                    "error": f"Pattern not found in {filepath}",
                }
            if occurrences > 1:
                return {
                    "success": False,
                    "error": (
                        f"Pattern appears {occurrences} times; "
                        "be more specific"
                    ),
                }
            new_content = content.replace(old_str, new_str, 1)
            with open(real_filepath, "w") as file:
                file.write(new_content)
            return {
                "success": True,
                "result": f"Successfully replaced in {filepath}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def list_files(directory: str, pattern: str) -> Dict[str, Any]:
        """
        List files in a directory matching a given pattern.
        Returns a dict with 'success' and 'result' or 'error'.
        """
        try:
            real_filepath = get_real_path(directory)
            if not real_filepath.exists():
                return {
                    "success": False,
                    "error": f"Directory not found: {directory}",
                }
            files = [
                str(get_virtual_path(file))
                for file in real_filepath.rglob("*")
                if fnmatch.fnmatch(file.name, pattern)
            ]
            return {"success": True, "result": files}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Code search
    @mcp.tool()
    def search_code(pattern: str, file_pattern: str) -> Dict[str, Any]:
        """
        Perform a grep-like search in the codebase.
        Returns a dict with 'success' and 'result' or 'error'.
        """
        result = []
        try:
            for file in repo_root().rglob(file_pattern):
                if not file.is_file():
                    continue
                with open(file, "r") as f:
                    for i, line in enumerate(f, start=1):
                        if pattern in line:
                            virtual_path = get_virtual_path(file)
                            result.append(
                                f"{virtual_path}:{i} {line.rstrip()}"
                            )
            if not result:
                return {"success": True, "result": []}
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def search_function_or_class_definition_in_code(
        name: str,
    ) -> Dict[str, Any]:
        """
        Find the definition of a function or a class.
        Returns a dict with 'success' and 'result' or 'error'.
        """
        result = []
        def_re = re.compile(
            rf"^\s*(?:async\s+)?def\s+{re.escape(name)}\s*\("
            rf"|^\s*class\s+{re.escape(name)}\s*[:(]"
        )
        try:
            for file in repo_root().rglob("*.py"):
                if not file.is_file():
                    continue
                with open(file, "r") as f:
                    for i, line in enumerate(f, start=1):
                        if def_re.match(line):
                            virtual_path = get_virtual_path(file)
                            result.append(
                                f"{virtual_path}:{i} {line.rstrip()}"
                            )
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def find_references(
            name: str, filepath: str = "", line: str = "") -> Dict[str, Any]:
        """
        Find all usages of a symbol (function or class).
        Returns a dict with 'success' and 'result' or 'error'.
        """
        result = []
        try:
            for file in repo_root().rglob("*.py"):
                if not file.is_file():
                    continue
                with open(file, "r") as f:
                    for i, line in enumerate(f, start=1):
                        if name in line:
                            result.append(
                                f"{file.resolve()}:{i} {line.rstrip()}"
                            )
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Execution Tools
    MAX_OUTPUT_CHARS = 20000

    def _truncate(text: str, label: str) -> str:
        """Truncate output if too long, with a note about what was cut."""
        if not text:
            return ""
        if len(text) <= MAX_OUTPUT_CHARS:
            return text
        return (
            text[:MAX_OUTPUT_CHARS]
            + f"\n[... {label} truncated: {len(text)} chars total, "
            f"showing first {MAX_OUTPUT_CHARS} ...]"
        )

    @mcp.tool()
    def run_tests() -> Dict[str, Any]:
        """
        Execute the evaluation script.
        Returns a dict with 'success' and test results or 'error'.
        """
        if not Path("eval.sh").exists():
            return {
                "success": False,
                "error": "No eval script found at /eval.sh",
            }
        try:
            sub = subprocess.run(
                "bash /eval.sh",
                shell=True,
                cwd=str(repo_root()),
                capture_output=True,
                text=True,
                timeout=600,
            )
            return {
                "success": True,
                "result": {
                    "stdout": _truncate(sub.stdout, "stdout"),
                    "stderr": _truncate(sub.stderr, "stderr"),
                    "returncode": sub.returncode,
                },
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Evaluation script timed out after 600s",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Could not run evaluation script: {e}",
            }

    @mcp.tool()
    def get_patch() -> str:
        """
        Retrieve the unified git diff of all changes made to the repository.
        """
        try:
            sub = subprocess.run(
                "git -c core.fileMode=false diff",
                shell=True,
                cwd=str(repo_root()),
                capture_output=True,
                text=True,
                timeout=600,
            )
            if sub.returncode != 0:
                return f"ERROR: git diff failed: {sub.stderr}"
            return _truncate(sub.stdout, "patch")
        except subprocess.TimeoutExpired:
            return "ERROR: git diff timed out after 600s"
        except Exception as e:
            return f"ERROR: could not run git diff: {e}"

    @mcp.tool()
    def run_command(command: str, workdir: str) -> Dict[str, Any]:
        """
        Execute a shell command in the specified working directory.
        Returns a dict with 'success' and command results or 'error'.
        """
        try:
            real_workdir = get_real_path(workdir)
            if not real_workdir.exists():
                return {
                    "success": False,
                    "error": f"Directory not found: {workdir} (Real: {real_workdir})",
                }
            sub = subprocess.run(
                command,
                shell=True,
                cwd=real_workdir,
                capture_output=True,
                text=True,
                timeout=600,
            )
            return {
                "success": True,
                "result": {
                    "stdout": _truncate(sub.stdout, "stdout"),
                    "stderr": _truncate(sub.stderr, "stderr"),
                    "returncode": sub.returncode,
                },
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out after 600s"}
        except Exception as e:
            return {"success": False, "error": str(e)}
