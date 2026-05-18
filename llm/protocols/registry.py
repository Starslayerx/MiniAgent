from collections.abc import Callable

from core.settings import ProtocolConfig, ProviderConfig, ProviderProtocol
from llm.base import ModelClient

from .anthropic_messages import AnthropicMessagesClient
from .openai_completions import OpenAICompletionsClient
from .openai_responses import OpenAIResponsesClient

type ClientFactory = Callable[[ProviderConfig, ProtocolConfig, str, str | None], ModelClient]


def _get_api_key(provider: ProviderConfig) -> str:
    if provider.api_key is None:
        raise ValueError('Provider api_key is required')
    return provider.api_key.get_secret_value()


def _create_openai_completions_client(
    provider: ProviderConfig,
    protocol_config: ProtocolConfig,
    model: str,
    reasoning_effort: str | None = None,
) -> ModelClient:
    return OpenAICompletionsClient(
        api_key=_get_api_key(provider),
        base_url=protocol_config.base_url,
        model=model,
        extra_body=protocol_config.extra_body,
        reasoning_effort=reasoning_effort,
    )


def _create_openai_responses_client(
    provider: ProviderConfig,
    protocol_config: ProtocolConfig,
    model: str,
    reasoning_effort: str | None = None,
) -> ModelClient:
    return OpenAIResponsesClient(
        api_key=_get_api_key(provider),
        base_url=protocol_config.base_url,
        model=model,
        extra_body=protocol_config.extra_body,
        reasoning_effort=reasoning_effort,
    )


def _create_anthropic_messages_client(
    provider: ProviderConfig,
    protocol_config: ProtocolConfig,
    model: str,
    reasoning_effort: str | None = None,
) -> ModelClient:
    return AnthropicMessagesClient(
        api_key=_get_api_key(provider),
        base_url=protocol_config.base_url,
        model=model,
        max_tokens=protocol_config.max_tokens,
        budget_tokens=protocol_config.budget_tokens,
    )


CLIENT_REGISTRY: dict[ProviderProtocol, ClientFactory] = {
    ProviderProtocol.openai_completions_api: _create_openai_completions_client,
    ProviderProtocol.openai_responses_api: _create_openai_responses_client,
    ProviderProtocol.anthropic_messages_api: _create_anthropic_messages_client,
}


def create_client(
    *,
    provider: ProviderConfig,
    protocol: ProviderProtocol,
    protocol_config: ProtocolConfig,
    model: str | None = None,
    reasoning_effort: str | None = None,
) -> ModelClient:
    selected_model = model or provider.default_model
    factory = CLIENT_REGISTRY[protocol]
    return factory(provider, protocol_config, selected_model, reasoning_effort)
