"""Runtime flags."""

from __future__ import annotations

import sys

from app.core.env import env_flag


def dev_mode_enabled(argv: list[str] | None = None) -> bool:
    if env_flag('DEV'):
        return True
    args = argv if argv is not None else sys.argv
    return '--dev' in args


def headless_enabled() -> bool:
    """Docker / Pi / no GUI — skip browser + tkinter."""
    return env_flag('HEADLESS') or env_flag('DOCKER')


def recoil_only_enabled() -> bool:
    """Unified hub UI (same on Windows and Pi)."""
    return True
