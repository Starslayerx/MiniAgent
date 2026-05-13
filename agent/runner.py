import json

from agent.context import AgentContext
from llm.types import (
    SystemMessage,
    AgentMessage,
    ToolSpec,
    ToolResultMessage,
    TokenUsage,
)
from ui.renderer import Event


def _format_token_usage(usage: TokenUsage) -> str:
    output = f' Cost {usage.total_tokens} tokens. (Input: {usage.input_tokens} / Output: {usage.output_tokens}'

    if reasoning_tokens := usage.reasoning_tokens:
        output += f' / Reasoning: {reasoning_tokens}'
    output += ')'

    cache_read = usage.cache_read_input_tokens
    cache_create = usage.cache_creation_input_tokens
    if cache_read or cache_create:
        cache = '  [Cache] '
        if cache_read:
            cache += f'Read: {cache_read} '
        if cache_create:
            cache += f'Created: {cache_create}'
        output += cache

    return output

async def agent_loop(
    *,
    context: AgentContext,
    system_message: SystemMessage,
    messages: list[AgentMessage],
    tools: list[ToolSpec],
    tool_handlers: dict,
    show_turn_usage: bool = True,
) -> str:
    """Core agent logic"""

    client = context.client
    renderer = context.renderer

    while True:
        response = await client.create_message(
            system_message=system_message,
            messages=messages,
            tools=tools,
        )

        if response.usage:
            context.last_call_usage = response.usage
            context.current_turn_usage.add(response.usage)

        has_tool_call = False
        agent_response_parts = []

        messages.append(response)
        tool_results = []

        for part in response.parts:
            if part.type == 'reasoning' and part.summary:
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
                    content=json.dumps(part.arguments, ensure_ascii=False)
                ))

                handler = tool_handlers.get(part.name)
                is_error = False
                if handler:
                    result = await handler(**part.arguments)
                else:
                    is_error = True
                    result = f'Unknown tool {part.name}'

                tool_results.append(ToolResultMessage(
                    tool_call_id=part.tool_call_id,
                    name=part.name,
                    content=result,
                    is_error=is_error,
                ))

                renderer.render(Event(
                    type='tool_result',
                    prefix=f'[ToolResult:{part.name}] ',
                    content=result,
                ))

        messages.extend(tool_results)
        if not has_tool_call:
            if show_turn_usage:
                renderer.render(Event(
                    type='usage',
                    prefix='[Usage]',
                    content=_format_token_usage(context.current_turn_usage),
                ))
            return ''.join(agent_response_parts)
