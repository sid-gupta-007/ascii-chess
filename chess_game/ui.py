import sys
from .constants import *
from .utils import get_key, clear_screen, square_name, PIECE_NAME, parse_square
from .board import ChessBoard

class InteractiveGame:
    """
    Navigate with arrow keys, select with Enter,
    deselect with Backspace/Delete/ESC.
    Legal moves glow on the board when a piece
    is selected.
    """

    def __init__(self):
        self.board = ChessBoard()
        self.cursor = [7, 4]      # row, col — start at e1
        self.selected = None      # (row, col) of selected piece
        self.legal = []           # list of (row, col) legal targets
        self.message = ""
        self.flipped = False

    def run(self):
        try:
            # Hide terminal cursor for cleaner display
            sys.stdout.write('\033[?25l')
            sys.stdout.flush()
            self._loop()
        except KeyboardInterrupt:
            pass
        finally:
            # Restore terminal cursor
            sys.stdout.write('\033[?25h')
            sys.stdout.write(RESET + '\n')
            sys.stdout.flush()

    def _loop(self):
        while True:
            self._render()

            if self.board.game_over:
                self._render_game_over()
                key = get_key()
                if key and key.lower() == 'y':
                    self.board = ChessBoard()
                    self.cursor = [7, 4]
                    self.selected = None
                    self.legal = []
                    self.message = "New game started!"
                    continue
                break

            key = get_key()
            if key is None:
                continue

            # ── Navigation ──
            if key == 'UP':
                if self.flipped:
                    self.cursor[0] = min(7, self.cursor[0] + 1)
                else:
                    self.cursor[0] = max(0, self.cursor[0] - 1)
                self.message = ""

            elif key == 'DOWN':
                if self.flipped:
                    self.cursor[0] = max(0, self.cursor[0] - 1)
                else:
                    self.cursor[0] = min(7, self.cursor[0] + 1)
                self.message = ""

            elif key == 'LEFT':
                self.cursor[1] = max(0, self.cursor[1] - 1)
                self.message = ""

            elif key == 'RIGHT':
                self.cursor[1] = min(7, self.cursor[1] + 1)
                self.message = ""

            # ── Select / Move ──
            elif key == 'ENTER':
                self._handle_enter()

            # ── Deselect ──
            elif key in ('BACKSPACE', 'DELETE', 'ESC'):
                if self.selected:
                    self.selected = None
                    self.legal = []
                    self.message = "Deselected."
                else:
                    self.message = ""

            # ── Commands ──
            elif key.lower() == 'q':
                break
            elif key.lower() == 'h':
                self._show_help()
            elif key.lower() == 'm':
                self._show_moves()
            elif key.lower() == 'f':
                self.flipped = not self.flipped
                self.message = "Board flipped!"
            elif key.lower() == 'r':
                self.board.game_over = True
                self.board.winner = ('black'
                    if self.board.current_turn == 'white' else 'white')
                self.board.game_over_reason = 'resignation'

    # ── Enter Key Logic ───────────────────────

    def _handle_enter(self):
        cr, cc = self.cursor

        if self.selected is None:
            # ── Nothing selected → try to pick up a piece ──
            piece = self.board.get(cr, cc)
            if not piece:
                self.message = "Empty square. Pick one of your pieces!"
                return
            if self.board.color(piece) != self.board.current_turn:
                self.message = (
                    f"That's {self.board.color(piece)}'s piece! "
                    f"It's {self.board.current_turn}'s turn."
                )
                return
            moves = self.board.legal_moves(cr, cc)
            if not moves:
                self.message = (
                    f"That {PIECE_NAME[piece.upper()]} has "
                    "no legal moves right now."
                )
                return

            self.selected = (cr, cc)
            self.legal = moves
            self.message = (
                f"{PIECE_NAME[piece.upper()]} selected at "
                f"{square_name(cr, cc)}  —  "
                f"{len(moves)} move{'s' if len(moves) != 1 else ''} available"
            )

        else:
            # ── Piece already selected ──
            sr, sc = self.selected

            # Same square → deselect
            if (cr, cc) == (sr, sc):
                self.selected = None
                self.legal = []
                self.message = "Deselected."
                return

            # Clicking another friendly piece → switch selection
            target_piece = self.board.get(cr, cc)
            if (target_piece and
                self.board.color(target_piece) == self.board.current_turn):
                moves = self.board.legal_moves(cr, cc)
                if moves:
                    self.selected = (cr, cc)
                    self.legal = moves
                    self.message = (
                        f"Switched to {PIECE_NAME[target_piece.upper()]} "
                        f"at {square_name(cr, cc)}  —  "
                        f"{len(moves)} move{'s' if len(moves) != 1 else ''}"
                    )
                    return
                else:
                    self.message = (
                        f"That {PIECE_NAME[target_piece.upper()]} has "
                        "no legal moves."
                    )
                    return

            # Not a legal target
            if (cr, cc) not in self.legal:
                # Explain WHY it's illegal
                moving = self.board.get(sr, sc)
                self.message = (
                    f"Can't move {PIECE_NAME[moving.upper()]} there! "
                    "Look at the green/red highlighted squares."
                )
                return

            # ── Pawn promotion ──
            promo = None
            moving_piece = self.board.get(sr, sc)
            promo_row = 0 if self.board.current_turn == 'white' else 7
            if moving_piece and moving_piece.upper() == 'P' and cr == promo_row:
                promo = self._ask_promotion()

            # ── Execute the move ──
            ok, err = self.board.make_move(sr, sc, cr, cc, promo)
            if ok:
                self.selected = None
                self.legal = []
                last = self.board.move_history[-1]
                self.message = f"Played: {last}"
            else:
                self.message = err

    # ── Promotion Dialog ──────────────────────

    def _ask_promotion(self):
        """Interactive promotion: press Q/R/B/N."""
        self.message = (
            "PAWN PROMOTION! Press:  "
            "[Q] Queen   [R] Rook   [B] Bishop   [N] Knight"
        )
        self._render()
        while True:
            key = get_key()
            if key and key.upper() in ('Q', 'R', 'B', 'N'):
                return key.upper()

    # ── Board Rendering ───────────────────────

    def _render(self):
        """Build and display the full game screen.
        Uses in-place overwrite (no screen clear) for flicker-free rendering."""
        # Find king-in-check position for highlighting
        self._king_in_check_pos = None
        if self.board.is_in_check(self.board.current_turn):
            self._king_in_check_pos = self.board.find_king(
                self.board.current_turn
            )

        CLR = '\033[K'  # Clear to end of line (removes leftover chars)
        buf = []
        buf.append('\033[H')  # Move cursor home (NO screen clear = no flicker)

        # ── Title ──
        buf.append(f'\n{CLR}')
        buf.append(f'  ╔═══════════════════════════════════════════╗{CLR}\n')
        buf.append(f'  ║          A S C I I   C H E S S           ║{CLR}\n')
        buf.append(f'  ║            Interactive Mode               ║{CLR}\n')
        buf.append(f'  ╚═══════════════════════════════════════════╝{CLR}\n')
        buf.append(f'{CLR}\n')

        # ── Turn Indicator ──
        turn = self.board.current_turn.upper()
        if self.board.current_turn == 'white':
            buf.append(f'  {BOLD}{FG_CYAN}>>> {turn}\'s turn <<<{RESET}{CLR}\n')
        else:
            buf.append(f'  {BOLD}{FG_RED}>>> {turn}\'s turn <<<{RESET}{CLR}\n')
        buf.append(f'{CLR}\n')

        # ── Board ──
        if self.flipped:
            row_order = range(7, -1, -1)
            col_order = range(7, -1, -1)
            file_labels = '        h   g   f   e   d   c   b   a'
        else:
            row_order = range(8)
            col_order = range(8)
            file_labels = '        a   b   c   d   e   f   g   h'

        buf.append(f'{file_labels}{CLR}\n')
        buf.append(f'      +---+---+---+---+---+---+---+---+{CLR}\n')

        for r in row_order:
            rank_label = 8 - r
            buf.append(f'  {rank_label}   |')
            for c in col_order:
                cell_str = self._render_cell(r, c)
                buf.append(cell_str)
                buf.append(f'{RESET}|')
            buf.append(f'{CLR}\n')
            buf.append(f'      +---+---+---+---+---+---+---+---+{CLR}\n')

        buf.append(f'{file_labels}{CLR}\n')
        buf.append(f'{CLR}\n')

        # ── Legend ──
        buf.append(f'  Highlights:  ')
        buf.append(f'{REVERSE}{BOLD}[X]{RESET}=Cursor  ')
        buf.append(f'{BG_YELLOW}{FG_BLACK}{BOLD} X {RESET}=Selected  ')
        buf.append(f'{BG_GREEN}{FG_BLACK}{BOLD} + {RESET}=Can move  ')
        buf.append(f'{BG_RED}{FG_WHITE}{BOLD} x {RESET}=Capture{CLR}\n')
        buf.append(f'  Pieces:  UPPERCASE = White    lowercase = black{CLR}\n')
        buf.append(f'{CLR}\n')

        # ── Check / Checkmate Warning ──
        if self._king_in_check_pos:
            if self.board.game_over and self.board.game_over_reason == 'checkmate':
                buf.append(
                    f'  {BOLD}{BG_RED}{FG_WHITE}'
                    f' !!  CHECKMATE  !! {RESET}'
                    f'  {FG_RED}{BOLD}King is trapped!{RESET}{CLR}\n{CLR}\n'
                )
            else:
                buf.append(
                    f'  {BOLD}{BG_RED}{FG_WHITE}'
                    f' !! CHECK !! {RESET}'
                    f'  {FG_RED}{BOLD}Your King is under attack!{RESET}{CLR}\n{CLR}\n'
                )

        # ── Message ──
        if self.message:
            buf.append(f'  {self.message}{CLR}\n')
        buf.append(f'{CLR}\n')

        # ── Status Bar ──
        csq = square_name(self.cursor[0], self.cursor[1])
        cp  = self.board.get(self.cursor[0], self.cursor[1])
        if cp:
            cursor_info = f"{PIECE_NAME[cp.upper()]}({cp}) at {csq}"
        else:
            cursor_info = f"Empty at {csq}"
        buf.append(f'  Cursor: {BOLD}{cursor_info}{RESET}')

        if self.selected:
            ssq = square_name(self.selected[0], self.selected[1])
            sp  = self.board.get(self.selected[0], self.selected[1])
            if sp:
                buf.append(
                    f'    |    Selected: '
                    f'{BOLD}{FG_YELLOW}'
                    f'{PIECE_NAME[sp.upper()]}({sp}) at {ssq}'
                    f'{RESET}'
                )
        buf.append(f'{CLR}\n{CLR}\n')

        # ── Controls ──
        buf.append(
            f'  {FG_GRAY}[Arrows] Navigate   '
            f'[Enter] Select/Move   '
            f'[Backspace/Del] Deselect{RESET}{CLR}\n'
        )
        buf.append(
            f'  {FG_GRAY}[H] Help   '
            f'[M] Move History   '
            f'[F] Flip Board   '
            f'[R] Resign   '
            f'[Q] Quit{RESET}{CLR}\n'
        )

        # ── Last Move ──
        if self.board.move_history:
            last = self.board.move_history[-1]
            buf.append(f'{CLR}\n  Last move: {BOLD}{last}{RESET}{CLR}\n')

        # Clear any remaining lines below from previous renders
        buf.append('\033[J')

        sys.stdout.write(''.join(buf))
        sys.stdout.flush()

    def _render_cell(self, row, col):
        """
        Render a single board cell (3 visible chars)
        with ANSI highlights.

        Priority (highest first):
          0. King in check  →  flashing red background
          1. Cursor  →  [X]  with reverse video
          2. Selected piece  →  yellow background
          3. Legal capture  →  red background
          4. Legal empty move  →  green background
          5. Normal piece / empty square
        """
        piece = self.board.get(row, col)
        is_cursor   = (row == self.cursor[0] and col == self.cursor[1])
        is_selected = (self.selected is not None and
                       row == self.selected[0] and
                       col == self.selected[1])
        is_legal    = (row, col) in self.legal
        is_light    = (row + col) % 2 == 0  # Real chess: a1 is dark, h1 is light
        is_capture  = (is_legal and piece is not None and
                       self.board.is_enemy(piece, self.board.current_turn))

        # Check if this cell contains a king that is in check
        is_king_in_check = (
            self._king_in_check_pos is not None and
            row == self._king_in_check_pos[0] and
            col == self._king_in_check_pos[1]
        )

        # ── Build the 3-char cell content ──
        # Cursor uses [brackets] for extra visibility
        if piece:
            sym = piece  # Preserve case: uppercase=white, lower=black
            if is_cursor:
                content = f'[{sym}]'
            elif is_king_in_check:
                content = f'!{sym}!'  # Danger markers around checked king
            else:
                content = f' {sym} '
        else:
            if is_cursor:
                if is_legal:
                    content = '[+]'
                else:
                    content = '[ ]'
            elif is_legal:
                content = ' + '
            else:
                content = '   '  # Bg color shows light/dark, no dots needed

        # ── Apply ANSI styling ──

        # KING IN CHECK — highest visual priority (except cursor)
        if is_king_in_check and is_cursor:
            return f'{BG_RED}{FG_WHITE}{BOLD}{content}{RESET}'

        if is_king_in_check:
            return f'{BG_RED}{FG_WHITE}{BOLD}{content}{RESET}'

        if is_cursor and is_selected:
            return f'{BG_YELLOW}{FG_BLACK}{BOLD}{content}{RESET}'

        if is_cursor and is_capture:
            return f'{BG_RED}{FG_WHITE}{BOLD}{content}{RESET}'

        if is_cursor and is_legal:
            return f'{BG_GREEN}{FG_BLACK}{BOLD}{content}{RESET}'

        if is_cursor:
            return f'{REVERSE}{BOLD}{content}{RESET}'

        if is_selected:
            return f'{BG_YELLOW}{FG_BLACK}{BOLD}{content}{RESET}'

        if is_capture:
            return f'{BG_RED}{FG_WHITE}{BOLD}{content}{RESET}'

        if is_legal:
            return f'{BG_GREEN}{FG_BLACK}{BOLD}{content}{RESET}'

        # ── Normal (no highlight) — apply board square colors ──
        sq_bg = BG_LIGHT_SQ if is_light else BG_DARK_SQ
        if piece:
            if piece.isupper():
                # White piece: black text on light, white text on dark
                fg = FG_BLACK if is_light else FG_WHITE
                return f'{sq_bg}{fg}{BOLD}{content}{RESET}'
            else:
                # Black piece: red on light, bright red on dark
                fg = '\033[31m' if is_light else FG_RED
                return f'{sq_bg}{fg}{BOLD}{content}{RESET}'
        else:
            return f'{sq_bg}{content}{RESET}'

    # ── Game Over Screen ──────────────────────

    def _render_game_over(self):
        self._render()
        buf = []
        buf.append('\n')
        buf.append('  ╔═══════════════════════════════════════╗\n')
        buf.append('  ║            GAME  OVER!                ║\n')
        buf.append('  ╠═══════════════════════════════════════╣\n')
        if self.board.winner:
            w = self.board.winner.upper()
            reason = self.board.game_over_reason
            buf.append(f'  ║  {BOLD}{w} WINS!{RESET}')
            buf.append(f'{"":>{35 - len(w) - 7}}║\n')
            buf.append(f'  ║  by {reason}')
            buf.append(f'{"":>{35 - len(reason) - 4}}║\n')
        else:
            reason = self.board.game_over_reason
            buf.append(f'  ║  {BOLD}DRAW!{RESET}')
            buf.append(f'{"":>{35 - 5}}║\n')
            buf.append(f'  ║  ({reason})')
            buf.append(f'{"":>{35 - len(reason) - 3}}║\n')
        buf.append('  ╚═══════════════════════════════════════╝\n')
        buf.append('\n')
        buf.append('  Play again? [Y/N] ')
        sys.stdout.write(''.join(buf))
        sys.stdout.flush()

    # ── Help Screen ───────────────────────────

    def _show_help(self):
        buf = ['\033[H']
        buf.append('\n')
        buf.append('  ╔═════════════════════════════════════════════════╗\n')
        buf.append('  ║                 HOW TO PLAY                     ║\n')
        buf.append('  ╠═════════════════════════════════════════════════╣\n')
        buf.append('  ║                                                 ║\n')
        buf.append('  ║  1. Use ARROW KEYS to move the cursor           ║\n')
        buf.append('  ║  2. Press ENTER on your piece to select it      ║\n')
        buf.append('  ║  3. Green squares show where it can move        ║\n')
        buf.append('  ║  4. Red squares show pieces you can capture     ║\n')
        buf.append('  ║  5. Move cursor to a green/red square           ║\n')
        buf.append('  ║  6. Press ENTER to make the move!               ║\n')
        buf.append('  ║  7. Press BACKSPACE to change your mind         ║\n')
        buf.append('  ║                                                 ║\n')
        buf.append('  ╠═════════════════════════════════════════════════╣\n')
        buf.append('  ║                                                 ║\n')
        buf.append('  ║  CONTROLS:                                      ║\n')
        buf.append('  ║    Arrow Keys .... Navigate the board           ║\n')
        buf.append('  ║    Enter ......... Select piece / Confirm move  ║\n')
        buf.append('  ║    Backspace ..... Deselect piece               ║\n')
        buf.append('  ║    Delete / ESC .. Deselect piece               ║\n')
        buf.append('  ║    H ............. This help screen             ║\n')
        buf.append('  ║    M ............. Show move history            ║\n')
        buf.append('  ║    F ............. Flip the board               ║\n')
        buf.append('  ║    R ............. Resign                       ║\n')
        buf.append('  ║    Q ............. Quit game                    ║\n')
        buf.append('  ║                                                 ║\n')
        buf.append('  ╠═════════════════════════════════════════════════╣\n')
        buf.append('  ║                                                 ║\n')
        buf.append('  ║  CASTLING:                                      ║\n')
        buf.append('  ║    Select the King, then move it two squares    ║\n')
        buf.append('  ║    toward the rook. The game handles the rest!  ║\n')
        buf.append('  ║                                                 ║\n')
        buf.append('  ║  EN PASSANT:                                    ║\n')
        buf.append('  ║    After opponent moves pawn two squares,       ║\n')
        buf.append('  ║    the capture square glows automatically.      ║\n')
        buf.append('  ║                                                 ║\n')
        buf.append('  ║  PROMOTION:                                     ║\n')
        buf.append('  ║    Move pawn to last rank, then press           ║\n')
        buf.append('  ║    Q / R / B / N to choose the new piece.       ║\n')
        buf.append('  ║                                                 ║\n')
        buf.append('  ╚═════════════════════════════════════════════════╝\n')
        buf.append(f'\n  {FG_GRAY}Press any key to return...{RESET}\n')
        buf.append('\033[J')  # Clear remaining lines below
        sys.stdout.write(''.join(buf))
        sys.stdout.flush()
        get_key()

    # ── Move History Screen ───────────────────

    def _show_moves(self):
        buf = ['\033[H']
        buf.append('\n')
        buf.append('  ╔═══════════════════════════════════╗\n')
        buf.append('  ║          MOVE HISTORY             ║\n')
        buf.append('  ╠═══════════════════════════════════╣\n')
        if not self.board.move_history:
            buf.append('  ║  No moves yet.                   ║\n')
        else:
            for move in self.board.move_history:
                padded = move.ljust(31)
                buf.append(f'  ║  {padded}  ║\n')
        buf.append('  ╚═══════════════════════════════════╝\n')
        buf.append(f'\n  {FG_GRAY}Press any key to return...{RESET}\n')
        buf.append('\033[J')  # Clear remaining lines below
        sys.stdout.write(''.join(buf))
        sys.stdout.flush()
        get_key()


# ═══════════════════════════════════════════════
#  CLASSIC MODE  —  Text Input
# ═══════════════════════════════════════════════

class ClassicGame:
    """Type moves like 'e2 e4'. No arrow keys needed."""

    def __init__(self):
        self.board = ChessBoard()
        self.message = ""
        self.flipped = False

    def run(self):
        while True:
            self._render()

            if self.board.game_over:
                self._game_over()
                try:
                    again = input("  Play again? (y/n): ").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    break
                if again == 'y':
                    self.board = ChessBoard()
                    self.message = "New game!"
                    continue
                break

            try:
                prompt = f"  [{self.board.current_turn.upper()}] Enter move: "
                inp = input(prompt).strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not inp:
                continue
            cmd = inp.lower()

            if cmd in ('quit', 'exit', 'q'):
                break
            elif cmd == 'help':
                self._show_help()
                continue
            elif cmd == 'moves':
                self._show_moves()
                continue
            elif cmd == 'board':
                continue
            elif cmd == 'flip':
                self.flipped = not self.flipped
                self.message = "Board flipped!"
                continue
            elif cmd == 'resign':
                self.board.game_over = True
                enemy = ('black'
                    if self.board.current_turn == 'white' else 'white')
                self.board.winner = enemy
                self.board.game_over_reason = 'resignation'
                continue

            # Parse move
            parts = inp.split()
            if len(parts) != 2:
                self.message = "Invalid format! Use: e2 e4 (from to)"
                continue

            f = parse_square(parts[0])
            t = parse_square(parts[1])
            if not f:
                self.message = f"Bad square: {parts[0]}"
                continue
            if not t:
                self.message = f"Bad square: {parts[1]}"
                continue

            # Promotion check
            promo = None
            piece = self.board.get(f[0], f[1])
            if piece and piece.upper() == 'P':
                promo_row = 0 if self.board.current_turn == 'white' else 7
                if t[0] == promo_row:
                    while True:
                        try:
                            choice = input(
                                "  Promote to (Q/R/B/N): "
                            ).strip().upper()
                        except (EOFError, KeyboardInterrupt):
                            choice = 'Q'
                        if choice in ('Q', 'R', 'B', 'N'):
                            promo = choice
                            break
                        print("  Enter Q, R, B, or N!")

            ok, err = self.board.make_move(f[0], f[1], t[0], t[1], promo)
            if ok:
                self.message = f"Played: {self.board.move_history[-1]}"
            else:
                self.message = err

    def _render(self):
        clear_screen()
        print()
        print('  ╔═══════════════════════════════════════════╗')
        print('  ║          A S C I I   C H E S S           ║')
        print('  ║             Classic Mode                  ║')
        print('  ╚═══════════════════════════════════════════╝')
        print()

        turn = self.board.current_turn.upper()
        print(f'  >>> {turn}\'s turn <<<')
        print()

        if self.flipped:
            rows = range(7, -1, -1)
            cols = range(7, -1, -1)
            file_labels = '        h   g   f   e   d   c   b   a'
        else:
            rows = range(8)
            cols = range(8)
            file_labels = '        a   b   c   d   e   f   g   h'

        print(file_labels)
        print('      +---+---+---+---+---+---+---+---+')
        for r in rows:
            rank = 8 - r
            row_str = f'  {rank}   |'
            for c in cols:
                piece = self.board.get(r, c)
                is_light_sq = (r + c) % 2 == 0
                sq_bg = BG_LIGHT_SQ if is_light_sq else BG_DARK_SQ
                if piece:
                    if piece.isupper():
                        fg = FG_BLACK if is_light_sq else FG_WHITE
                    else:
                        fg = '\033[31m' if is_light_sq else FG_RED
                    row_str += f'{sq_bg}{fg}{BOLD} {piece} {RESET}|'
                else:
                    row_str += f'{sq_bg}   {RESET}|'
            print(row_str)
            print('      +---+---+---+---+---+---+---+---+')
        print(file_labels)
        print()
        print('  Legend:  UPPERCASE = White    lowercase = black')

        if (not self.board.game_over and
                self.board.is_in_check(self.board.current_turn)):
            print()
            print('  *** CHECK! ***')

        if self.board.move_history:
            print(f'\n  Last move: {self.board.move_history[-1]}')

        if self.message:
            print(f'\n  {self.message}')
        print()

    def _game_over(self):
        print()
        print('  ╔═══════════════════════════════════╗')
        print('  ║          GAME OVER!               ║')
        print('  ╠═══════════════════════════════════╣')
        if self.board.winner:
            w = self.board.winner.upper()
            reason = self.board.game_over_reason
            print(f'  ║  {w} WINS by {reason}!')
        else:
            reason = self.board.game_over_reason
            print(f'  ║  DRAW! ({reason})')
        print('  ╚═══════════════════════════════════╝')
        print()

    def _show_help(self):
        clear_screen()
        print()
        print('  ╔═══════════════════════════════════════════╗')
        print('  ║              COMMANDS                     ║')
        print('  ╠═══════════════════════════════════════════╣')
        print('  ║                                           ║')
        print('  ║  MOVING:                                  ║')
        print('  ║    Type: source destination               ║')
        print('  ║    Example: e2 e4                         ║')
        print('  ║    Example: g1 f3                         ║')
        print('  ║                                           ║')
        print('  ║  CASTLING:                                ║')
        print('  ║    e1 g1 = White kingside                 ║')
        print('  ║    e1 c1 = White queenside                ║')
        print('  ║    e8 g8 = Black kingside                 ║')
        print('  ║    e8 c8 = Black queenside                ║')
        print('  ║                                           ║')
        print('  ║  OTHER:                                   ║')
        print('  ║    help   - This screen                   ║')
        print('  ║    moves  - Move history                  ║')
        print('  ║    flip   - Flip board                    ║')
        print('  ║    resign - Resign                        ║')
        print('  ║    quit   - Exit                          ║')
        print('  ║                                           ║')
        print('  ╚═══════════════════════════════════════════╝')
        print()
        input('  Press Enter to continue...')

    def _show_moves(self):
        clear_screen()
        print()
        print('  ╔═══════════════════════════════════╗')
        print('  ║          MOVE HISTORY             ║')
        print('  ╠═══════════════════════════════════╣')
        if not self.board.move_history:
            print('  ║  No moves yet.                   ║')
        else:
            for move in self.board.move_history:
                padded = move.ljust(31)
                print(f'  ║  {padded}  ║')
        print('  ╚═══════════════════════════════════╝')
        print()
        input('  Press Enter to continue...')


# ═══════════════════════════════════════════════
#  MAIN  —  Mode Selection + Entry Point
# ═══════════════════════════════════════════════

