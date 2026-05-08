from dataclasses import dataclass
from pathlib import Path

from llm.base import ModelClient
from ui.renderer import Renderer


@dataclass
class AgentContext:
    client: ModelClient
    model_name: str
    max_context_tokens: int | None
    renderer: Renderer
    workdir: Path
