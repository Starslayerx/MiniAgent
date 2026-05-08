import json
from typing import Any
from openai import AsyncOpenAI

from llm.types import (
    AgentMessage,
    AssistantMessage,
    SystemMessage,
    ToolSpec,
    TextBlock,
    MessagePart,
    ReasoningPart,
    ToolCallPart,
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

    def _to_input(self, messages: list[AgentMessage]) -> list[dict]:
        items = []
        for message in messages:
            if message.role == 'user':
                items.append({'role': 'user', 'content': message.content})
            elif message.role == 'assistant':
                for part in message.parts:
                    if part.type == 'message':
                        items.append({
                            'type': 'message',
                            'role': part.role,
                            'content': [
                                {'type': 'output_text', 'text': block.content}
                                for block in part.content
                                if block.type == 'text'
                            ]
                        })
                    elif part.type == 'reasoning':
                        item = {
                            'type': 'reasoning',
                            'summary': [
                                {'type': 'summary_text', 'text': text}
                                for text in part.summary
                            ]
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
                items.append({
                    'type': 'function_call_output',
                    'call_id': message.tool_call_id,
                    'output': message.content,
                })

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

    def _to_assistant_message(self, response: Any) -> AssistantMessage:
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
                        ]
                    )
                )
            elif item.type == 'message':
                parts.append(MessagePart(
                    id=item.id,
                    role='assistant',
                    content=[
                        TextBlock(content=content.text)
                        for content in item.content
                        if content.type == 'output_text'
                    ]
                ))
            elif item.type == 'function_call':
                parts.append(ToolCallPart(
                    id=item.id,
                    tool_call_id=item.call_id,
                    name=item.name,
                    arguments=json.loads(item.arguments) if item.arguments else {},
                ))

        return AssistantMessage(parts=parts)


    async def create_message(
        self,
        *,
        system_message: SystemMessage,
        messages: list[AgentMessage],
        tools: list[ToolSpec],
    ) -> AssistantMessage:
        response = await self.client.responses.create(
            model=self.model,
            instructions=system_message.content,
            input=self._to_input(messages),
            tools=self._to_tools(tools),
            reasoning={'effort': self.reasoning_effort} if self.reasoning_effort else None,
            extra_body=self.extra_body,
        )

        return self._to_assistant_message(response)
