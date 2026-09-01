"""App identity."""

from __future__ import annotations

import json
from pathlib import Path

from app.core.paths import app_root, bundle_root

APP_SLUG = 'AimSyncCS2Makcu'
APP_DISPLAY_NAME = 'AimSync CS2 Makcu'
GITHUB_REPO = 'Kava4/AimSync-CS2-Makcu'
APP_NAME = APP_SLUG
APP_STORAGE_DIR = APP_SLUG
APP_EXE_NAME = f'{APP_SLUG}.exe'
APP_ZIP_NAME = f'{APP_SLUG}.zip'
LOG_NAME = APP_SLUG
APP_LOG_FILE = f'{APP_SLUG.lower()}.log'
APP_MUTEX = f'Local\\{APP_SLUG}_v1'
APP_VERSION_LABEL = 'Early Access'


def _read_shipped_version() -> tuple[str, str]:
    candidates = [
        bundle_root() / 'release' / 'version.json',
        app_root() / 'release' / 'version.json',
        Path(__file__).resolve().parents[2] / 'release' / 'version.json',
    ]
    for path in candidates:
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            version = str(data.get('version') or '').strip()
            label = str(data.get('label') or APP_VERSION_LABEL).strip()
            if version:
                return version, label
        except Exception:
            pass
    return '0.1.0-dev', APP_VERSION_LABEL


APP_VERSION, APP_VERSION_LABEL = _read_shipped_version()
