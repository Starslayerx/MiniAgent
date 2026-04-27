from typing import Any
from enum import StrEnum
from pydantic import BaseModel, SecretStr
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    PydanticBaseSettingsSource,
    TomlConfigSettingsSource,
    CliSettingsSource,
)

from core.paths import get_env_file_path, get_providers_file_path


class ProviderProtocol(StrEnum):
    openai_completions_api = 'openai_completions'
    openai_responses_api = 'openai_responses'
    anthropic_messages_api = 'anthropic_messages'

class ModelConfig(BaseModel):
    name: str
    max_context_tokens: int | None = None

class ProviderConfig(BaseModel):
    protocol: ProviderProtocol
    base_url: str
    api_key: SecretStr | None = None
    default_model: str
    models_config: list[ModelConfig]
    extra_body: dict[str, Any] | None = None
    reasoning_efforts: list[str] | None = None

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
