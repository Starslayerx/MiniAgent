import pytest
from pathlib import Path
from collections.abc import Iterator

import core.paths as paths


@pytest.fixture(autouse=True)
def clear_path_caches() -> Iterator[None]:
    paths.get_root_dir.cache_clear()
    paths.get_prompts_dir.cache_clear()
    paths.get_env_file_path.cache_clear()
    paths.get_providers_file_path.cache_clear()

    yield

    paths.get_root_dir.cache_clear()
    paths.get_prompts_dir.cache_clear()
    paths.get_env_file_path.cache_clear()
    paths.get_providers_file_path.cache_clear()


@pytest.fixture
def root_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def test_get_current_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    assert paths.get_current_dir() == tmp_path


def test_get_root_dir_default(root_dir: Path) -> None:
    assert paths.get_root_dir() == root_dir


def test_get_root_dir_custom(tmp_path: Path) -> None:
    assert paths.get_root_dir(tmp_path) == tmp_path


def test_get_prompts_dir_default(root_dir: Path) -> None:
    prompts_dir = root_dir / "prompts/"
    assert paths.get_prompts_dir() == prompts_dir


def test_get_prompts_dir_custom(root_dir: Path) -> None:
    prompts_dir = root_dir / "test_prompts/"
    assert paths.get_prompts_dir("test_prompts/") == prompts_dir


def test_get_env_file_path(root_dir: Path) -> None:
    env_file = root_dir / ".env"
    assert paths.get_env_file_path() == env_file


def test_get_env_file_path_custom(root_dir: Path) -> None:
    env_filename = ".test.env"
    env_path = root_dir / env_filename
    assert paths.get_env_file_path(env_filename) == env_path


def test_get_providers_file_path_default(root_dir: Path) -> None:
    provider_path = root_dir / "providers.toml"
    assert paths.get_providers_file_path() == provider_path


def test_get_providers_file_path_base(root_dir: Path) -> None:
    provider_file = "test_providers.toml"
    provider_path = root_dir / provider_file
    assert paths.get_providers_file_path(provider_file) == provider_path
