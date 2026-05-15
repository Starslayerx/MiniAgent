import json
from typing import Any

from openai import AsyncOpenAI
from openai.types.responses import Response

from llm.types import (
    AgentMessage,
    AssistantMessage,
    MessagePart,
    ReasoningPart,
    SystemMessage,
    TextBlock,
    TokenUsage,
    ToolCallPart,
    ToolSpec,
)


class OpenAIResponsesClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        extra_body: dict[str, Any] | None = None,
        reasoning_effort: str | None = None,
    ) -> None:
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        self.model = model
        self.extra_body = extra_body
        self.reasoning_effort = reasoning_effort

    def _to_input(self, messages: list[AgentMessage]) -> list[dict[str, Any]]:
        items = []
        for message in messages:
            if message.role == 'user':
                items.append({'role': 'user', 'content': message.content})
            elif message.role == 'assistant':
                for part in message.parts:
                    if part.type == 'message':
                        items.append(
                            {
                                'type': 'message',
                                'role': part.role,
                                'content': [
                                    {'type': 'output_text', 'text': block.content}
                                    for block in part.content
                                    if block.type == 'text'
                                ],
                            }
                        )
                    elif part.type == 'reasoning':
                        item = {
                            'type': 'reasoning',
                            'summary': [
                                {'type': 'summary_text', 'text': text} for text in part.summary
                            ],
                        }
                        if part.id:
                            item['id'] = part.id
                        items.append(item)
                    elif part.type == 'tool_call':
                        item = {
                            'type': 'function_call',
                            'call_id': part.tool_call_id,
                            'name': part.name,
                            'arguments': json.dumps(part.arguments),
                        }
                        if part.id:
                            item['id'] = part.id
                        items.append(item)
            elif message.role == 'tool':
                items.append(
                    {
                        'type': 'function_call_output',
                        'call_id': message.tool_call_id,
                        'output': message.content,
                    }
                )

        return items

    def _to_tools(self, tools: list[ToolSpec]) -> list[dict]:
        return [
            {
                'type': 'function',
                'name': tool.name,
                'description': tool.description,
                'parameters': tool.parameter_schema,
            }
            for tool in tools
        ]

    def _to_assistant_message(self, response: Response) -> AssistantMessage:
        raw_usage = getattr(response, 'usage', None)
        usage = None
        if raw_usage:
            input_details = getattr(raw_usage, 'input_tokens_details', None)
            output_details = getattr(raw_usage, 'output_tokens_details', None)
            usage = TokenUsage(
                input_tokens=getattr(raw_usage, 'input_tokens', 0) or 0,
                output_tokens=getattr(raw_usage, 'output_tokens', 0) or 0,
                input_cache_read_tokens=getattr(input_details, 'cached_tokens', 0) or 0,
                output_reasoning_tokens=getattr(output_details, 'reasoning_tokens', 0) or 0,
            )

        parts = []

        for item in response.output:
            if item.type == 'reasoning':
                parts.append(
                    ReasoningPart(
                        id=item.id,
                        summary=[
                            summary.text
                            for summary in item.summary
                            if summary.type == 'summary_text'
                        ],
                    )
                )
            elif item.type == 'message':
                parts.append(
                    MessagePart(
                        id=item.id,
                        role='assistant',
                        content=[
                            TextBlock(content=content.text)
                            for content in item.content
                            if content.type == 'output_text'
                        ],
                    )
                )
            elif item.type == 'function_call':
                parts.append(
                    ToolCallPart(
                        id=item.id,
                        tool_call_id=item.call_id,
                        name=item.name,
                        arguments=json.loads(item.arguments) if item.arguments else {},
                    )
                )

        return AssistantMessage(parts=parts, usage=usage)

    async def create_message(
        self,
        *,
        system_message: SystemMessage,
        messages: list[AgentMessage],
        tools: list[ToolSpec],
    ) -> AssistantMessage:
        kwargs = {
            'model': self.model,
            'instructions': system_message.content,
            'input': self._to_input(messages),
        }
        if tools:
            kwargs['tools'] = self._to_tools(tools)
        if self.reasoning_effort:
            kwargs['reasoning'] = {'effort': self.reasoning_effort}
        if self.extra_body:
            kwargs['extra_body'] = self.extra_body

        response = await self.client.responses.create(**kwargs)

        return self._to_assistant_message(response)
