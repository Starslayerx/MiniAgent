import json
import asyncio
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from openai import AsyncOpenAI

from tools import TOOLS, TOOL_HANDLERS
from paths import WORKDIR
from prompts import SYSTEM_PROMPT
from settings import Settings, ProviderConfig
from style import Renderer, Event



renderer = Renderer()

async def agent_loop(provider: ProviderConfig, client: AsyncOpenAI, messages: list):

    response = await client.responses.create(
        model=provider.model.primary,
        instructions=SYSTEM_PROMPT,
        input=messages,
        tools=TOOLS,
        extra_body={
            'enable_thinking': True,
        }
    )

    while True:
        has_tool_call = False

        for item in response.output:
            if item.type == 'reasoning':
                for summary in item.summary:
                    renderer.render(Event(
                        type='reasoning',
                        prefix='[Reasoning] ',
                        content=summary.text,
                    ))
            elif item.type == 'message':
                for content in item.content:
                    messages.append({'role': 'assistant', 'content': content.text})
                    renderer.render(Event(
                        type='assistant',
                        prefix='[Assistant] ',
                        content=content.text,
                    ))
            elif item.type == 'function_call':
                has_tool_call = True
                handler = TOOL_HANDLERS.get(item.name)
                args = json.loads(item.arguments) if item.arguments else {}
                renderer.render(Event(
                    type='tool_call',
                    prefix=f'[ToolCall:{item.name}] ',
                    content='\n'.join(f'{parm}={arg}' for parm, arg in args.items()),
                ))

                result = handler(**args) if handler else f'Unknown tool {item.name}'
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
            break

        response = await client.responses.create(
            model=provider.model.primary,
            instructions=SYSTEM_PROMPT,
            input=messages,
            previous_response_id=response.id,
            tools=TOOLS,
            extra_body={
                'enable_thinking': True,
            }
        )


async def main():
    settings = Settings()
    provider = settings.get_provider()
    history_messages = [{'role': 'user', 'content': f'Your current work dir is `{WORKDIR}`'}]
    session = PromptSession()

    client = AsyncOpenAI(
        api_key=provider.api_key.get_secret_value(),
        base_url=provider.base_url,
    )

    while True:
        try:
            with patch_stdout():
                query = await session.prompt_async('>>> ')
        except KeyboardInterrupt:
            print('^C')
            continue
        except EOFError:
            print('Bye~')
            break

        if query.strip().lower() in ('q', 'exit'):
            print('Bye~')
            break

        history_messages.append({'role': 'user', 'content': query})
        await agent_loop(provider, client, messages=history_messages)

if __name__ == '__main__':
    asyncio.run(main())
