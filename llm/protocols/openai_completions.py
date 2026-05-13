import json
from typing import Any
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from llm.types import (
    AgentMessage,
    AssistantMessage,
    SystemMessage,
    ToolSpec,
    AssistantPart,
    TextBlock,
    MessagePart,
    ReasoningPart,
    ToolCallPart,
    TokenUsage,
)

class OpenAICompletionsClient:
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

    def _to_messages(
        self,
        *,
        system_message: SystemMessage,
        messages: list[AgentMessage],
    ) -> list[dict[str, Any]]:
        completion_messages = [{'role': 'system', 'content': system_message.content}]
        pending_reasoning: str | None = None

        for message in messages:
            if message.role == 'assistant':
                tool_calls = []
                for part in message.parts:
                    if part.type == 'reasoning':
                        pending_reasoning = '\n'.join(part.summary)
                    elif part.type == 'message':
                        for block in part.content:
                            if block.type == 'text':
                                entry = {'role': message.role, 'content': block.content}
                                if pending_reasoning:
                                    entry['reasoning_content'] = pending_reasoning
                                    pending_reasoning = None
                                completion_messages.append(entry)
                    elif part.type == 'tool_call':
                        tool_calls.append({
                            'id': part.tool_call_id,
                            'type': 'function',
                            'function': {
                                'name': part.name,
                                'arguments': json.dumps(part.arguments, ensure_ascii=False),
                            }
                        })
                if tool_calls:
                    entry = {
                        'role': message.role,
                        'content': '',
                        'tool_calls': tool_calls,
                    }
                    if pending_reasoning:
                        entry['reasoning_content'] = pending_reasoning
                        pending_reasoning = None
                    completion_messages.append(entry)
            elif message.role == 'user':
                completion_messages.append({'role': message.role, 'content': message.content})
            elif message.role == 'tool':
                completion_messages.append({
                    'role': message.role,
                    'tool_call_id': message.tool_call_id,
                    'content': message.content,
                })

        return completion_messages

    def _to_tools(
        self,
        *,
        tools: list[ToolSpec],
    ) -> list[dict]:
        completion_tools = []
        for tool in tools:
            completion_tools.append({
                'type': 'function',
                'function': {
                    'name': tool.name,
                    'description': tool.description,
                    'parameters': tool.parameter_schema,
                },
            })
        return completion_tools

    def _to_assistant_message(
        self,
        *,
        response: ChatCompletion,
    ) -> AssistantMessage:
        parts: list[AssistantPart] = []
        msg = response.choices[0].message

        usage = None
        if usage := response.usage:
            details = getattr(usage, 'completion_tokens_details', None)
            usage = TokenUsage(
                input_tokens=usage.prompt_tokens or 0,
                output_tokens=usage.completion_tokens or 0,
                total_tokens=usage.total_tokens or 0,
                reasoning_tokens=getattr(details, 'reasoning_tokens', 0),
            )

        reasoning_content = getattr(msg, 'reasoning_content', None)
        if reasoning_content:
            parts.append(ReasoningPart(summary=[reasoning_content]))

        if msg.tool_calls is None:
            parts.append(MessagePart(
                role='assistant',
                id=response.id,
                content=[TextBlock(content=msg.content)]
            ))
        else:
            for tc in msg.tool_calls:
                parts.append(ToolCallPart(
                    tool_call_id=tc.id,
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments),
                ))

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
            'messages': self._to_messages(
                system_message=system_message,
                messages=messages,
            ),
            'tools': self._to_tools(tools=tools),
        }
        if self.reasoning_effort:
            kwargs['reasoning_effort'] = self.reasoning_effort
        if self.extra_body:
            kwargs['extra_body'] = self.extra_body

        response = await self.client.chat.completions.create(**kwargs)

        return self._to_assistant_message(response=response)
