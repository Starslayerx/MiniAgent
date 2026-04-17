from typing import Literal
from dataclasses import dataclass
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit import print_formatted_text
from prompt_toolkit.styles import Style


style = Style.from_dict({
    # assistant
    'assistant.prefix': 'ansigreen bold',
    'assistant.content': '',
    # resoning
    'reasoning.prefix': 'ansibrightblack bold',
    'reasoning.content': 'ansibrightblack italic',
    # tool
    'tool_call.prefix': 'ansiyellow bold',
    'tool_call.content': 'bold',
    'tool_result.prefix': 'ansiyellow',
    'tool_result.content': '',
    # error
    'error.prefix': 'ansired bold',
    'error.content': 'ansired',
})

EventType = Literal[
    'assistant',
    'reasoning',
    'tool_call',
    'tool_result',
    'error',
]

@dataclass
class Event:
    type: EventType
    prefix: str | None = None
    content: str| None = None

class Renderer:
    def render(self, event: Event) -> None:
        prefix_style = f'class:{event.type}.prefix'
        content_style = f'class:{event.type}.content'

        fragments = []

        if event.prefix:
            fragments.append((prefix_style, event.prefix))

        if event.content:
            fragments.append((content_style, event.content))

        print_formatted_text(
            FormattedText(fragments),
            style=style,
        )

