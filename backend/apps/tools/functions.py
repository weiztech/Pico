from functools import cache


@cache
def get_tool_choices():
    from apps.tools.apis import TOOLS_APIS

    tools = []
    for tool in TOOLS_APIS:
        tools.append((tool.api_basename, tool.api_basename.upper()))
    return tools


@cache
def get_tool_prefix_map():
    from apps.tools.apis import TOOLS_APIS

    return {
        tool.api_basename: tool.url_prefix
        for tool in TOOLS_APIS
    }