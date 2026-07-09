import re
import json
import ast


def _value_to_python_literal(value) -> str:
    """Turn a Python value (str/int/list/dict/...) into valid Python source."""
    return repr(value)


def _args_to_call(name: str, arguments: dict) -> str:
    """Build a Python function call string from a name + arguments dict."""
    parts = [f"{key}={_value_to_python_literal(value)}"
             for key, value in arguments.items()]
    return f"{name}({', '.join(parts)})"


def _extract_python_block(text: str) -> str | None:
    """Case (a): a fenced ```python ... ``` or ``` ... ``` block."""
    match = re.search(r"```python(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    match = re.search(r"```(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    return None


def _extract_xml_invoke(text: str) -> str | None:
    invoke_match = re.search(
        r'<invoke\s+name=["\'](?P<name>[^"\']+)["\']>(?P<body>.*?)</invoke>',
        text, re.DOTALL,
    )
    if not invoke_match:
        return None

    name = invoke_match.group("name")
    body = invoke_match.group("body")

    arguments = {}
    for param_match in re.finditer(
        r'<parameter\s+name=["\'](?P<pname>[^"\']+)["\']>'
        r'(?P<pvalue>.*?)</parameter>',
        body, re.DOTALL,
    ):
        pname = param_match.group("pname")
        pvalue = param_match.group("pvalue").strip()
        # Try to interpret numbers/lists/booleans; fall back to plain string
        try:
            arguments[pname] = ast.literal_eval(pvalue)
        except (ValueError, SyntaxError):
            arguments[pname] = pvalue

    return _args_to_call(name, arguments)


def _extract_json_tool_call(text: str) -> str | None:
    match = re.search(r"<tool_call>(.*?)</tool_call>", text, re.DOTALL)
    if not match:
        return None

    try:
        payload = json.loads(match.group(1).strip())
        name = payload["name"]
        arguments = payload.get("arguments", {})
        return _args_to_call(name, arguments)
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def _extract_react(text: str) -> str | None:
    action_match = re.search(r"Action:\s*(\S+)", text)
    input_match = re.search(r"Action Input:\s*(\{.*?\})", text, re.DOTALL)
    if not action_match:
        return None

    name = action_match.group(1).strip()
    arguments = {}
    if input_match:
        try:
            arguments = json.loads(input_match.group(1))
        except json.JSONDecodeError:
            arguments = {}

    return _args_to_call(name, arguments)


def extract_code(text: str) -> str | None:
    for extractor in (
        _extract_python_block,
        _extract_xml_invoke,
        _extract_json_tool_call,
        _extract_react,
    ):
        result = extractor(text)
        if result:
            return result

    return None
