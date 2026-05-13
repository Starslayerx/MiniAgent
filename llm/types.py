from __future__ import annotations
from typing import Literal, Any, Union
from dataclasses import dataclass


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

AssistantPart = Union[MessagePart, ReasoningPart, ToolCallPart]

@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    reasoning_tokens: int | None = None
    cache_read_input_tokens: int | None = None
    cache_creation_input_tokens: int | None = None

    def add(self, other: TokenUsage) -> None:
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.total_tokens += other.total_tokens

        if other.reasoning_tokens is not None:
            self.reasoning_tokens = (
                self.reasoning_tokens or 0
            ) + other.reasoning_tokens

        if other.cache_creation_input_tokens is not None:
            self.cache_creation_input_tokens = (
                self.cache_creation_input_tokens or 0
            ) + other.cache_creation_input_tokens

        if other.cache_read_input_tokens is not None:
            self.cache_read_input_tokens = (
                self.cache_read_input_tokens or 0
            ) + other.cache_read_input_tokens

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

AgentMessage = Union[UserMessage, AssistantMessage, ToolResultMessage]
