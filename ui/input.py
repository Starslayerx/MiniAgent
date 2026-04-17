from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

async def get_input(session: PromptSession, *, prompt):
    with patch_stdout():
        user_input = await session.prompt_async(prompt)
    return user_input
