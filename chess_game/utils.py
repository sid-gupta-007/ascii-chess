import sys
import os
import tty
import termios
import select

from .constants import *

# ═══════════════════════════════════════════════
# Cross-Platform Keyboard Input
# ═══════════════════════════════════════════════

def get_key():
    """
    Read a single keypress from stdin.
    Returns a string like 'UP', 'DOWN', 'ENTER',
    'BACKSPACE', 'ESC', or the character pressed.
    Works on Windows (msvcrt) and Unix (termios).
    """
    if os.name == 'nt':
        return _get_key_windows()
    else:
        return _get_key_unix()

def _get_key_windows():
    import msvcrt
    key = msvcrt.getch()
    if key in (b'\xe0', b'\x00'):
        key2 = msvcrt.getch()
        table = {
            b'H': 'UP', b'P': 'DOWN',
            b'K': 'LEFT', b'M': 'RIGHT',
            b'S': 'DELETE',
        }
        return table.get(key2)
    if key == b'\r':   return 'ENTER'
    if key == b'\x08': return 'BACKSPACE'
    if key == b'\x1b': return 'ESC'
    if key == b'\x03': raise KeyboardInterrupt
    try:
        return key.decode('utf-8')
    except Exception:
        return None


def _get_key_unix():
    import tty, termios, select
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        # IMPORTANT: Use os.read(fd, 1) instead of sys.stdin.read(1)
        # sys.stdin.read() has Python-level buffering that consumes
        # ALL available bytes from the OS, so select.select() sees
        # nothing left and arrow key sequences break.
        # os.read() reads exactly 1 byte at the OS level.
        ch = os.read(fd, 1).decode('utf-8', errors='ignore')

        if ch == '\x1b':
            # Check if more bytes follow (escape sequence vs bare ESC)
            if select.select([fd], [], [], 0.1)[0]:
                ch2 = os.read(fd, 1).decode('utf-8', errors='ignore')
                if ch2 == '[':
                    ch3 = os.read(fd, 1).decode('utf-8', errors='ignore')
                    arrows = {
                        'A': 'UP', 'B': 'DOWN',
                        'C': 'RIGHT', 'D': 'LEFT',
                    }
                    if ch3 in arrows:
                        return arrows[ch3]
                    # Handle Delete key: ESC [ 3 ~
                    if ch3 == '3':
                        os.read(fd, 1)   # consume the '~'
                        return 'DELETE'
                    # Handle other sequences (Home, End, etc.) — ignore
                    return None
                elif ch2 == 'O':
                    # Some terminals send ESC O A for arrow keys
                    ch3 = os.read(fd, 1).decode('utf-8', errors='ignore')
                    arrows = {
                        'A': 'UP', 'B': 'DOWN',
                        'C': 'RIGHT', 'D': 'LEFT',
                    }
                    if ch3 in arrows:
                        return arrows[ch3]
                    return None
            return 'ESC'

        if ch in ('\r', '\n'): return 'ENTER'
        if ch in ('\x7f', '\x08'): return 'BACKSPACE'
        if ch == '\x03': raise KeyboardInterrupt
        return ch

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


# ═══════════════════════════════════════════════
# Utility Helpers
# ═══════════════════════════════════════════════

def clear_screen():
    """Clear the terminal (cross-platform)."""
    os.system('cls' if os.name == 'nt' else 'clear')


def square_name(row, col):
    """Convert (row, col) to algebraic notation like 'e4'."""
    return chr(col + ord('a')) + str(8 - row)


def parse_square(text):
    """Convert algebraic notation like 'e4' to (row, col)."""
    text = text.strip().lower()
    if len(text) != 2:
        return None
    c, r = text[0], text[1]
    if not ('a' <= c <= 'h' and '1' <= r <= '8'):
        return None
    return (8 - int(r), ord(c) - ord('a'))


PIECE_NAME = {
    'K': 'King', 'Q': 'Queen', 'R': 'Rook',
    'B': 'Bishop', 'N': 'Knight', 'P': 'Pawn',
}


# ═══════════════════════════════════════════════
#  CHESS BOARD  —  Core Game Logic
# ═══════════════════════════════════════════════

