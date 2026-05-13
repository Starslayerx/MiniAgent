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
    max_context_tokens: int | None
    renderer: Renderer
    workdir: Path
    skill_reigstry: SkillRegistry
    current_turn_usage: TokenUsage = field(default_factory=TokenUsage)
    last_call_usage: TokenUsage | None = None
