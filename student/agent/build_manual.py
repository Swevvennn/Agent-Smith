def build_sandbox_manual(tools: list[dict]) -> str:
    if not tools:
        return "Error: No tools found in the mcp server"

    manual = "You have the following Python functions at your disposal:"
    for tool in tools:
        function_and_params = f"- {tool['name']}("
        schema = tool["input_schema"]
        params = ""
        for param in schema["properties"]:
            if param not in schema["required"]:
                params = params + f"{param}: {schema['properties'][param]['type']} (optionnal), "
            else:
                params = params + f"{param}: {schema['properties'][param]['type']}, "
        params = params.rstrip(", ")
        function_and_params += params + ")"
        manual += "\n\n" + function_and_params + "\n\t" + tool["description"].strip()