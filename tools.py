import subprocess
from paths import USER_DIR


def run_bash(command: str) -> str:
    """Run a bash command"""

    dangerous = ['rm -rf /', 'sudo', 'shutdown', 'reboot', '> /dev/']
    if any(d in command for d in dangerous):
        return 'Error: Dangerous command blocked'
    try:
        r = subprocess.run(
            command,
            shell=True,
            cwd=USER_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        out = (r.stdout + r.stderr).strip()
        return out[:5000] if out else '(no output)'
    except subprocess.TimeoutExpired:
        return 'Error: Timeout (120s)'

TOOLS = [
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
    }
]
