import pytest
from pydantic import ValidationError

from core.settings import Settings


@pytest.fixture
def settings():

    return Settings(
        provider='dashscope',
        providers={
            'dashscope': {
                'protocol': 'openai_responses',
                'base_url': 'https://dashscope.aliyuncs.com/api/v2/apps/protocols/compatible-mode/v1',
                'api_key': 'sk-dashscope',
                'default_model': 'qwen3.6',
                'models_config': [
                    {'name': 'qwen3.6', 'max_context_tokens': 256000},
                    {'name': 'qwen3.5', 'max_context_tokens': 256000},
                ],
                'extra_body': {'enable_thinking': True},
                'reasoning_efforts': None,

            },
            'deepseek': {
                'protocol': 'openai_completions',
                'base_url': 'https://api.other.com',
                'api_key': 'sk-deepseek',
                'default_model': 'deepseek-v4-flash',
                'models_config': [
                    {'name': 'deepseek-v4-flash', 'max_context_tokens': 1000000},
                    {'name': 'deepseek-v4-pro', 'max_context_tokens': 1000000},
                ],
                'extra_body': {'thinking': {'type': 'enabled'}},
                'reasoning_efforts': ['high', 'max'],
            },
        }
    )


def test_get_provider_with_current_provider(settings):
    provider = settings.get_provider()

    assert provider.protocol == 'openai_responses'
    assert provider.base_url == 'https://dashscope.aliyuncs.com/api/v2/apps/protocols/compatible-mode/v1'
    assert provider.api_key != 'sk-dashscope'
    assert provider.api_key.get_secret_value() == 'sk-dashscope'
    assert provider.default_model == 'qwen3.6'

    item = provider.models_config
    assert item[0].name == 'qwen3.6'
    assert item[0].max_context_tokens == 256_000
    assert item[1].name == 'qwen3.5'
    assert item[1].max_context_tokens == 256_000

    assert provider.extra_body == {'enable_thinking': True}
    assert provider.reasoning_efforts is None


def test_get_provider_with_optional_provider(settings):
    provider = settings.get_provider('deepseek')

    assert provider.protocol == 'openai_completions'
    assert provider.base_url == 'https://api.other.com'
    assert provider.api_key != 'sk-deepseek'
    assert provider.api_key.get_secret_value() == 'sk-deepseek'
    assert provider.default_model == 'deepseek-v4-flash'

    item = provider.models_config
    assert item[0].name == 'deepseek-v4-flash'
    assert item[0].max_context_tokens == 1_000_000
    assert item[1].name == 'deepseek-v4-pro'
    assert item[1].max_context_tokens == 1_000_000

    assert provider.extra_body == {'thinking': {'type': 'enabled'}}
    assert provider.reasoning_efforts == ['high', 'max']


def test_get_provider_unknown_provider(settings):
    with pytest.raises(ValueError, match='Unknown provider'):
        settings.get_provider('test_unknow')


def test_provider_unknown_protocol():
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            provider='unknow',
            providers={
                'unknow': {
                    'protocol': 'unknow',
                    'base_url': 'https://example.com',
                    'api_key': 'sk-test',
                    'default_model': 'small-pickle',
                    'models_config': [
                        {'name': 'small-pickle', 'max_context_tokens': 1},
                        {'name': 'big-pickle', 'max_context_tokens': 2},
                    ],
                }
            }
        )

    errors = exc_info.value.errors()
    assert errors[0]['loc'] == ('providers', 'unknow', 'protocol')
    assert errors[0]['type'] == 'enum'


def test_provider_optional_fields_default_to_none():
    settings = Settings(
        provider='dashscope',
        providers={
            'dashscope': {
                'protocol': 'openai_responses',
                'base_url': 'https://example.com',
                'api_key': 'sk-test',
                'default_model': 'qwen3.6',
                'models_config': [
                    {'name': 'qwen3.6', 'max_context_tokens': None},
                ],
                'extra_body': None,
                'reasoning_efforts': None,
            }
        }
    )

    provider = settings.get_provider()
    assert provider.extra_body is None
    assert provider.reasoning_efforts is None
    assert provider.models_config[0].name == 'qwen3.6'
    assert provider.models_config[0].max_context_tokens is None
