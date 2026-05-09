from agent.runner import agent_loop
from agent.context import AgentContext
from prompts import build_system_prompt

from .plan import build_plan_registry
from llm.types import (
    SystemMessage,
    UserMessage,
    ToolSpec,
)

async def build_subagent_registry(
    context: AgentContext,
    child_tools: list,
    child_tool_handlers: dict,
    max_iterations: int = 30, # Not Implemented Yet
):

    async def run_subagent(prompt: str):
        """Run a subagent"""

        _, plan_tool_handlers = await build_plan_registry()
        subagent_tool_handlers = child_tool_handlers | plan_tool_handlers

        messages = [UserMessage(content=prompt)]
        return await agent_loop(
            context=context,
            system_message=SystemMessage(content=build_system_prompt(context.skill_reigstry)),
            messages=messages,
            tools=child_tools,
            tool_handlers=subagent_tool_handlers,
        )

    tools = [
        ToolSpec(
            name='task',
            description='Spawn a subagent with fresh context. It shares the same system prompt and filesystem but not conversation history.',
            parameter_schema={
                'type': 'object',
                'properties': {
                    'prompt': {
                        'type': 'string',
                        'description': 'Short description of the task',
                    },
                },
                'additionalProperties': False,
                'required': ['prompt'],
            }
        )
    ]

    tool_handlers = {'task': run_subagent}

    return tools, tool_handlers
