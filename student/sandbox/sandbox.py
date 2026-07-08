import multiprocessing
import resource
import builtins
import socket
from sandbox.sandbox_config import SandboxConfig


def _is_path_allowed(path: str, allowed_directories: list[str]) -> bool:
    import os
    abs_path = os.path.abspath(path)
    for allowed in allowed_directories:
        abs_allowed = os.path.abspath(allowed)
        if abs_path.startswith(abs_allowed):
            return True
    return False


def _make_safe_open(allowed_directories: list[str]):
    real_open = builtins.open

    def safe_open(file, *args, **kwargs):
        if not _is_path_allowed(str(file), allowed_directories):
            raise PermissionError(
                f"Access to '{file}' is not allowed. "
                f"Allowed directories: {allowed_directories}"
            )
        return real_open(file, *args, **kwargs)

    return safe_open


def _make_safe_import(authorized_imports: list[str]):
    real_import = builtins.__import__

    def safe_import(name, *args, **kwargs):
        base_module = name.split(".")[0]
        if name not in authorized_imports and f"{base_module}.*" not in authorized_imports \
                and base_module not in authorized_imports:
            raise ImportError(f"Import '{name}' is not allowed in sandbox")
        return real_import(name, *args, **kwargs)

    return safe_import


def _block_network(*args, **kwargs):
    raise PermissionError("Network access is not allowed in sandbox")


def _run_in_subprocess(
    code: str,
    config: SandboxConfig,
    result_queue,
    answer_queue,
    mcp_transport: str = "stdio",
    mcp_target: str | None = None,
    mcp_args: list[str] | None = None,
):

    max_bytes = config.max_memory_mb * 1024 * 1024
    try:
        resource.setrlimit(resource.RLIMIT_AS, (max_bytes, max_bytes))
    except Exception:
        pass
    mcp_client = None
    tool_wrappers = {}
    if mcp_target is not None:
        from client_mcp.bridge import SyncMCPClient, make_wrappers_tools

        if mcp_transport == "http":
            mcp_client = SyncMCPClient(mcp_type="http", url=mcp_target)
        else:
            mcp_client = SyncMCPClient(command=mcp_target, mcp_type="stdio")
        tool_wrappers = make_wrappers_tools(mcp_client)

    socket.socket = _block_network

    final_answer_holder = {"value": None}

    def final_answer(answer):
        final_answer_holder["value"] = answer
        return answer

    safe_builtins = {
        "print": print, "len": len, "range": range, "enumerate": enumerate,
        "str": str, "int": int, "float": float, "bool": bool,
        "list": list, "dict": dict, "set": set, "tuple": tuple,
        "sorted": sorted, "sum": sum, "min": min, "max": max, "abs": abs,
        "zip": zip, "map": map, "filter": filter,
        "isinstance": isinstance, "type": type,
        "Exception": Exception, "ValueError": ValueError,
        "TypeError": TypeError, "KeyError": KeyError,
        "True": True, "False": False, "None": None,
        "__import__": _make_safe_import(config.authorized_imports),
        "open": _make_safe_open(config.allowed_directories),
    }

    namespace = {
        "__builtins__": safe_builtins,
        "final_answer": final_answer,
    }
    namespace.update(tool_wrappers)

    import sys
    import io
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()

    try:
        exec(code, namespace)
        captured = sys.stdout.getvalue()
        sys.stdout = old_stdout
        output = captured if captured.strip() else "Code executed successfully"
        result_queue.put({"success": True, "output": output})
    except (KeyboardInterrupt, SystemExit):
        sys.stdout = old_stdout
        raise
    except Exception as e:
        captured = sys.stdout.getvalue()
        sys.stdout = old_stdout
        output = captured + f"\n{type(e).__name__}: {e}" if captured.strip() else f"{type(e).__name__}: {e}"
        result_queue.put({"success": False, "output": output})
    finally:
        if mcp_client is not None:
            mcp_client.close()

    answer_queue.put(final_answer_holder["value"])


def run_code(
    code: str,
    config: SandboxConfig | None = None,
    mcp_transport: str = "stdio",
    mcp_target: str | None = None,
    mcp_args: list[str] | None = None,
) -> dict:
    if config is None:
        config = SandboxConfig()

    result_queue = multiprocessing.Queue()
    answer_queue = multiprocessing.Queue()

    process = multiprocessing.Process(
        target=_run_in_subprocess,
        args=(
            code,
            config,
            result_queue,
            answer_queue,
            mcp_transport,
            mcp_target,
            mcp_args,
        ),
    )
    process.start()
    process.join(timeout=config.max_execution_time_seconds)

    if process.is_alive():
        process.terminate()
        process.join()
        return {
            "success": False,
            "output": f"Execution timed out after {config.max_execution_time_seconds}s. Output is partial.",
            "final_answer": None,
            "timed_out": True,
        }

    result = result_queue.get() if not result_queue.empty() else {
        "success": False, "output": "Process crashed without returning a result"
    }
    final_value = answer_queue.get() if not answer_queue.empty() else None

    result["final_answer"] = final_value
    result["timed_out"] = False
    return result
# EOF
