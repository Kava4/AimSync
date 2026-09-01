#!/usr/bin/env python3
"""Wrapper — deploy AimSync to Raspberry Pi."""
import subprocess
import sys
from pathlib import Path

target = Path(__file__).resolve().parent / 'pi' / 'deploy.py'
raise SystemExit(subprocess.call([sys.executable, str(target), *sys.argv[1:]]))
