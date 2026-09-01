"""Seal maintainer plaintext in app/_src into app/protected/sealed/*.bin."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.protected.crypto import seal_bytes, unseal_bytes  # noqa: E402

APP = ROOT / 'app'
SRC = APP / '_src'
SEALED = APP / 'protected' / 'sealed'
MANIFEST = APP / 'protected' / 'manifest.json'


def _blob_path(rel: str) -> Path:
    return SEALED / f"{rel.replace('/', '__')}.bin"


def _is_stub(path: Path) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding='utf-8')
    return 'bind_protected_module' in text and len(text.strip().splitlines()) <= 8


def _source_bytes(rel: str) -> bytes | None:
    src = SRC / rel
    if src.is_file():
        return src.read_bytes()

    blob = _blob_path(rel)
    if blob.is_file():
        return unseal_bytes(blob.read_bytes())

    fallback = APP / rel
    if fallback.is_file() and not _is_stub(fallback):
        return fallback.read_bytes()
    return None


def extract_modules() -> int:
    modules = json.loads(MANIFEST.read_text(encoding='utf-8')).get('modules', [])
    if not modules:
        print('No modules in manifest.json')
        return 1

    extracted = 0
    for rel in modules:
        rel = str(rel).replace('\\', '/')
        blob = _blob_path(rel)
        if not blob.is_file():
            print(f'SKIP missing blob: {rel}')
            continue
        out = SRC / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(unseal_bytes(blob.read_bytes()))
        extracted += 1
        print(f'Extracted: {rel} -> {out.relative_to(ROOT)}')

    print(f'Done — {extracted} module(s) in {SRC}')
    return 0 if extracted else 1


def seal_modules() -> int:
    modules = json.loads(MANIFEST.read_text(encoding='utf-8')).get('modules', [])
    if not modules:
        print('No modules in manifest.json')
        return 1

    SEALED.mkdir(parents=True, exist_ok=True)
    sealed = 0
    for rel in modules:
        rel = str(rel).replace('\\', '/')
        raw = _source_bytes(rel)
        if raw is None:
            print(f'SKIP missing source: {rel}')
            continue
        payload = seal_bytes(raw)
        out = _blob_path(rel)
        out.write_bytes(payload)
        sealed += 1
        print(f'Sealed: {rel} -> {out.name} ({len(payload)} bytes)')

    print(f'Done — {sealed} module(s) in {SEALED}')
    return 0 if sealed else 1


def main() -> int:
    parser = argparse.ArgumentParser(description='Seal or extract protected AimSync modules')
    parser.add_argument('--extract', action='store_true', help='Write sealed blobs to app/_src/')
    args = parser.parse_args()
    if args.extract:
        return extract_modules()
    return seal_modules()


if __name__ == '__main__':
    raise SystemExit(main())
