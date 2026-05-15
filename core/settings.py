from enum import StrEnum
from typing import Any

from pydantic import BaseModel, SecretStr
from pydantic_settings import (
    BaseSettings,
    CliSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

from core.paths import get_env_file_path, get_providers_file_path


class ProviderProtocol(StrEnum):
    openai_completions_api = 'openai_completions'
    openai_responses_api = 'openai_responses'
    anthropic_messages_api = 'anthropic_messages'


class ModelConfig(BaseModel):
    name: str
    max_context_tokens: int | None = None


class ProtocolConfig(BaseModel):
    base_url: str
    extra_body: dict[str, Any] | None = None
    reasoning_efforts: list[str] | None = None
    max_tokens: int | None = None
    budget_tokens: int | None = None


class ProviderConfig(BaseModel):
    api_key: SecretStr | None = None
    default_protocol: ProviderProtocol
    protocols: dict[ProviderProtocol, ProtocolConfig]
    default_model: str
    models_config: list[ModelConfig]

    def get_model_config(self, model_name: str) -> ModelConfig | None:
        return next(
            (item for item in self.models_config if item.name == model_name),
            None,
        )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=get_env_file_path(),
        env_file_encoding='utf-8',
        env_nested_delimiter='__',
    )

    # current provider name
    provider: str

    # providers configuration
    providers: dict[str, ProviderConfig]

    debug_max_context_tokens: int | None = None

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            CliSettingsSource(settings_cls),
            init_settings,
            env_settings,
            dotenv_settings,
            TomlConfigSettingsSource(
                settings_cls,
                toml_file=get_providers_file_path(),
                deep_merge=True,
            ),
            file_secret_settings,
        )

    def get_provider(self, name: str | None = None) -> ProviderConfig:
        provider_name = name or self.provider
        try:
            return self.providers[provider_name]
        except KeyError as exc:
            raise ValueError(f'Unknown provider: {provider_name}') from exc

    def get_protocol_config(
        self,
        provider_name: str | None = None,
        protocol: ProviderProtocol | None = None,
    ) -> tuple[ProviderConfig, ProviderProtocol, ProtocolConfig]:
        provider = self.get_provider(provider_name)
        selected_protocol = protocol or provider.default_protocol
        try:
            return provider, selected_protocol, provider.protocols[selected_protocol]
        except KeyError as exc:
            raise ValueError(f'Unknown protocol for provider: {selected_protocol}') from exc
