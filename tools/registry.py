from agent.context import AgentContext

from .plan import build_plan_registry
from .skill import SkillRegistry, build_skill_registry
from .subagent import build_subagent_registry
from .system import tool_handlers as system_tool_handlers
from .system import tools as system_tools


async def build_child_registry(skill_registry: SkillRegistry):
    """Return child tools"""

    plan_tools, plan_tool_handlers = await build_plan_registry()
    skill_tools, skill_tool_handlers = await build_skill_registry(registry=skill_registry)

    child_tools = [*plan_tools, *system_tools, *skill_tools]
    child_tool_handlers = plan_tool_handlers | system_tool_handlers | skill_tool_handlers
    return child_tools, child_tool_handlers


async def build_root_registry(context: AgentContext):
    """Return all tools"""

    child_tools, child_tool_handlers = await build_child_registry(context.skill_reigstry)
    subagent_tools, subagent_tool_handlers = await build_subagent_registry(
        context=context,
        child_tools=child_tools,
        child_tool_handlers=child_tool_handlers,
    )

    root_tools = [*child_tools, *subagent_tools]
    root_tool_handlers = child_tool_handlers | subagent_tool_handlers
    return root_tools, root_tool_handlers
