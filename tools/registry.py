from agent.context import AgentContext
from .plan import tools as plan_tools, tool_handlers as plan_tool_handlers
from .system import tools as system_tools, tool_handlers as system_tool_handlers
from .subagent import build_subagent_registry


def build_child_registry():
    """Return child tools"""

    child_tools = [*plan_tools, *system_tools]
    child_tool_handlers = plan_tool_handlers | system_tool_handlers
    return child_tools, child_tool_handlers


async def build_root_registry(context: AgentContext):
    """Return all tools"""

    child_tools, child_tool_handlers = build_child_registry()
    subagent_tools, subagent_tool_handlers = await build_subagent_registry(
        context=context,
        child_tools=child_tools,
        child_tool_handlers=child_tool_handlers,
    )

    root_tools = [*child_tools, *subagent_tools]
    root_tool_handlers = child_tool_handlers | subagent_tool_handlers
    return root_tools, root_tool_handlers
