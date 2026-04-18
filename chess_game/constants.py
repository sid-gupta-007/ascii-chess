import os
import sys

# ═══════════════════════════════════════════════
# Platform Setup
# ═══════════════════════════════════════════════

def enable_ansi():
    """Enable ANSI escape sequences on Windows 10+."""
    if os.name == 'nt':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(
                kernel32.GetStdHandle(-11), 7
            )
        except Exception:
            pass

enable_ansi()


# ═══════════════════════════════════════════════
# ANSI Escape Codes
# ═══════════════════════════════════════════════

RESET   = '\033[0m'
BOLD    = '\033[1m'
REVERSE = '\033[7m'

FG_BLACK  = '\033[30m'
FG_RED    = '\033[91m'
FG_GREEN  = '\033[92m'
FG_YELLOW = '\033[93m'
FG_CYAN   = '\033[96m'
FG_WHITE  = '\033[97m'
FG_GRAY   = '\033[90m'

BG_RED    = '\033[41m'
BG_GREEN  = '\033[42m'
BG_YELLOW = '\033[43m'
BG_CYAN   = '\033[46m'

BG_LIGHT_SQ = '\033[107m'  # Bright white background for light squares
BG_DARK_SQ  = '\033[100m'  # Dark gray background for dark squares
