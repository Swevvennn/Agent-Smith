from typing import Dict, List, Any
import subprocess
import textwrap


def tools_kit(mcp):
    @mcp.tool()
    def run_tests(solution_code: str, test_list: List[str],
                  test_imports: List[str] | None = None) -> Dict[str, Any]:
        """
        runs the given tests against your solution.
        Returns {"passed": bool, "message": str}.
        Use it to CHECK your work before finishing.
        """
        test_imports = test_imports or []
        solution_code = textwrap.dedent(solution_code).strip("\n")
        parts = list(test_imports) + [solution_code] + list(test_list)
        full_code = "\n".join(parts)

        try:
            proc = subprocess.run(
                ["python3", "-c", full_code],
                capture_output=True, text=True, timeout=30,
            )
        except subprocess.TimeoutExpired:
            return {
                "passed": False,
                "message": "Timeout: code took too long (>30s)"}

        if proc.returncode == 0:
            return {"passed": True, "message": f"All tests passed: {parts}"}

        error = (proc.stderr.strip().splitlines()[-6:]
                 if proc.stderr.strip() else "unknown error")
        return {"passed": False, "message": error}
