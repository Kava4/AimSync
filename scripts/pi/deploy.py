#!/usr/bin/env python3
"""Deploy AimSync CS2 Makcu recoil Docker stack to Raspberry Pi over SSH/SFTP."""

from __future__ import annotations

import argparse
import os
import stat
import sys
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parents[2]

# Paths required for `docker compose build` on Pi
SYNC_PATHS = [
    'main.py',
    'requirements-pi.txt',
    'Dockerfile',
    'docker-compose.yml',
    '.dockerignore',
    'docker/entrypoint.sh',
    'app',
    'web',
]

SKIP_DIR_NAMES = {
    '__pycache__',
    '.pytest_cache',
    '.git',
    '_src',
    'AimSync.App',
    'AimSyncCS2Makcu',
}
SKIP_FILE_SUFFIXES = {'.pyc', '.pyo'}


def should_skip(path: Path) -> bool:
    for part in path.parts:
        if part in SKIP_DIR_NAMES:
            return True
    return path.suffix in SKIP_FILE_SUFFIXES


def upload_tree(sftp: paramiko.SFTPClient, local: Path, remote: str) -> None:
    if local.is_file():
        if should_skip(local):
            return
        remote_dir = os.path.dirname(remote.replace('\\', '/'))
        try:
            sftp.stat(remote_dir)
        except OSError:
            parts = remote_dir.strip('/').split('/')
            cur = ''
            for part in parts:
                cur = f'{cur}/{part}' if cur else f'/{part}'
                try:
                    sftp.stat(cur)
                except OSError:
                    sftp.mkdir(cur)
        sftp.put(str(local), remote.replace('\\', '/'))
        return

    for item in sorted(local.iterdir()):
        if should_skip(item):
            continue
        child_remote = f"{remote.rstrip('/')}/{item.name}"
        if item.is_dir():
            try:
                sftp.mkdir(child_remote)
            except OSError:
                pass
            upload_tree(sftp, item, child_remote)
        else:
            upload_tree(sftp, item, child_remote)


def run(client: paramiko.SSHClient, cmd: str) -> tuple[int, str, str]:
    print(f'\n$ {cmd}')
    _, stdout, stderr = client.exec_command(cmd, get_pty=True)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    code = stdout.channel.recv_exit_status()
    if out.strip():
        try:
            print(out.rstrip())
        except UnicodeEncodeError:
            print(out.rstrip().encode('ascii', errors='replace').decode('ascii'))
    if err.strip():
        try:
            print(err.rstrip())
        except UnicodeEncodeError:
            print(err.rstrip().encode('ascii', errors='replace').decode('ascii'))
    return code, out, err


def main() -> int:
    parser = argparse.ArgumentParser(description='Deploy AimSync to Raspberry Pi')
    parser.add_argument('--host', default=os.environ.get('AIMSYNC_PI_HOST', '192.168.1.80'))
    parser.add_argument('--user', default=os.environ.get('AIMSYNC_PI_USER', 'kava'))
    parser.add_argument('--password', default=os.environ.get('AIMSYNC_PI_PASSWORD', ''))
    parser.add_argument('--remote-dir', default='~/aimsync')
    args = parser.parse_args()

    password = args.password
    if not password:
        password = os.environ.get('AIMSYNC_PI_PASS', 'kava123321')

    remote_dir = args.remote_dir.replace('~', f'/home/{args.user}')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f'Connecting to {args.user}@{args.host}…')
    client.connect(args.host, username=args.user, password=password, timeout=30)

    run(client, f'mkdir -p {remote_dir}')
    sftp = client.open_sftp()

    print(f'Uploading to {remote_dir}…')
    for rel in SYNC_PATHS:
        local = ROOT / rel
        if not local.exists():
            print(f'  skip missing {rel}')
            continue
        remote = f'{remote_dir}/{rel}'.replace('\\', '/')
        print(f'  {rel}')
        upload_tree(sftp, local, remote)

    sftp.close()

    code, _, _ = run(client, f'cd {remote_dir} && docker compose up -d --build')
    if code != 0:
        client.close()
        return code

    run(client, f'cd {remote_dir} && docker compose ps')
    run(client, f'cd {remote_dir} && docker compose logs --tail=40 aimsync')
    run(client, 'curl -s http://127.0.0.1:5000/api/health || true')

    print(f'\nDone — open http://{args.host}:5000')
    client.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
