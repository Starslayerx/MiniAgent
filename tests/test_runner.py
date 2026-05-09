import pytest
from pathlib import Path

from agent.context import AgentContext
from agent.runner import agent_loop
from llm.types import (
    TextBlock,
    MessagePart,
    ToolCallPart,
    ToolResultMessage,
    ToolSpec,
    AssistantMessage,
    AgentMessage,
    SystemMessage,
    UserMessage,
)
from tools.skill import SkillRegistry

class FakeModelClient:
    def __init__(self):
        self.calls = 0

    async def create_message(
        self,
        *,
        system_message: SystemMessage,
        messages: list[AgentMessage],
        tools: list[ToolSpec],
    ):
        self.calls += 1

        assert isinstance(system_message, SystemMessage)
        # truthy check: is not None and len() > 0
        assert messages
        assert messages[0].content == 'run echo'
        assert tools
        assert tools[0].name == 'echo'

        if self.calls == 1:
            return AssistantMessage(
                parts=[
                    ToolCallPart(
                        id='fc_1',
                        tool_call_id='call_1',
                        name='echo',
                        arguments={'value': 'hello'},
                    )
                ]
            )

        return AssistantMessage(
            parts=[
                MessagePart(
                    id='msg_1',
                    role='assistant',
                    content=[TextBlock(content='done')]
                )
            ]
        )


class FakeRenderer:
    def __init__(self):
        self.events = []
    def render(self, event):
        self.events.append(event)


@pytest.mark.asyncio
async def test_agent_loop_with_tool_result_before_next_model_call(tmp_path):
    """Test below function

    1. Correct message order
    2. Tool call function
    3. Tool result will be add into message history
    """
    client = FakeModelClient()
    renderer = FakeRenderer()
    messages = [UserMessage(content='run echo')]
    skill_reigstry = SkillRegistry(tmp_path)

    async def echo(value: str) -> str:
        return value

    context = AgentContext(
        client=client,
        model_name='fake-model',
        max_context_tokens=None,
        renderer=renderer,
        workdir=Path.cwd(),
        skill_reigstry=skill_reigstry,
    )

    result = await agent_loop(
        context=context,
        system_message=SystemMessage(content='system'),
        messages=messages,
        tools=[ToolSpec(
            name='echo',
            description='Echo a value',
            parameter_schema={
                'type': 'object',
                'properties': {'value': {'type': 'string'}},
                'required': ['value'],
            }
        )],
        tool_handlers={'echo': echo},
    )

    assert result == 'done'
    assert client.calls == 2

    assert isinstance(messages[0], UserMessage)
    assert isinstance(messages[1], AssistantMessage)
    assert isinstance(messages[2], ToolResultMessage)
    assert isinstance(messages[3], AssistantMessage)

    assert messages[2].tool_call_id == 'call_1'
    assert messages[2].name == 'echo'
    assert messages[2].content == 'hello'
