"""Start Flask web UI + recoil worker."""

from __future__ import annotations

import logging
import os
import sys
import threading
import time
import webbrowser

from app.core.config import config_dir
from app.core.identity import APP_DISPLAY_NAME, APP_LOG_FILE, APP_MUTEX, LOG_NAME
from app.core.paths import app_root
from app.core.runtime import (
    dev_mode_enabled,
    headless_enabled,
    recoil_only_enabled,
)
from app.makcu.manager import makcu_manager
from app.runtime.worker import recoil_worker
from web.app import flask_port, get_local_ip, run_flask, set_shutdown_callback, stop_flask


def _hide_console_window() -> None:
    try:
        import ctypes

        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
    except Exception:
        pass


def _setup_logging() -> None:
    log_dir = config_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=str(log_dir / APP_LOG_FILE),
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filemode='a',
    )
    if headless_enabled():
        root = logging.getLogger()
        if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
            sh = logging.StreamHandler(sys.stdout)
            sh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            root.addHandler(sh)


def _open_browser(url: str) -> None:
    try:
        if hasattr(os, 'startfile'):
            os.startfile(url)
            return
    except OSError:
        pass
    try:
        webbrowser.open_new_tab(url)
    except Exception:
        webbrowser.open(url, new=1, autoraise=True)


def _acquire_single_instance() -> bool:
    if sys.platform != 'win32':
        return True
    try:
        import ctypes

        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, APP_MUTEX)
        if ctypes.windll.kernel32.GetLastError() == 183:
            return False
        return True
    except Exception:
        return True


def run_web_app(*, dev_mode: bool | None = None) -> int:
    if getattr(sys, 'frozen', False) and sys.platform == 'win32':
        _hide_console_window()

    if dev_mode is None:
        dev_mode = dev_mode_enabled()

    headless = headless_enabled()
    recoil_only = recoil_only_enabled()

    if not _acquire_single_instance():
        logging.getLogger(LOG_NAME).warning('%s is already running.', APP_DISPLAY_NAME)
        return 1

    root = app_root()
    os.chdir(root)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    if dev_mode:
        os.environ['AIMSYNC_DEV'] = '1'

    _setup_logging()
    logger = logging.getLogger(LOG_NAME)

    stop_event = threading.Event()
    allow_dev_mouse = bool(dev_mode) and sys.platform == 'win32' and not headless
    makcu_manager.set_dev_allowed(allow_dev_mouse)
    makcu_manager.connect()

    threading.Thread(target=run_flask, name='Flask', daemon=True).start()
    threading.Thread(target=recoil_worker, args=(stop_event,), name='RecoilWorker', daemon=True).start()

    url = f'http://{get_local_ip()}:{flask_port()}'
    time.sleep(0.45)
    if headless:
        logger.info('%s headless at %s (open from another device)', APP_DISPLAY_NAME, url)
    else:
        _open_browser(url)
        logger.info('%s running at %s', APP_DISPLAY_NAME, url)
    if allow_dev_mouse:
        logger.info('Dev mode — local mouse if Makcu unavailable')

    shutdown_requested = threading.Event()

    def request_shutdown(_shutdown_pc: bool = False) -> None:
        stop_event.set()
        stop_flask()
        makcu_manager.disconnect()
        shutdown_requested.set()
        if _shutdown_pc and sys.platform == 'win32':
            import subprocess

            try:
                subprocess.run(
                    ['shutdown', '/s', '/t', '0'],
                    check=True,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
                )
            except Exception:
                pass
        os._exit(0)

    set_shutdown_callback(request_shutdown)

    if headless:
        logger.info('Headless keep-alive — use Stop App in the web UI or SIGTERM.')
        try:
            while not shutdown_requested.is_set():
                time.sleep(0.5)
        except KeyboardInterrupt:
            request_shutdown(False)
        return 0

    try:
        import tkinter as tk

        root_tk = tk.Tk()
        root_tk.withdraw()
        root_tk.title(APP_DISPLAY_NAME)
        root_tk.protocol('WM_DELETE_WINDOW', lambda: request_shutdown(False))

        def poll() -> None:
            if shutdown_requested.is_set():
                root_tk.destroy()
                return
            root_tk.after(200, poll)

        poll()
        root_tk.mainloop()
    except Exception:
        logger.info('Tk unavailable — running headless; use Stop App in browser.')
        try:
            while not shutdown_requested.is_set():
                time.sleep(0.5)
        except KeyboardInterrupt:
            request_shutdown(False)

    return 0
