import json

from agent.context import AgentContext
from llm.types import (
    AssistantMessage,
    SystemMessage,
    AgentMessage,
    ToolSpec,
    ToolResultMessage,
)
from ui.renderer import Event


async def agent_loop(
    *,
    context: AgentContext,
    system_message: SystemMessage,
    messages: list[AgentMessage],
    tools: list[ToolSpec],
    tool_handlers: dict,
) -> str:
    """Core agent logic"""

    client = context.client
    renderer = context.renderer

    while True:
        response: AssistantMessage = await client.create_message(
            system_message=system_message,
            messages=messages,
            tools=tools,
        )
        messages.append(response)

        agent_response_parts = []
        has_tool_call = False
        for part in response.parts:
            if part.type == 'reasoning':
                renderer.render(Event(
                    type='reasoning',
                    prefix='[Reasoning] ',
                    content='\n'.join(part.summary),
                ))
            elif part.type == 'message':
                for block in part.content:
                    if block.type == 'text':
                        agent_response_parts.append(block.content)
                        renderer.render(Event(
                            type='assistant',
                            prefix='[Assistant] ',
                            content=block.content,
                        ))
            elif part.type == 'tool_call':
                has_tool_call = True
                renderer.render(Event(
                    type='tool_call',
                    prefix=f'[ToolCall:{part.name}:{part.tool_call_id}] ',
                    content=json.dumps(part.arguments)
                ))

                handler = tool_handlers.get(part.name)
                is_error = False
                if handler:
                    result = await handler(**part.arguments)
                else:
                    is_error = True
                    result = f'Unknown tool {part.name}'

                renderer.render(Event(
                    type='tool_result',
                    prefix=f'[ToolResult:{part.name}] ',
                    content=result,
                ))

                messages.append(
                    ToolResultMessage(
                        tool_call_id=part.tool_call_id,
                        name=part.name,
                        content=result,
                        is_error=is_error,
                    ),
                )

        if not has_tool_call:
            return ''.join(agent_response_parts)
