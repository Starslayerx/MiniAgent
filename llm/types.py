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
class AssistantMessage:
    parts: list[AssistantPart]
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
