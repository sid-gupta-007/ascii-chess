#!/usr/bin/env python3
"""
Launcher script for the ASCII Chess application.
Routes execution to the modularized chess_game package.
"""

import sys
import os

# ── Cross-platform UTF-8 setup ──────────────────────────
# Windows consoles default to cp1252 which can't render
# Unicode box-drawing characters.  Force UTF-8 everywhere.
if os.name == 'nt':
    os.system('')  # enable ANSI/VT100 escape sequences on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from chess_game.main import main

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGame exited.")
