def get_tool_choices():
    from apps.tools.apis import TOOLS_APIS

    tools = []
    for tool in TOOLS_APIS:
        tools.append((tool.api_basename, tool.api_basename.upper()))
    return tools