import io
import contextlib


def run_code(code: str) -> str:
    """Execute Python code and capture what it prints.

    Returns the printed output, or the error message if it crashed.
    """
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            exec(code, {})
        return output.getvalue()
    except Exception as error:
        return f"ERROR: {error}"
