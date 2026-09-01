"""App config — CS2 recoil."""

from __future__ import annotations

import copy
import json
import os
import threading
from pathlib import Path

from app.core.identity import APP_STORAGE_DIR

_io_lock = threading.Lock()
_last_good: dict | None = None

DEFAULTS: dict = {
    'recoil_enabled': False,
    'recoil_keybind': 'ALWAYS',
    'global_toggle_hotkey': 'M5',
    'recoil_mode': 'CS2',
    'recoil_require_rmb': False,
    'recoil_return_crosshair': False,
    'recoil_randomisation': False,
    'recoil_random_strength': 5.0,
    'recoil_x_control': 100,
    'recoil_y_control': 100,
    'shutdown_on_app_stop': False,
    'cloud_username': 'Anonymous',
    'is_premium': False,
    'mouse_input_method': 'makcu',
    'recoil_cs2_settings': {
        'cs2_weapon': 'assault_rifle',
        'cs2_sensitivity': 1.25,
    },
}


def config_dir() -> Path:
    from app.core.env import env_get

    custom = env_get('CONFIG_DIR')
    if custom:
        path = Path(custom)
        path.mkdir(parents=True, exist_ok=True)
        return path

    base = Path(os.environ.get('APPDATA', Path.home()))
    path = base / APP_STORAGE_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_path() -> Path:
    return config_dir() / 'config.json'


def _merge_defaults(data: dict) -> dict:
    out = copy.deepcopy(DEFAULTS)
    for key, value in data.items():
        if key not in out:
            out[key] = value
        elif isinstance(out[key], dict) and isinstance(value, dict):
            merged = copy.deepcopy(out[key])
            merged.update(value)
            out[key] = merged
        else:
            out[key] = value
    out['recoil_mode'] = 'CS2'
    cs2 = out.setdefault('recoil_cs2_settings', {})
    if 'cs2_weapon' not in cs2:
        cs2['cs2_weapon'] = DEFAULTS['recoil_cs2_settings']['cs2_weapon']
    if 'cs2_sensitivity' not in cs2:
        cs2['cs2_sensitivity'] = DEFAULTS['recoil_cs2_settings']['cs2_sensitivity']
    hotkey = str(out.get('global_toggle_hotkey') or DEFAULTS['global_toggle_hotkey']).strip() or 'M5'
    out['global_toggle_hotkey'] = hotkey
    out['recoil_keybind'] = hotkey
    return out


def _read_json_file(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding='utf-8').strip()
        if not text:
            return None
        data = json.loads(text)
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def load_config() -> dict:
    global _last_good
    with _io_lock:
        path = config_path()
        for candidate in (path, path.with_suffix('.json.bak')):
            data = _read_json_file(candidate)
            if data is not None:
                merged = _merge_defaults(data)
                _last_good = copy.deepcopy(merged)
                return merged
        if _last_good is not None:
            return copy.deepcopy(_last_good)
        return copy.deepcopy(DEFAULTS)


def save_config(config: dict) -> None:
    global _last_good
    with _io_lock:
        payload = _merge_defaults(config)
        path = config_path()
        tmp = path.with_suffix('.json.tmp')
        body = json.dumps(payload, indent=2)
        tmp.write_text(body, encoding='utf-8')
        tmp.replace(path)
        bak = path.with_suffix('.json.bak')
        try:
            bak.write_text(body, encoding='utf-8')
        except OSError:
            pass
        _last_good = copy.deepcopy(payload)
