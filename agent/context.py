from dataclasses import dataclass
from pathlib import Path
from openai import AsyncOpenAI

from ui.renderer import Renderer


@dataclass
class AgentContext:
    client: AsyncOpenAI
    primary_model: str
    light_model: str
    renderer: Renderer
    workdir: Path
