from typing import Literal

from pydantic import BaseModel, Field, Json, field_validator

from llm.types import ToolSpec

PLAN_REMINDER_INTERVAL = 3


class PlanItem(BaseModel):
    content: str = Field(..., min_length=1)
    status: Literal['pending', 'in_progress', 'completed']
    active_form: str = ''


class TodoArguments(BaseModel):
    items: list[PlanItem] | Json[list[PlanItem]] = Field(default_factory=list)

    @field_validator('items')
    @classmethod
    def check_constraints(cls, v: list[PlanItem]) -> list[PlanItem]:
        if len(v) > 12:
            raise ValueError('Keep the session plan short (max 12 items)')

        in_progress_count = sum(1 for item in v if item.status == 'in_progress')
        if in_progress_count > 1:
            raise ValueError('Only one plan item can be in_progress')
        return v


class TodoManager:
    def __init__(self):
        self.items: list[PlanItem] = []
        self.rounds_since_update = 0

    def update(self, validated_items: list[PlanItem]) -> str:
        self.items = validated_items
        self.rounds_since_update += 1
        return self.render()

    def render(self) -> str:
        if not self.items:
            return 'No session plan yet.'

        lines = []
        for item in self.items:
            marker = {
                'pending': '[ ]',
                'in_progress': '[>]',
                'completed': '[x]',
            }[item.status]
            line = f'{marker} {item.content}'
            if item.status == 'in_progress' and item.active_form:
                line += f' ({item.active_form})'
            lines.append(line)

        completed = sum(1 for item in self.items if item.status == 'completed')
        lines.append(f'\n({completed}/{len(self.items)} completed)')
        return '\n'.join(lines)

    def note_round_without_update(self) -> None:
        self.rounds_since_update += 1

    def reminder(self) -> str | None:
        """Format output"""

        if not self.items:
            return None
        if self.rounds_since_update < PLAN_REMINDER_INTERVAL:
            return None
        return '<reminder>Refresh your current plan before continuing.</reminder>'


async def build_plan_registry(todo_manager: TodoManager | None = None):
    manager = todo_manager or TodoManager()

    async def update_plan(items):
        try:
            args = TodoArguments(items=items)
            return manager.update(args.items)
        except Exception as e:
            return f'Error: {e!s}'

    tools = [
        ToolSpec(
            name='plan',
            description='Create or replace the visible task plan for the current session.',
            parameter_schema={
                'type': 'object',
                'properties': {
                    'items': {
                        'type': 'array',
                        'description': 'Ordered plan items. Send the full updated plan each time',
                        'maxItems': 12,
                        'items': {
                            'type': 'object',
                            'properties': {
                                'content': {
                                    'type': 'string',
                                    'description': 'Short user-facing task description.',
                                },
                                'status': {
                                    'type': 'string',
                                    'enum': ['pending', 'in_progress', 'completed'],
                                    'description': 'Current state of this item.',
                                },
                                'active_form': {
                                    'type': 'string',
                                    'description': 'Optional present-progress wording for the active item.',
                                    'default': '',
                                },
                            },
                            'additionalProperties': False,
                            'required': ['content', 'status'],
                        },
                    },
                },
                'additionalProperties': False,
                'required': ['items'],
            },
        ),
    ]

    tool_handlers = {
        'plan': update_plan,
    }

    return tools, tool_handlers
