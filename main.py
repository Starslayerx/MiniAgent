import json
import asyncio
from openai import AsyncOpenAI

from tools import TOOLS, run_bash
from paths import USER_DIR
from settings import Settings, ProviderConfig


async def agent_loop(provider: ProviderConfig, client: AsyncOpenAI, messages: list):
    init_system_message = f"You are a coding agent at {USER_DIR}. Use bash to solve tasks. Act, don't explain."

    while True:
        response = await client.responses.create(
            model=provider.model.primary,
            instructions=init_system_message,
            input=messages,
            tools=TOOLS,
            extra_body={
                'enable_thinking': True,
            }
        )

        messages.extend(response.output)

        has_tool_call = False

        for item in response.output:
            if item.type == 'reasoning':
                print('[Reasoning]', end=' ')
                for summary in item.summary:
                    print(summary.text[:500])
            elif item.type == 'message':
                print(f'[Message] {item.content[0].text}')
            if item.type == 'function_call':
                has_tool_call = True
                if item.name == 'bash':
                    command = json.loads(item.arguments)['command']
                    result = run_bash(command)
                    print(f'[Bash] {command}')
                    print(f'[Tool Output] {result}')
                    messages.append({
                        'type': 'function_call_output',
                        'call_id': item.call_id,
                        'output': result,
                    })

        if not has_tool_call:
            break

async def main():
    settings = Settings()
    provider = settings.get_provider()
    messages = [
        {'role': 'user', 'content': 'How many .py files and .toml files under your current directory? Don\'t include files from system packages (vitrual envrionment).'}
    ]

    client = AsyncOpenAI(
        api_key=provider.api_key.get_secret_value(),
        base_url=provider.base_url,
    )

    await agent_loop(provider, client, messages=messages)

if __name__ == '__main__':
    asyncio.run(main())
