import re

def extract_code(text: str) -> str | None:
    match = re.search(r"```python(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    match = re.search(r"```(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    return None