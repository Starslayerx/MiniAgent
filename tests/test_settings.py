import pytest

from core.settings import Settings


@pytest.fixture
def settings():

    return Settings(
        provider='openai',
        providers={
            'openai': {
                'base_url': 'https://api.openai.com/v1',
                'api_key': 'sk-test',
                'model': {
                    'primary': 'gpt-5.4',
                    'light': 'gpt-5.4-mini',
                }
            },
            'other': {
                'base_url': 'https://api.other.com/v1',
                'api_key': 'sk-other',
                'model': {
                    'primary': 'big-pickle',
                    'light': 'mini-pickle',
                }
            }
        }
    )


def test_get_provider_returns_current_provider(settings):
    provider = settings.get_provider()

    assert provider.base_url == 'https://api.openai.com/v1'
    assert provider.api_key != 'sk-test'
    assert provider.api_key.get_secret_value() == 'sk-test'
    assert provider.model.primary == 'gpt-5.4'
    assert provider.model.light == 'gpt-5.4-mini'


def test_get_provider_select_other_provider(settings):
    provider = settings.get_provider('other')

    assert provider.base_url == 'https://api.other.com/v1'
    assert provider.api_key != 'sk-other'
    assert provider.api_key.get_secret_value() == 'sk-other'
    assert provider.model.primary == 'big-pickle'
    assert provider.model.light == 'mini-pickle'


def test_get_provider_unknown_provider(settings):
    with pytest.raises(ValueError, match='Unknown provider'):
        settings.get_provider(name='missing')
