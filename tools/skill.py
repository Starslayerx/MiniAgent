import frontmatter
from pathlib import Path
from dataclasses import dataclass

from llm.types import ToolSpec

@dataclass(slots=True)
class SkillManifest:
    name: str
    description: str
    path: Path

@dataclass(slots=True)
class SkillDocument:
    manifest: SkillManifest
    body: str

class SkillRegistry:
    def __init__(self, skill_dir: Path):
        self.root: Path = skill_dir
        self.folders: list[Path] = self._load_skill_folders()
        self.documents: dict[str, SkillDocument] = self._load_skill_documents()

    def _load_skill_folders(self) -> list[Path]:
        return [self.root / p.name for p in self.root.iterdir() if p.is_dir()]

    def _load_skill_documents(self) -> dict[str, SkillDocument]:
        documents: dict[str, SkillDocument] = {}
        for dir in self.folders:
            with open(dir / 'SKILL.md', 'r', encoding='utf-8') as f:
                content = f.read()
                post = frontmatter.loads(content)
                manifest = SkillManifest(
                    name=post.get('name'),
                    description=post.get('description'),
                    path=str(dir),
                )
                documents[post.get('name')] = SkillDocument(manifest=manifest, body=post.content)
        return documents

    def load_body_by_name(self, name: str) -> str:
        return self.documents[name].body


async def bulid_skill_registry(registry: SkillRegistry) -> str:

    async def load_skill(name: str) -> str:
        return registry.load_body_by_name(name)

    tools = [
        ToolSpec(
            name='load_skill',
            description='Load skill content.',
            parameter_schema={
                'type': 'object',
                'properties': {
                    'name': {
                        'type': 'string',
                        'description': 'Skill name.',
                    }
                }
            }
        )
    ]

    tool_handlers = {
        'load_skill': load_skill,
    }

    return tools, tool_handlers
