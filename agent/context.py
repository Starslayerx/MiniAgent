from dataclasses import dataclass
from pathlib import Path
from openai import AsyncOpenAI

from ui.renderer import Renderer


@dataclass
class AgentContext:
    client: AsyncOpenAI
    model_name: str
    max_context_tokens: int | None
    renderer: Renderer
    workdir: Path
