import asyncio

from prompt_toolkit import PromptSession

from agent.context import AgentContext
from agent.runner import agent_loop
from core.paths import get_current_dir, get_skills_dir
from core.settings import Settings
from llm.protocols import create_client
from llm.types import AgentMessage, SystemMessage, UserMessage
from prompts.system import build_system_prompt
from tools.registry import build_root_registry
from tools.skill import SkillRegistry
from ui.input import get_input
from ui.renderer import Renderer


async def main():
    settings = Settings()  # pyright: ignore[reportCallIssue]
    provider, protocol, protocol_config = settings.get_protocol_config()

    reasoning_effort = None
    if reason_efforts := protocol_config.reasoning_efforts:
        reasoning_effort = reason_efforts[0]

    client = create_client(
        provider=provider,
        protocol=protocol,
        protocol_config=protocol_config,
        model=provider.default_model,
        reasoning_effort=reasoning_effort,
    )
    session = PromptSession()
    renderer = Renderer()
    work_dir = get_current_dir()

    history_messages: list[AgentMessage] = [UserMessage(content=f'Your current work dir is `{work_dir}`')]

    model_config = provider.get_model_config(provider.default_model)

    max_context_tokens = 254_000
    if model_config and model_config.max_context_tokens:
        max_context_tokens = model_config.max_context_tokens
    if settings.debug_max_context_tokens:
        max_context_tokens = settings.debug_max_context_tokens

    context = AgentContext(
        client=client,
        model_name=provider.default_model,
        max_context_tokens=max_context_tokens,
        renderer=renderer,
        workdir=work_dir,
        skill_reigstry=SkillRegistry(get_skills_dir()),
    )
    root_tools, root_tool_handlers = await build_root_registry(context)

    while True:
        try:
            query = await get_input(session, prompt='⚡')
        except KeyboardInterrupt:
            print('^C')
            continue
        except EOFError:
            print(f'Total cost {context.total_usage.total_tokens} tokens.')
            break

        if query.strip().lower() in ('q', 'exit'):
            print(f'Total cost {context.total_usage.total_tokens} tokens.')
            break

        system_message = SystemMessage(
            content=build_system_prompt(
                skill_registry=context.skill_reigstry,
            ),
        )
        history_messages.append(UserMessage(content=query))

        await agent_loop(
            context=context,
            system_message=system_message,
            messages=history_messages,
            tools=root_tools,
            tool_handlers=root_tool_handlers,
        )


if __name__ == '__main__':
    asyncio.run(main())
