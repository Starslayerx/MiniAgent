import aiofiles
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = ROOT_DIR / 'prompts/'
ENV_PATH = ROOT_DIR / '.env'
PROVIDERS_TOML = ROOT_DIR / 'providers.toml'

USER_DIR = Path.cwd()
