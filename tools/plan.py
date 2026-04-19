import json
from typing import Literal
from pydantic import BaseModel, Field, Json, field_validator


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



TODO = TodoManager()
async def update_todo(items):
    try:
        args = TodoArguments(items=items)
        return TODO.update(args.items)
    except Exception as e:
        return f'Error: {str(e)}'

tools = [
    {
        'type': 'function',
        'name': 'todo',
        'description': 'Rewrite the current session plan for multi-step work',
        'parameters': {
            'type': 'object',
            'properties': {
                'items': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'content': {'type': 'string'},
                            'status': {
                                'type': 'string',
                                'enum': ['pending', 'in_progress', 'completed'],
                            },
                            'active_form': {
                                'type': 'string',
                                'description': 'Optional present-continuous label.'
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
    }
]


tool_handlers = {
    'todo': update_todo,
}
