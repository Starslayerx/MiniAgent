from dataclasses import dataclass, field
from pathlib import Path

from llm.base import ModelClient
from llm.types import TokenUsage
from ui.renderer import Renderer
from tools.skill import SkillRegistry


@dataclass
class AgentContext:
    client: ModelClient
    model_name: str
    renderer: Renderer
    workdir: Path
    skill_reigstry: SkillRegistry
    max_context_tokens: int = 254_000
    last_context_usage: TokenUsage | None = None
    total_usage: TokenUsage = field(default_factory=TokenUsage)
