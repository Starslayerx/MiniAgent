import asyncio
from prompt_toolkit import PromptSession
from openai import AsyncOpenAI

from core.paths import WORKDIR
from core.settings import Settings
from prompts.system import SYSTEM_PROMPT
from tools.registry import build_root_registry
from agent.runner import agent_loop
from agent.context import AgentContext
from ui.renderer import Renderer
from ui.input import get_input


async def main():
    settings = Settings()
    provider = settings.get_provider()
    client = AsyncOpenAI(
        api_key=provider.api_key.get_secret_value(),
        base_url=provider.base_url,
    )

    session = PromptSession()
    renderer = Renderer()

    history_messages = [{'role': 'user', 'content': f'Your current work dir is `{WORKDIR}`'}]

    context = AgentContext(
        client=client,
        primary_model=provider.model.primary,
        light_model=provider.model.light,
        renderer=renderer,
        workdir=WORKDIR,
    )
    root_tools, root_tool_handlers = await build_root_registry(context)

    while True:
        try:
            query = await get_input(session, prompt='>>>')
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

        await agent_loop(
            context=context,
            system_prompt=SYSTEM_PROMPT,
            messages=history_messages,
            tools=root_tools,
            tool_handlers=root_tool_handlers,
        )

if __name__ == '__main__':
    asyncio.run(main())
