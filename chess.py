#!/usr/bin/env python3
"""
Launcher script for the ASCII Chess application.
Routes execution to the modularized chess_game package.
"""

from chess_game.main import main

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGame exited.")
