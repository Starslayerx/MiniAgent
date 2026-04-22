from agent.runner import agent_loop
from agent.context import AgentContext
from prompts import SYSTEM_PROMPT

from .plan import build_plan_registry

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

        messages = [{'role': 'user', 'content': prompt}]
        return await agent_loop(
            context=context,
            system_prompt=SYSTEM_PROMPT,
            messages=messages,
            tools=child_tools,
            tool_handlers=subagent_tool_handlers,
        )

    tools = [
        {
            'type': 'function',
            'name': 'task',
            'description': 'Spawn a sunagent with fresh context. It share the same system prompt and filesystem but not conversation history.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'prompt': {
                        'type': 'string',
                        'description': 'Short description of the task',
                    },
                },
                'additionalProperties': False,
                'required': ['prompt'],
            },
        },
    ]

    tool_handlers = {'task': run_subagent}

    return tools, tool_handlers
