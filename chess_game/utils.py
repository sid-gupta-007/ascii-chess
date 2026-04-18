import sys
import os
import tty
import termios
import select

from .constants import *

# ═══════════════════════════════════════════════
# Cross-Platform Keyboard Input
# ═══════════════════════════════════════════════

def get_key(timeout=None):
    """
    Read a single keypress from stdin.
    Returns a string like 'UP', 'DOWN', 'ENTER',
    'BACKSPACE', 'ESC', or the character pressed.
    If timeout is passed (in seconds) and no key is pressed, returns None.
    Works on Windows (msvcrt) and Unix (termios).
    """
    if os.name == 'nt':
        return _get_key_windows(timeout)
    else:
        return _get_key_unix(timeout)

def _get_key_windows(timeout=None):
    import msvcrt
    if timeout is not None:
        import time
        start_time = time.time()
        while not msvcrt.kbhit():
            if time.time() - start_time > timeout:
                return None
            time.sleep(0.01)
            
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


def _get_key_unix(timeout=None):
    import tty, termios, select
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        
        # Timeout logic for first byte
        if timeout is not None:
            rlist, _, _ = select.select([fd], [], [], timeout)
            if not rlist:
                return None
                
        ch = os.read(fd, 1).decode('utf-8', errors='ignore')

        if ch == '\x1b':
            # Check if more bytes follow (escape sequence vs bare ESC)
            if select.select([fd], [], [], 0.05)[0]:
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
                        # select to drain ~ so it doesn't block
                        if select.select([fd], [], [], 0.05)[0]:
                            os.read(fd, 1)   
                        return 'DELETE'
                    return None
                elif ch2 == 'O':
                    if select.select([fd], [], [], 0.05)[0]:
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

