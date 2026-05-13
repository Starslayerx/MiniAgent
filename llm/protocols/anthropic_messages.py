from anthropic import AsyncAnthropic
from typing import Any

from anthropic.types import Message

from llm.types import (
    AgentMessage,
    ToolSpec,
    AssistantMessage,
    SystemMessage,
    ToolSpec,
    TextBlock,
    MessagePart,
    ReasoningPart,
    ToolCallPart,
    TokenUsage,
)

class AnthropicMessagesClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        max_tokens: int | None = None,
        budget_tokens: int | None = None,
    ) -> None:
        self.client = AsyncAnthropic(
            api_key=api_key,
            base_url=base_url,
        )
        self.model = model
        self.max_tokens = max_tokens or 4096
        self.budget_tokens = budget_tokens or 1024

    def _to_messages(
        self,
        *,
        messages: list[AgentMessage],
    ) -> list[dict[str, Any]]:

        def _append_message(output_messages: list, role: str, blocks: list):
            if not blocks:
                return
            if output_messages and output_messages[-1]['role'] == role:
                output_messages[-1]['content'].extend(blocks)
            else:
                output_messages.append({'role': role, 'content': blocks})

        anthropic_messages = []
        for message in messages:
            if message.role == 'assistant':
                content_blocks = []
                for part in message.parts:
                    if part.type == 'message':
                        for block in part.content:
                            if block.type == 'text':
                                content_blocks.append({
                                    'type': 'text',
                                    'text': block.content,
                                })
                    elif part.type == 'reasoning':
                        if part.redacted_data is not None:
                            content_blocks.append({
                                'type': 'redacted_thinking',
                                'data': part.redacted_data,
                            })
                        elif part.summary and part.signature is not None:
                            content_blocks.append({
                                'type': 'thinking',
                                'thinking': ''.join(part.summary),
                                'signature': part.signature,
                            })
                    elif part.type == 'tool_call':
                        content_blocks.append({
                            'type': 'tool_use',
                            'id': part.tool_call_id,
                            'name': part.name,
                            'input': part.arguments,
                        })
                _append_message(anthropic_messages, 'assistant', content_blocks)
            elif message.role == 'user':
                if anthropic_messages and anthropic_messages[-1]['role'] == 'user':
                    anthropic_messages[-1]['content'].append({
                        'type': 'text',
                        'text': message.content,
                    })
                else:
                    anthropic_messages.append({
                        'role': 'user',
                        'content': [{
                            'type': 'text',
                            'text': message.content,
                        }],
                    })
            elif message.role == 'tool':
                if anthropic_messages and anthropic_messages[-1]['role'] == 'user':
                    anthropic_messages[-1]['content'].append({
                        'type': 'tool_result',
                        'tool_use_id': message.tool_call_id,
                        'content': message.content,
                        'is_error': message.is_error,
                    })
                else:
                    anthropic_messages.append({
                        'role': 'user',
                        'content': [{
                            'type': 'tool_result',
                            'tool_use_id': message.tool_call_id,
                            'content': message.content,
                            'is_error': message.is_error,
                        }],
                    })
        return anthropic_messages

    def _to_tools(self, *, tools: list[ToolSpec]) -> list[dict]:
        anthropic_tools: list[dict] = []
        for tool in tools:
            anthropic_tools.append({
                'name': tool.name,
                'description': tool.description,
                'input_schema': tool.parameter_schema,
            })
        return anthropic_tools

    def _to_assistant_message(self, *, message: Message) -> AssistantMessage:
        usage = None
        if usage:= message.usage:
            usage = TokenUsage(
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                total_tokens=usage.input_tokens + usage.output_tokens,
                reasoning_tokens=None,
                cache_read_input_tokens=usage.cache_read_input_tokens,
                cache_creation_input_tokens=usage.cache_creation_input_tokens,
            )

        parts = []
        for content in message.content:
            if content.type == 'text':
                parts.append(MessagePart(
                    role='assistant',
                    content=[TextBlock(content=content.text)],
                ))
            elif content.type == 'thinking':
                parts.append(ReasoningPart(
                    summary=[content.thinking],
                    signature=content.signature,
                    redacted_data=getattr(content, 'redacted_data', None),
                ))
            elif content.type == 'tool_use':
                parts.append(ToolCallPart(
                    tool_call_id=content.id,
                    name=content.name,
                    arguments=content.input,
                ))
            elif content.type == 'redacted_thinking':
                parts.append(ReasoningPart(
                    summary=[],
                    redacted_data=content.data,
                ))
        return AssistantMessage(parts=parts, usage=usage)

    async def create_message(
        self,
        *,
        system_message: SystemMessage,
        messages: list[AgentMessage],
        tools: list[ToolSpec],
    ) -> AssistantMessage:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_message.content,
            messages=self._to_messages(messages=messages),
            tools=self._to_tools(tools=tools),
            thinking={
                'type': 'enabled',
                'budget_tokens': self.budget_tokens,
            },
        )
        return self._to_assistant_message(message=response)
