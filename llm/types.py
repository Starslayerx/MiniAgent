from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class ToolSpec:
    name: str
    description: str
    parameter_schema: dict[str, Any]


@dataclass
class TextBlock:
    content: str
    type: Literal['text'] = 'text'


ContentBlock = TextBlock


@dataclass
class MessagePart:
    role: Literal['assistant']
    content: list[ContentBlock]
    id: str | None = None
    type: Literal['message'] = 'message'


@dataclass
class ReasoningPart:
    summary: list[str]
    id: str | None = None
    signature: str | None = None
    redacted_data: str | None = None
    type: Literal['reasoning'] = 'reasoning'


@dataclass
class ToolCallPart:
    tool_call_id: str
    name: str
    arguments: dict[str, Any]
    id: str | None = None
    type: Literal['tool_call'] = 'tool_call'


AssistantPart = MessagePart | ReasoningPart | ToolCallPart


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    input_cache_read_tokens: int = 0
    input_cache_creation_tokens: int = 0
    output_reasoning_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def add(self, other: TokenUsage) -> None:
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.input_cache_read_tokens += other.input_cache_read_tokens
        self.input_cache_creation_tokens += other.input_cache_creation_tokens
        self.output_reasoning_tokens += other.output_reasoning_tokens


@dataclass
class AssistantMessage:
    parts: list[AssistantPart]
    usage: TokenUsage | None = None
    role: Literal['assistant'] = 'assistant'


@dataclass(slots=True)
class ToolResultMessage:
    tool_call_id: str
    name: str | None
    content: str
    is_error: bool = False
    role: Literal['tool'] = 'tool'


@dataclass(slots=True)
class UserMessage:
    content: str
    role: Literal['user'] = 'user'


@dataclass(slots=True)
class SystemMessage:
    content: str
    role: Literal['system'] = 'system'


AgentMessage = UserMessage | AssistantMessage | ToolResultMessage
