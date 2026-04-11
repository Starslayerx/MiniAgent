import subprocess
from pathlib import Path

from paths import WORKDIR


class PathSecurityError(ValueError):
    pass

def safe_path(path: str) -> Path:
    """Return absolute path"""

    path = (WORKDIR / path).resolve()
    if not path.is_relative_to(WORKDIR):
        raise PathSecurityError(f'Path escapes workspace: {path}')
    return path

def run_bash(command: str) -> str:
    """Run a bash command"""

    dangerous = ['rm -rf /', 'sudo', 'shutdown', 'reboot', '> /dev/']
    if any(d in command for d in dangerous):
        return 'Error: Dangerous command blocked'
    try:
        r = subprocess.run(
            command,
            shell=True,
            cwd=WORKDIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        out = (r.stdout + r.stderr).strip()
        return out[:5000] if out else '(no output)'
    except subprocess.TimeoutExpired:
        return 'Error: Timeout (120s)'

def run_read(path: str, line_limit: int = None, encoding: str = 'utf-8') -> str:
    """Read file"""

    try:
        text = safe_path(path).read_text(encoding=encoding)
        lines = text.splitlines()
        if line_limit and line_limit < len(lines):
            lines = lines[:line_limit]
        return '\n'.join(lines)
    except Exception as e:
        return f'Error: {e}'

def run_write(path: str, content: str, encoding: str = 'utf-8') -> str:
    """Write file"""

    try:
        abs_path = safe_path(path)
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        with open(abs_path, 'x', encoding=encoding) as f:
            f.write(content)
        return f'Success: file saved to {path}'
    except PathSecurityError as e:
        return f'Error: {e}'
    except FileExistsError:
        return f'Error: file {path} already exists'
    except FileNotFoundError:
        return f'Error: the directory for "{path}" does not exist'
    except Exception as e:
        return f'Error: {e}'

def run_edit(path: str, old_content: str, new_content: str, encoding='utf-8') -> str:
    """Edit file"""

    try:
        abs_path = safe_path(path)
        with open(abs_path, 'r', encoding=encoding) as f:
            content = f.read()
        if old_content not in content:
            return f'Error: old_content not found in this file'
        new_full_content = content.replace(old_content, new_content)
        with open(abs_path, 'w', encoding=encoding) as f:
            f.write(new_full_content)
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
                'command': {
                    'type': 'string',
                },
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
                'limit': {'type': 'integer'},
                'encoding': {'type': 'string'},
            },
            'additionalProperties': False,
            'required': ['path'],
        },
    },
    {
        'type': 'function',
        'name': 'write_file',
        'description': 'Write a new file',
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
    'bash': lambda **kw: run_bash(kw['command']),
    'read_file': lambda **kw: run_read(
        kw['path'],
        kw.get('limit'),
        kw.get('encoding'),
    ),
    'write_file': lambda **kw: run_write(
        kw['path'],
        kw['content'],
        kw.get('encoding'),
    ),
    'edit_file': lambda **kw: run_edit(
        kw['path'],
        kw['old_content'],
        kw['new_content'],
        kw.get('encoding'),
    ),
}
