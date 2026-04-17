from .plan import tools as plan_tools, tool_handlers as plan_tool_handlers
from .system import tools as system_tools, tool_handlers as system_tool_handlers
from .subagent import tools as subagent_tools, tool_handlers as subagent_tool_handlers

root_tools = [*plan_tools, *system_tools]
root_tool_handlers = plan_tool_handlers | system_tool_handlers

child_tools = [*plan_tools, *system_tools]
child_tool_handlers = plan_tool_handlers | system_tool_handlers
