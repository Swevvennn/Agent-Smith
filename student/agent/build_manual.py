def get_schema_type(schema: dict) -> str:
    if "type" in schema:
        return schema["type"]

    if "anyOf" in schema:
        types = [
            item.get("type")
            for item in schema["anyOf"]
            if item.get("type")
        ]
        return " | ".join(types)

    if "oneOf" in schema:
        types = [
            item.get("type")
            for item in schema["oneOf"]
            if item.get("type")
        ]
        return " | ".join(types)
    return "unknown"


def build_sandbox_manual(tools: list[dict]) -> str:
    if not tools:
        return "Error: No tools found in the mcp server"

    manual = "You have the following Python functions at your disposal:"
    for tool in tools:
        function_and_params = f"- {tool['name']}("
        schema = tool["input_schema"]
        params = ""
        for param in schema.get("properties", {}):
            param_schema = schema["properties"][param]

            param_type = get_schema_type(param_schema)
            params += f"{param}: {param_type}, "
        params = params.rstrip(", ")
        function_and_params += params + ")"
        manual += "\n\n" + function_and_params + "\n\t" + tool["description"].strip()
    return manual
