"""Verify build-venv before PyInstaller (run from repo root)."""

from __future__ import annotations

import sys


def main() -> int:
    errors: list[str] = []
    for mod in ('PyInstaller', 'flask', 'makcu'):
        try:
            __import__(mod)
            print(f'OK  {mod}')
        except ImportError as exc:
            errors.append(f'{mod}: {exc}')
            print(f'FAIL {mod}: {exc}')

    if errors:
        print('\nFix: scripts\\create_build_venv.bat')
        return 1
    print('\nBuild stack OK — run scripts\\build_app.bat')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
