from typing import Protocol

from .types import (
    AgentMessage,
    AssistantMessage,
    SystemMessage,
    ToolSpec,
)


class ModelClient(Protocol):
    async def create_message(
        self,
        *,
        system_message: SystemMessage,
        messages: list[AgentMessage],
        tools: list[ToolSpec] | None = None,
    ) -> AssistantMessage: ...
