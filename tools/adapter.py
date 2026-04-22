import json
import inspect
from functools import warps
from typing import Any


def normalize_json_value(value: Any, *, max_depth: int = 2) -> Any:
    """solve Double JSON Encoding issue in a simple way

    Examples:

    | Excepted | Wrong Schema |
    | :- | :- |
    | {"config": {"key": "value"}} | {"config": "{\"key\": \"value\"}"} |
    | '{"items":[{"content":"a","status":"pending"}]}' | {"items": '[{"content":"a","status":"pending"}]'}|
    """
    for _ in range(max_depth):
        if not isinstance(value, str):
            return value

        text = value.strip()
        if not (
            (text.startswith('{') and text.endswith('}')) or
            (text.startswith('(') and text.endswith(')'))
        ):
            return value

        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            return value

    return value
