from core.paths import WORKDIR
from prompts import SYSTEM_PROMPT


MAX_ITERATIONS = 30

async def task(prompt: str) -> str:
    sub_system_prompt = f'You are a coding agent at {WORKDIR}. Complete the given task, then summarize your findings.'
    sub_messages = [{'role': 'user', 'content': prompt}]
    for _ in range(MAX_ITERATIONS):
        pass


tools = [{}]
tool_handlers = {}
