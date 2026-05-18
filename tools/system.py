import asyncio
from pathlib import Path

import aiofiles

from core.paths import get_current_dir
from llm.types import ToolSpec


class PathSecurityError(ValueError):
    pass


def safe_path(path: str) -> Path:
    """Return absolute path"""

    work_dir = get_current_dir()
    abs_path = (work_dir / path).resolve()
    if not abs_path.is_relative_to(work_dir):
        raise PathSecurityError(f'Path escapes workspace: {path}')
    return abs_path


async def run_bash(command: str, timeout: int = 120) -> str:
    """Run a bash command"""

    work_dir = get_current_dir()

    dangerous = ['rm -rf /', 'sudo', 'shutdown', 'reboot', '> /dev/']
    if any(d in command for d in dangerous):
        return 'Error: Dangerous command blocked'

    proc = await asyncio.create_subprocess_shell(
        command,
        cwd=work_dir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        out = (stdout + stderr).decode(errors='replace').strip()
        return out[:5000] if out else '(no output)'
    except TimeoutError:
        proc.kill()
        await proc.wait()
        return f'Error: Timeout ({timeout}s)'


async def run_read(path: str, line_limit: int = 10000, encoding: str = 'utf-8') -> str:
    """Read file"""

    try:
        async with aiofiles.open(safe_path(path), encoding=encoding) as f:
            text = await f.read()
            lines = text.splitlines()
            if line_limit and line_limit < len(lines):
                lines = lines[:line_limit]
            return '\n'.join(lines)
    except Exception as e:
        return f'Error: {e}'


async def run_write(path: str, content: str, encoding: str = 'utf-8') -> str:
    """Write file"""

    try:
        abs_path = safe_path(path)
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(abs_path, 'x', encoding=encoding) as f:
            await f.write(content)
        return f'Success: file saved to {path}'
    except PathSecurityError as e:
        return f'Error: {e}'
    except FileExistsError:
        return f'Error: file {path} already exists'
    except FileNotFoundError:
        return f'Error: the directory for "{path}" does not exist'
    except Exception as e:
        return f'Error: {e}'


async def run_edit(path: str, old_content: str, new_content: str, encoding='utf-8') -> str:
    """Edit file"""

    try:
        abs_path = safe_path(path)
        async with aiofiles.open(abs_path, encoding=encoding) as f:
            content = await f.read()

        if old_content not in content:
            return 'Error: old_content not found in this file'
        new_full_content = content.replace(old_content, new_content)

        async with aiofiles.open(abs_path, 'w', encoding=encoding) as f:
            await f.write(new_full_content)
        return 'Success: file edited successfully'
    except PathSecurityError as e:
        return f'Error: {e}'
    except FileExistsError:
        return f'Error: file {path} already exists'
    except FileNotFoundError:
        return f'Error: the directory for "{path}" does not exist'
    except Exception as e:
        return f'Error: {e}'


tools = [
    ToolSpec(
        name='bash',
        description='Run a shell command in the current workspace and return stdout/stderr.',
        parameter_schema={
            'type': 'object',
            'properties': {
                'command': {
                    'type': 'string',
                    'description': 'Shell command to execute.',
                },
                'timeout': {
                    'type': 'integer',
                    'description': 'Command timeout in seconds. Defaults to 120.',
                    'default': 120,
                },
            },
            'additionalProperties': False,
            'required': ['command'],
        },
    ),
    ToolSpec(
        name='read_file',
        description='Read a UTF-8 text file from the current workspace.',
        parameter_schema={
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'Relative path inside the current workspace.',
                },
                'line_limit': {
                    'type': 'integer',
                    'description': 'Maximum number of lines to return.',
                    'default': 10000,
                },
                'encoding': {
                    'type': 'string',
                    'description': 'File encoding. Defaults to utf-8.',
                    'default': 'utf-8',
                },
            },
            'additionalProperties': False,
            'required': ['path'],
        },
    ),
    ToolSpec(
        name='write_file',
        description='Create a new text file in the current workspace. Fails if the file already exists.',
        parameter_schema={
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'Relative path inside the current workspace.',
                },
                'content': {
                    'type': 'string',
                    'description': 'Completed file contents to write.',
                },
                'encoding': {
                    'type': 'string',
                    'description': 'File encoding. Defaults to utf-8.',
                    'default': 'utf-8',
                },
            },
            'additionalProperties': False,
            'required': ['path', 'content'],
        },
    ),
    ToolSpec(
        name='edit_file',
        description='Edit an existing text file by replacing an exact text snippet.',
        parameter_schema={
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'Relative path inside the current workspace.',
                },
                'old_content': {
                    'type': 'string',
                    'description': 'Exact text to replace. The edit fails if this text is not found.',
                },
                'new_content': {
                    'type': 'string',
                    'description': 'Replacement text.',
                },
                'encoding': {
                    'type': 'string',
                    'description': 'File encoding. Defaults to utf-8.',
                    'default': 'utf-8',
                },
            },
            'additionalProperties': False,
            'required': ['path', 'old_content', 'new_content'],
        },
    ),
]

tool_handlers = {
    'bash': run_bash,
    'read_file': run_read,
    'write_file': run_write,
    'edit_file': run_edit,
}
