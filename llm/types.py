from __future__ import annotations
from typing import Literal, Any, Union
from dataclasses import dataclass


@dataclass
class ToolSpec:
    name: str
    description: str
    parameter_schema: dict[str, Any]


@dataclass
class TextPart:
    content: str
    type: Literal['text'] = 'text'

@dataclass
class ReasoningPart:
    content: str
    type: Literal['reasoning'] = 'reasoning'

@dataclass
class ToolCallPart:
    tool_call_id: str
    name: str
    arguments: dict[str, Any]
    type: Literal['tool_call'] = 'tool_call'

AssistantPart = Union[TextPart, ReasoningPart, ToolCallPart]

@dataclass
class AssistantMessage:
    parts: list[AssistantPart]
    role: Literal['assistant'] = 'assistant'


@dataclass(slots=True)
class ToolResultMessage:
    tool_call_id: str
    name: str
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
