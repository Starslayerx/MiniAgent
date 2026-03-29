from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
    CliSettingsSource,
)

from paths import ENV_PATH, PROVIDERS_TOML


class AgentModelsConfig(BaseModel):
    primary: str
    light: str

class ProviderConfig(BaseModel):
    base_url: str
    api_key: SecretStr | None = None
    model: AgentModelsConfig

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
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
                toml_file=PROVIDERS_TOML,
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
