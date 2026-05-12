from typing import Type

from core.settings import ProviderConfig, ProviderProtocol, ProtocolConfig
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
    protocol: ProviderProtocol,
    protocol_config: ProtocolConfig,
    model: str | None = None,
    reasoning_effort: str | None = None,
) -> ModelClient:
    client_cls = CLIENT_REGISTRY[protocol]
    selected_model = model or provider.default_model

    if protocol == ProviderProtocol.anthropic_messages_api:
        return client_cls(
            api_key=provider.api_key.get_secret_value(),
            base_url=protocol_config.base_url,
            model=selected_model,
            max_tokens=protocol_config.max_tokens,
            budget_tokens=protocol_config.budget_tokens,
        )

    return client_cls(
        api_key=provider.api_key.get_secret_value(),
        base_url=protocol_config.base_url,
        model=selected_model,
        extra_body=protocol_config.extra_body,
        reasoning_effort=reasoning_effort,
    )
