import json

from agent.context import AgentContext
from llm.types import (
    AgentMessage,
    SystemMessage,
    TokenUsage,
    ToolResultMessage,
    ToolSpec,
    UserMessage,
)
from prompts.compress import get_compress_prompts
from ui.renderer import Event


def _format_token_usage(usage: TokenUsage) -> str:
    input = f'- Input: {usage.input_tokens} tokens.'
    if usage.input_cache_read_tokens:
        input += f' Cache read: {usage.input_cache_read_tokens} tokens.'
    if usage.input_cache_creation_tokens:
        input += f' Cache create: {usage.input_cache_creation_tokens} tokens.'

    output = f'- Output: {usage.output_tokens} tokens.'
    if usage.output_reasoning_tokens:
        output += f' Reasoning: {usage.output_reasoning_tokens} tokens.'

    return '\n'.join(
        [
            f' Cost: {usage.total_tokens} tokens.',
            input,
            output,
        ]
    )


def get_last_n_user_message(messages: list[AgentMessage], n: int = 10):
    results = []
    for msg in reversed(messages):
        if msg.role == 'user':
            results.append(msg)
            if len(results) > n:
                break
    results.reverse()
    return results


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

    current_turn_usage = TokenUsage()
    while True:
        # compress and summary
        if (usage := context.last_context_usage) and (
            usage.total_tokens > context.max_context_tokens * 0.9
        ):
            new_user_message = None
            if messages[-1].role == 'user':
                new_user_message = messages.pop()

            compress_prompt, compress_prefix = await get_compress_prompts()
            compress_messages = [*messages, UserMessage(content=compress_prompt)]

            response = await client.create_message(
                system_message=system_message,
                messages=compress_messages,
                tools=None,
            )

            if usage := response.usage:
                if show_turn_usage:
                    context.last_context_usage = usage
                context.total_usage.add(usage)
                current_turn_usage.add(usage)

            summaries = []
            for part in response.parts:
                if part.type == 'message':
                    for block in part.content:
                        if block.type == 'text':
                            summaries.append(block.content)

            compressed_message = compress_prefix + '\n'.join(summaries)
            old_user_messages = get_last_n_user_message(messages)

            messages.clear()
            messages.extend(old_user_messages)
            messages.append(UserMessage(content=compressed_message))
            if new_user_message:
                messages.append(new_user_message)

            renderer.render(
                Event(
                    type='usage',  # temp
                    prefix='[Context Compacted]\n',
                    content=compressed_message,
                )
            )

        response = await client.create_message(
            system_message=system_message,
            messages=messages,
            tools=tools,
        )

        if usage := response.usage:
            if show_turn_usage:
                context.last_context_usage = usage
            context.total_usage.add(usage)
            current_turn_usage.add(usage)

        has_tool_call = False
        agent_response_parts = []

        messages.append(response)
        tool_results = []

        for part in response.parts:
            if part.type == 'reasoning' and part.summary:
                renderer.render(
                    Event(
                        type='reasoning',
                        prefix='[Reasoning] ',
                        content='\n'.join(part.summary),
                    )
                )
            elif part.type == 'message':
                for block in part.content:
                    if block.type == 'text':
                        agent_response_parts.append(block.content)
                        renderer.render(
                            Event(
                                type='assistant',
                                prefix='[Assistant] ',
                                content=block.content,
                            )
                        )
            elif part.type == 'tool_call':
                has_tool_call = True
                renderer.render(
                    Event(
                        type='tool_call',
                        prefix=f'[ToolCall:{part.name}:{part.tool_call_id}] ',
                        content=json.dumps(part.arguments, ensure_ascii=False),
                    )
                )

                handler = tool_handlers.get(part.name)
                is_error = False
                if handler:
                    result = await handler(**part.arguments)
                else:
                    is_error = True
                    result = f'Unknown tool {part.name}'

                tool_results.append(
                    ToolResultMessage(
                        tool_call_id=part.tool_call_id,
                        name=part.name,
                        content=result,
                        is_error=is_error,
                    )
                )

                renderer.render(
                    Event(
                        type='tool_result',
                        prefix=f'[ToolResult:{part.name}] ',
                        content=result,
                    )
                )

        messages.extend(tool_results)
        if not has_tool_call:
            if show_turn_usage:
                renderer.render(
                    Event(
                        type='usage',
                        prefix='[Usage]',
                        content=_format_token_usage(current_turn_usage),
                    )
                )
            return ''.join(agent_response_parts)
