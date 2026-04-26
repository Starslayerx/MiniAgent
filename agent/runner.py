import json

from agent.context import AgentContext
from ui.renderer import Event


async def agent_loop(
    *,
    context: AgentContext,
    system_prompt: str,
    messages: list,
    tools: list,
    tool_handlers: dict,
) -> str:
    """Core agent logic"""

    client = context.client
    model = context.primary_model
    renderer = context.renderer

    while True:
        response = await client.responses.create(
            model=model,
            instructions=system_prompt,
            input=messages,
            tools=tools,
            reasoning={'effort': 'high'},
            extra_body={
                'thinking': {'type': 'enabled'},  # deepseek
                'enable_thinking': True,          # qwen
            },
        )

        has_tool_call = False
        message_parts = []

        for item in response.output:
            if item.type == 'reasoning':
                for summary in item.summary:
                    if summary.type == 'summary_text':
                        renderer.render(Event(
                            type='reasoning',
                            prefix='[Reasoning] ',
                            content=summary.text,
                        ))
            elif item.type == 'message':
                for content in item.content:
                    message_parts.append(content.text)
                    messages.append({'role': 'assistant', 'content': content.text})
                    renderer.render(Event(
                        type='assistant',
                        prefix='[Assistant] ',
                        content=content.text,
                    ))
            elif item.type == 'function_call':
                has_tool_call = True
                handler = tool_handlers.get(item.name)
                args = json.loads(item.arguments) if item.arguments else {}
                renderer.render(Event(
                    type='tool_call',
                    prefix=f'[ToolCall:{item.name}] ',
                    content='\n'.join(f'{parm}={arg}' for parm, arg in args.items()),
                ))

                if handler:
                    result = await handler(**args)
                else:
                    result = f'Unknown tool {item.name}'

                renderer.render(Event(
                    type='tool_result',
                    prefix=f'[ToolResult:{item.name}] ',
                    content=result,
                ))

                messages.append({
                    'type': 'function_call_output',
                    'call_id': item.call_id,
                    'output': result,
                })

        if not has_tool_call:
            return ''.join(message_parts)
