import json
import asyncio
from openai import AsyncOpenAI

from tools import TOOLS, run_bash
from paths import USER_DIR
from settings import Settings, ProviderConfig


async def agent_loop(provider: ProviderConfig, client: AsyncOpenAI, messages: list):
    init_system_message = f"You are a coding agent at {USER_DIR}. Use bash to solve tasks. Act, don't explain."

    response = await client.responses.create(
        model=provider.model.primary,
        instructions=init_system_message,
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
                print('[Reasoning]')
                for summary in item.summary:
                    print(summary.text)
            elif item.type == 'message':
                print('[Assistant]')
                for content in item.content:
                    messages.append({'role': 'assistant', 'content': content.text})
                    print(f'{content.text}')
            elif item.type == 'function_call':
                has_tool_call = True
                if item.name == 'bash':
                    command = json.loads(item.arguments)['command']
                    result = run_bash(command)
                    print(f'[Bash]\n  $ {command}')
                    print(f'  > {result}')
                    messages.append({
                        'type': 'function_call_output',
                        'call_id': item.call_id,
                        'output': result,
                    })

        if not has_tool_call:
            break

        response = await client.responses.create(
            model=provider.model.primary,
            instructions=init_system_message,
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
    history_messages = []

    client = AsyncOpenAI(
        api_key=provider.api_key.get_secret_value(),
        base_url=provider.base_url,
    )

    while True:
        try:
            query = input('\033[36mInput >> \033[0m')
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ('q', 'exit', ''):
            break
        history_messages.append({'role': 'user', 'content': query})
        await agent_loop(provider, client, messages=history_messages)

if __name__ == '__main__':
    asyncio.run(main())
