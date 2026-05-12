from typing import Type

from core.settings import ProviderConfig, ProviderProtocol
from llm.base import ModelClient
from .anthropic_messages import AnthropicMessagesClient
from .openai_completions import OpenAICompletionsClient
from .openai_responses import OpenAIResponsesClient


CLIENT_REGISTRY: dict[ProviderProtocol, Type[ModelClient]] = {
    ProviderProtocol.openai_completions_api: OpenAICompletionsClient,
    ProviderProtocol.openai_responses_api: OpenAIResponsesClient,
    ProviderProtocol.anthropic_messages_api: AnthropicMessagesClient,
}

def create_client(
    *,
    provider: ProviderConfig,
    model: str | None = None,
    reasoning_effort: str | None = None,
) -> ModelClient:
    client_cls = CLIENT_REGISTRY[provider.protocol]

    return client_cls(
        api_key=provider.api_key.get_secret_value(),
        base_url=provider.base_url,
        model=model or provider.default_model,
        extra_body=provider.extra_body,
        reasoning_effort=reasoning_effort,
    )
