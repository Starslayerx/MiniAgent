import pytest
from pydantic import ValidationError

from core.settings import ProviderProtocol, Settings


@pytest.fixture
def settings() -> Settings:

    return Settings.model_validate(
        {
            'provider': 'dashscope',
            'providers': {
                'dashscope': {
                    'api_key': 'sk-dashscope',
                    'default_protocol': 'openai_responses',
                    'default_model': 'qwen3.6',
                    'models_config': [
                        {'name': 'qwen3.6', 'max_context_tokens': 256000},
                        {'name': 'qwen3.5', 'max_context_tokens': 256000},
                    ],
                    'protocols': {
                        'openai_responses': {
                            'base_url': 'https://dashscope.aliyuncs.com/api/v2/apps/protocols/compatible-mode/v1',
                            'extra_body': {'enable_thinking': True},
                        },
                    },
                },
                'deepseek': {
                    'api_key': 'sk-deepseek',
                    'default_protocol': 'openai_completions',
                    'default_model': 'deepseek-v4-flash',
                    'models_config': [
                        {'name': 'deepseek-v4-flash', 'max_context_tokens': 1000000},
                        {'name': 'deepseek-v4-pro', 'max_context_tokens': 1000000},
                    ],
                    'protocols': {
                        'openai_completions': {
                            'base_url': 'https://api.other.com',
                            'extra_body': {'thinking': {'type': 'enabled'}},
                            'reasoning_efforts': ['high', 'max'],
                        },
                        'anthropic_messages': {
                            'base_url': 'https://api.other.com/anthropic',
                            'max_tokens': 4096,
                            'budget_tokens': 1024,
                        },
                    },
                },
            },
        },
    )


def test_get_provider_with_current_provider(settings: Settings) -> None:
    provider = settings.get_provider()

    assert provider.api_key is not None
    assert provider.api_key.get_secret_value() == 'sk-dashscope'
    assert provider.default_protocol == 'openai_responses'
    assert provider.default_model == 'qwen3.6'

    item = provider.models_config
    assert item[0].name == 'qwen3.6'
    assert item[0].max_context_tokens == 256_000
    assert item[1].name == 'qwen3.5'
    assert item[1].max_context_tokens == 256_000

    protocol = provider.protocols[ProviderProtocol.openai_responses_api]
    assert protocol.base_url == 'https://dashscope.aliyuncs.com/api/v2/apps/protocols/compatible-mode/v1'
    assert protocol.extra_body == {'enable_thinking': True}
    assert protocol.reasoning_efforts is None


def test_get_provider_with_optional_provider(settings: Settings) -> None:
    provider = settings.get_provider('deepseek')

    assert provider.api_key is not None
    assert provider.api_key.get_secret_value() == 'sk-deepseek'
    assert provider.default_protocol == 'openai_completions'
    assert provider.default_model == 'deepseek-v4-flash'

    item = provider.models_config
    assert item[0].name == 'deepseek-v4-flash'
    assert item[0].max_context_tokens == 1_000_000
    assert item[1].name == 'deepseek-v4-pro'
    assert item[1].max_context_tokens == 1_000_000

    protocol = provider.protocols[ProviderProtocol.openai_completions_api]
    assert protocol.base_url == 'https://api.other.com'
    assert protocol.extra_body == {'thinking': {'type': 'enabled'}}
    assert protocol.reasoning_efforts == ['high', 'max']

    anthropic_protocol = provider.protocols[ProviderProtocol.anthropic_messages_api]
    assert anthropic_protocol.base_url == 'https://api.other.com/anthropic'
    assert anthropic_protocol.max_tokens == 4096
    assert anthropic_protocol.budget_tokens == 1024


def test_get_provider_unknown_provider(settings: Settings) -> None:
    with pytest.raises(ValueError, match='Unknown provider'):
        settings.get_provider('test_unknow')


def test_provider_unknown_protocol() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings.model_validate(
            {
                'provider': 'unknow',
                'providers': {
                    'unknow': {
                        'api_key': 'sk-test',
                        'default_protocol': 'unknow',
                        'default_model': 'small-pickle',
                        'models_config': [
                            {'name': 'small-pickle', 'max_context_tokens': 1},
                            {'name': 'big-pickle', 'max_context_tokens': 2},
                        ],
                        'protocols': {
                            'openai_responses': {
                                'base_url': 'https://example.com',
                            },
                        },
                    }
                },
            },
        )

    errors = exc_info.value.errors()
    assert errors[0]['loc'] == ('providers', 'unknow', 'default_protocol')
    assert errors[0]['type'] == 'enum'


def test_provider_optional_fields_default_to_none() -> None:
    settings = Settings.model_validate(
        {
            'provider': 'test_provider',
            'providers': {
                'test_provider': {
                    'api_key': 'sk-test',
                    'default_protocol': 'openai_responses',
                    'default_model': 'qwen3.6',
                    'models_config': [
                        {'name': 'qwen3.6', 'max_context_tokens': None},
                    ],
                    'protocols': {
                        'openai_responses': {
                            'base_url': 'https://example.com',
                        },
                    },
                }
            },
        },
    )

    provider = settings.get_provider()
    protocol = provider.protocols[ProviderProtocol.openai_responses_api]
    assert protocol.extra_body is None
    assert protocol.reasoning_efforts is None
    assert protocol.max_tokens is None
    assert protocol.budget_tokens is None
    assert provider.models_config[0].name == 'qwen3.6'
    assert provider.models_config[0].max_context_tokens is None
