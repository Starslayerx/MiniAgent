import asyncio
from prompt_toolkit import PromptSession

from core.paths import get_current_dir
from core.settings import Settings
from llm.protocols.openai_responses import OpenAIResponsesClient
from llm.types import SystemMessage, UserMessage, ToolSpec
from prompts.system import SYSTEM_PROMPT
from agent.runner import agent_loop
from agent.context import AgentContext
from tools.registry import build_root_registry
from ui.renderer import Renderer
from ui.input import get_input


async def main():
    settings = Settings()
    provider = settings.get_provider()
    client = OpenAIResponsesClient(
        api_key=provider.api_key.get_secret_value(),
        base_url=provider.base_url,
        model=provider.default_model,
        extra_body=provider.extra_body,
        reasoning_effort='high',
    )
    session = PromptSession()
    renderer = Renderer()
    work_dir = get_current_dir()

    history_messages = [UserMessage(content=f'Your current work dir is `{work_dir}`')]

    model_config = provider.get_model_config(provider.default_model)

    context = AgentContext(
        client=client,
        model_name=provider.default_model,
        max_context_tokens=model_config.max_context_tokens if model_config else None,
        renderer=renderer,
        workdir=work_dir,
    )
    root_tools, root_tool_handlers = await build_root_registry(context)
    root_tools = [
        ToolSpec(name=tool['name'], description=tool['description'], parameter_schema=tool['parameters'])
        for tool in root_tools
    ]

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

        history_messages.append(UserMessage(content=query))

        await agent_loop(
            context=context,
            system_message=SystemMessage(content=SYSTEM_PROMPT),
            messages=history_messages,
            tools=root_tools,
            tool_handlers=root_tool_handlers,
        )

if __name__ == '__main__':
    asyncio.run(main())
