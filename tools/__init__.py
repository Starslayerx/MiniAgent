from .system import tools as system_tools, tool_handlers as system_tool_handlers
from .plan import tools as plan_tools, tool_handlers as plan_tool_handlers

TOOLS = [*system_tools, *plan_tools]
TOOL_HANDLERS = system_tool_handlers | plan_tool_handlers
