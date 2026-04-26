import aiofiles
import asyncio
from pathlib import Path

from core.paths import get_current_dir


class PathSecurityError(ValueError):
    pass

def safe_path(path: str) -> Path:
    """Return absolute path"""

    work_dir = get_current_dir()
    path = (work_dir / path).resolve()
    if not path.is_relative_to(work_dir):
        raise PathSecurityError(f'Path escapes workspace: {path}')
    return path

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
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return f'Error: Timeout ({timeout}s)'

async def run_read(path: str, line_limit: int = None, encoding: str = 'utf-8') -> str:
    """Read file"""

    try:
        async with aiofiles.open(safe_path(path), 'r', encoding=encoding) as f:
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
        async with aiofiles.open(abs_path, 'r', encoding=encoding) as f:
            content = await f.read()

        if old_content not in content:
            return f'Error: old_content not found in this file'
        new_full_content = content.replace(old_content, new_content)

        async with aiofiles.open(abs_path, 'w', encoding=encoding) as f:
            await f.write(new_full_content)
        return f'Success: file edited successfully'
    except PathSecurityError as e:
        return f'Error: {e}'
    except FileExistsError:
        return f'Error: file {path} already exists'
    except FileNotFoundError:
        return f'Error: the directory for "{path}" does not exist'
    except Exception as e:
        return f'Error: {e}'


tools = [
    {
        'type': 'function',
        'name': 'bash',
        'description': 'Run a shell command',
        'parameters': {
            'type': 'object',
            'properties': {
                'command': {'type': 'string'},
                'timeout': {'type': 'integer'},
            },
            'additionalProperties': False,
            'required': ['command'],
        },
    },
    {
        'type': 'function',
        'name': 'read_file',
        'description': 'Read a file',
        'parameters': {
            'type': 'object',
            'properties': {
                'path': {'type': 'string'},
                'line_limit': {'type': 'integer'},
                'encoding': {'type': 'string'},
            },
            'additionalProperties': False,
            'required': ['path'],
        },
    },
    {
        'type': 'function',
        'name': 'write_file',
        'description': 'Create a new file without overwriting any existing file',
        'parameters': {
            'type': 'object',
            'properties': {
                'path': {'type': 'string'},
                'content': {'type': 'string'},
                'encoding': {'type': 'string'},
            },
            'additionalProperties': False,
            'required': ['path', 'content'],
        },
    },
    {
        'type': 'function',
        'name': 'edit_file',
        'description': 'Edit a file, replace old content with new content',
        'parameters': {
            'type': 'object',
            'properties': {
                'path': {'type': 'string'},
                'old_content': {'type': 'string'},
                'new_content': {'type': 'string'},
                'encoding': {'type': 'string'},
            },
            'additionalProperties': False,
            'required': ['path', 'old_content', 'new_content'],
        },
    },
]

tool_handlers = {
    'bash': run_bash,
    'read_file': run_read,
    'write_file': run_write,
    'edit_file': run_edit,
}
