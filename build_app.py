"""PyInstaller build → dist/<APP_EXE_NAME> (recoil + Makcu + web UI)."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from app.core.env import env_flag
from app.core.identity import APP_DISPLAY_NAME, APP_EXE_NAME, APP_SLUG

ROOT = Path(__file__).resolve().parent
ENTRY = ROOT / 'main.py'
ICON = ROOT / 'web' / 'static' / 'AimSync_logo.ico'

_EXCLUDES = (
    'torch',
    'torchvision',
    'torchaudio',
    'ultralytics',
    'matplotlib',
    'onnxruntime',
    'cv2',
    'cyndilib',
    'numpy',
    'pandas',
    'scipy',
    'tensorboard',
)


def _add_data(src: Path, dest: str, out: list[str]) -> None:
    if not src.exists():
        return
    out.extend(['--add-data', f'{src}{os.pathsep}{dest}'])


def dist_exe_path() -> Path:
    return ROOT / 'dist' / APP_EXE_NAME


def _maybe_clean() -> None:
    if not env_flag('BUILD_CLEAN'):
        return
    for path in (ROOT / 'build', dist_exe_path(), ROOT / 'dist' / APP_SLUG):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.is_file():
            path.unlink(missing_ok=True)


def build_args() -> list[str]:
    _maybe_clean()

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    import pyi_collect_lite  # noqa: F401

    args = [
        str(ENTRY),
        f'--name={APP_SLUG}',
        '--onefile',
        '--noconfirm',
        f'--distpath={ROOT / "dist"}',
        f'--workpath={ROOT / "build"}',
        f'--specpath={ROOT}',
        '--paths',
        str(ROOT),
    ]

    if env_flag('BUILD_CONSOLE'):
        args.append('--console')
    else:
        args.append('--noconsole')
        args.append('--windowed')

    if ICON.is_file():
        args.extend(['--icon', str(ICON)])

    _add_data(ROOT / 'web' / 'static', 'web/static', args)
    _add_data(ROOT / 'web' / 'templates', 'web/templates', args)
    _add_data(ROOT / 'app' / 'recoil' / 'data', 'app/recoil/data', args)
    protected = ROOT / 'app' / 'protected'
    _add_data(protected / 'manifest.json', 'app/protected', args)
    _add_data(protected / 'sealed', 'app/protected/sealed', args)
    _add_data(ROOT / 'release' / 'projects.json', 'release', args)
    _add_data(ROOT / 'release' / 'version.json', 'release', args)
    _add_data(ROOT / 'requirements.txt', '.', args)

    hidden = (
        'engineio.async_drivers.threading',
        'flask',
        'werkzeug',
        'jinja2',
        'markupsafe',
        'itsdangerous',
        'click',
        'makcu',
        'tkinter',
        'app.protected.loader',
        'app.protected.crypto',
    )
    from app.protected.pyi_deps import protected_hidden_imports

    sealed_deps = protected_hidden_imports()
    hidden = tuple(dict.fromkeys(hidden + sealed_deps))
    if sealed_deps:
        print(f'[build] sealed-module hidden imports: {", ".join(sealed_deps)}')
    for mod in hidden:
        args.extend(['--hidden-import', mod])
    for mod in _EXCLUDES:
        args.extend(['--exclude-module', mod])

    return args


def main() -> int:
    if not ENTRY.is_file():
        print(f'ERROR: missing entry {ENTRY}')
        return 1

    try:
        import PyInstaller.__main__
    except ImportError:
        print('ERROR: pyinstaller not installed. Run scripts\\create_build_venv.bat')
        return 1

    print(f'[build] {APP_DISPLAY_NAME} onefile exe (recoil + Makcu + web UI)')
    PyInstaller.__main__.run(build_args())

    exe = dist_exe_path()
    if not exe.is_file():
        print(f'ERROR: build finished but {APP_EXE_NAME} is missing')
        return 1

    stale = ROOT / 'dist' / APP_SLUG
    if stale.is_dir():
        shutil.rmtree(stale, ignore_errors=True)

    size_mb = exe.stat().st_size / (1024 * 1024)
    print(f'\nOK: {exe} ({size_mb:.1f} MB)')
    print('Zip: scripts\\package_release.bat')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
