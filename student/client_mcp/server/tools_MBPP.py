from typing import Dict, List, Any


def tools_kit(mcp):
    @mcp.tool()
    def run_tests(solution_code: str, test_list: List[str],
                  test_imports: List[str] = []) -> Dict[str, Any]:
        """
        runs the given tests against your solution.
        Returns {"passed": bool, "message": str}.
        Use it to CHECK your work before finishing.
        """
        parts = list(test_imports) + [solution_code] + list(test_list)
        full_code = "\n".join(parts)

        try:
            exec(full_code, {})
            return {"passed": True, "message": "All tests passed"}
        except AssertionError:
            return {"passed": False, "message": "A test failed (assertion error)"}
        except Exception as error:
            return {
                "passed": False,
                "message": f"{type(error).__name__}: {error}",
            }

