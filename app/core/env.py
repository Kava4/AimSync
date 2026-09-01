"""AimSync environment variables (AIMSYNC_*)."""

from __future__ import annotations

import os

_ON = frozenset({'1', 'true', 'yes', 'on'})


def env_flag(name: str) -> bool:
    return os.environ.get(f'AIMSYNC_{name}', '').strip().lower() in _ON


def env_get(name: str, default: str = '') -> str:
    value = os.environ.get(f'AIMSYNC_{name}', '').strip()
    return value if value else default


def env_int(name: str, default: int) -> int:
    raw = env_get(name, '')
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default
