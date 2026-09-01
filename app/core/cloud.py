"""AimSync cloud API client (feedback, supporter keys, patterns)."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any

from app.core.env import env_get
from app.core.identity import LOG_NAME

logger = logging.getLogger(f'{LOG_NAME}.cloud')

DEFAULT_CLOUD_API = 'https://project-mkgdr.vercel.app/api'


def cloud_api_base() -> str:
    return env_get('CLOUD_API', DEFAULT_CLOUD_API).rstrip('/')


def _get_json(path: str, *, timeout: float = 12) -> tuple[dict[str, Any] | list[Any] | None, str | None]:
    url = f'{cloud_api_base()}/{path.lstrip("/")}'
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            raw = response.read().decode('utf-8', errors='replace')
            return json.loads(raw), None
    except urllib.error.HTTPError as exc:
        return None, f'HTTP {exc.code}'
    except Exception as exc:
        logger.warning('Cloud GET %s failed: %s', url, exc)
        return None, str(exc) or 'Cloud unreachable'


def _post_json(path: str, payload: dict, *, timeout: float = 12) -> tuple[dict[str, Any] | None, str | None]:
    url = f'{cloud_api_base()}/{path.lstrip("/")}'
    body = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=body,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode('utf-8', errors='replace')
            data = json.loads(raw)
            return data if isinstance(data, dict) else {'data': data}, None
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode('utf-8', errors='replace')[:200]
        except Exception:
            detail = ''
        return None, f'HTTP {exc.code}' + (f': {detail}' if detail else '')
    except Exception as exc:
        logger.warning('Cloud POST %s failed: %s', url, exc)
        return None, str(exc) or 'Cloud unreachable'


def fetch_patterns() -> dict[str, Any]:
    data, error = _get_json('patterns')
    if error:
        return {'patterns': [], 'online': False, 'error': error}
    patterns = []
    if isinstance(data, dict):
        patterns = data.get('patterns', []) or []
    return {'patterns': patterns, 'online': True, 'error': None}


def submit_feedback(payload: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    """Forward feedback / support codes to Cloud API → Discord webhook."""
    return _post_json('feedback', payload, timeout=10)


def validate_supporter_key(*, key: str, hwid: str) -> tuple[dict[str, Any] | None, str | None]:
    data, error = _post_json('license/validate', {'key': key, 'hwid': hwid}, timeout=10)
    if error:
        return None, error
    if not isinstance(data, dict):
        return None, 'Invalid license response'
    return data, None
