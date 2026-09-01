"""AimSync CS2 Makcu — entry point (web UI + recoil)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main() -> int:
    from app.core.runtime import dev_mode_enabled
    from app.web.runner import run_web_app

    try:
        return run_web_app(dev_mode=dev_mode_enabled())
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return 0
        if isinstance(code, int):
            return code
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
