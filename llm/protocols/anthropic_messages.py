from anthropic import AsyncAnthropic

from llm.types import (
    AgentMessage,
    ToolResultMessage,
    ToolSpec,
    AssistantMessage,
    SystemMessage,
    UserMessage,
    ToolSpec,
    TextBlock,
    MessagePart,
    ReasoningPart,
    ToolCallPart,
)

class AnthropicMessagesClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        reasoning_effort: str,
        extra_body: dict,
    ) -> None:
        self.client = AsyncAnthropic(
            api_key=api_key,
            base_url=base_url,
        )
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.extra_body = extra_body

    def _to_messages(
        self,
        *,
        messages: list[AgentMessage],
    ) -> list[dict]:

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

    def _to_assistant_message(self, *, message: dict) -> AgentMessage:
        if message.role == 'assistant':
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
            return AssistantMessage(parts=parts)
        elif message.role == 'user':
            for content in message.content:
                if content.type == 'text':
                    return UserMessage(content=content.text)
                elif content.type == 'tool_result':
                    return ToolResultMessage(
                        tool_call_id=content.tool_use_id,
                        content=content.content,
                        is_error=content.is_error,
                    )

    async def create_message(
        self,
        *,
        system_message: SystemMessage,
        messages: list[AgentMessage],
        tools: list[ToolSpec],
    ) -> AssistantMessage:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_message.content,
            messages=self._to_messages(messages=messages),
            tools=self._to_tools(tools=tools),
            thinking={
                'type': 'enabled',
                'budget_tokens': 1024,
            } if self.reasoning_effort else None,
        )
        return self._to_assistant_message(message=response)
