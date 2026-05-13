import asyncio
from prompt_toolkit import PromptSession

from core.paths import get_current_dir, get_skills_dir
from core.settings import Settings
from llm.protocols import create_client
from llm.types import SystemMessage, TokenUsage, UserMessage
from prompts.system import build_system_prompt
from agent.runner import agent_loop
from agent.context import AgentContext
from tools.registry import build_root_registry
from tools.skill import SkillRegistry
from ui.renderer import Renderer
from ui.input import get_input


async def main():
    settings = Settings()
    provider, protocol, protocol_config = settings.get_protocol_config()

    reasoning_effort = None
    if reason_efforts := getattr(protocol_config, 'reasoning_efforts'):
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

    history_messages = [UserMessage(content=f'Your current work dir is `{work_dir}`')]

    model_config = provider.get_model_config(provider.default_model)

    context = AgentContext(
        client=client,
        model_name=provider.default_model,
        max_context_tokens=model_config.max_context_tokens if model_config else None,
        renderer=renderer,
        workdir=work_dir,
        skill_reigstry=SkillRegistry(get_skills_dir()),
    )
    root_tools, root_tool_handlers = await build_root_registry(context)

    totoal_cost = 0
    while True:
        try:
            query = await get_input(session, prompt='⚡')
        except KeyboardInterrupt:
            print('^C')
            continue
        except EOFError:
            print(f'Total const {totoal_cost} tokens.')
            break

        if query.strip().lower() in ('q', 'exit'):
            print(f'Total const {totoal_cost} tokens.')
            break

        system_message = SystemMessage(
            content=build_system_prompt(
                skill_registry=context.skill_reigstry,
            ),
        )
        history_messages.append(UserMessage(content=query))

        context.current_turn_usage = TokenUsage()
        await agent_loop(
            context=context,
            system_message=system_message,
            messages=history_messages,
            tools=root_tools,
            tool_handlers=root_tool_handlers,
        )
        totoal_cost += context.current_turn_usage.total_tokens

if __name__ == '__main__':
    asyncio.run(main())
