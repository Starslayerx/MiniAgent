from tools.skill import SkillRegistry


def build_system_prompt(skill_registry: SkillRegistry) -> str:

    system_prompt = """You are a coding agent running in the Mini Agent CLI, a terminal-based coding assistant.

Your capabilities:

- Receive user prompts and other context provided by the harness, such as files in the workspace.
- Communicate with the user by thinking & response, and by making & updating plans.
- Emit function calls to run terminal commands and edit files.
"""
    skill_manifests = []
    for document in skill_registry.documents.values():
        path = document.manifest.path
        name = document.manifest.name
        description = document.manifest.description
        skill_manifests.append(f'- {name} skill at {path}: {description}')
    if len(skill_manifests) > 0:
        system_prompt += 'Available skills:\n\n'.join(skill_manifests)
    return system_prompt
