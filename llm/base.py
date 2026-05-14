from typing import Protocol

from .types import (
    SystemMessage,
    AssistantMessage,
    AgentMessage,
    ToolSpec,
)

class ModelClient(Protocol):
    async def create_message(
        self,
        *,
        system_message: SystemMessage,
        messages: list[AgentMessage],
        tools: list[ToolSpec] | None = None,
    ) -> AssistantMessage:
        ...


