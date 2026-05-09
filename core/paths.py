from pathlib import Path
from functools import lru_cache


@lru_cache
def get_current_dir():
    return Path.cwd()

@lru_cache
def get_root_dir(base: Path | None = None):
    return base or Path(__file__).resolve().parent.parent

@lru_cache
def get_prompts_dir(dir: str = 'prompts/'):
    return get_root_dir() / dir

@lru_cache
def get_env_file_path(filename: str = '.env'):
    return get_root_dir() / filename

@lru_cache
def get_providers_file_path(filename: str = 'providers.toml'):
    return get_root_dir() / filename

@lru_cache
def get_skills_dir():
    return get_root_dir() / 'skills'
