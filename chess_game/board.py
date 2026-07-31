from utils import square_name

class ChessBoard:
    """
    Full chess rules engine.
    Handles move generation, validation, check,
    checkmate, stalemate, castling, en passant,
    pawn promotion, and the 50-move rule.
    """

    def __init__(self):
        self.board = [[None]*8 for _ in range(8)]
        self.current_turn = 'white'
        self.move_history = []
        self.raw_move_history = []
        self.castling = {
            'K': True, 'Q': True,   # white kingside / queenside
            'k': True, 'q': True,   # black kingside / queenside
        }
        self.en_passant = None    # target square (row, col)
        self.halfmove = 0
        self.fullmove = 1
        self.game_over = False
        self.winner = None
        self.game_over_reason = ''
        self.last_move_coords = None

        # Timers
        self.time_limit = None
        self.increment = 0
        self.white_time = None
        self.black_time = None
        self.last_tick = None
        
        self._setup()

    def clone(self):
        """Fast clone for search tree, avoiding slow copy.deepcopy."""
        new_board = ChessBoard.__new__(ChessBoard)
        new_board.board = [row[:] for row in self.board]
        new_board.current_turn = self.current_turn
        new_board.castling = self.castling.copy()
        new_board.en_passant = self.en_passant
        new_board.halfmove = self.halfmove
        new_board.fullmove = self.fullmove
        new_board.game_over = self.game_over
        new_board.winner = self.winner
        new_board.game_over_reason = self.game_over_reason
        new_board.last_move_coords = self.last_move_coords
        
        # We don't need history for search tree copies
        new_board.move_history = []
        new_board.raw_move_history = []
        
        # Don't clone timer states for search
        new_board.time_limit = None
        new_board.last_tick = None
        
        return new_board

    def set_timer(self, time_limit, increment):
        self.time_limit = time_limit
        self.increment = increment
        if time_limit is not None:
            self.white_time = float(time_limit)
            self.black_time = float(time_limit)
        else:
            self.white_time = None
            self.black_time = None

    def update_timer(self):
        if self.time_limit is None or self.game_over:
            return
            
        # Don't start the clock until the first move is made
        if not self.move_history:
            return
        
        import time
        now = time.time()
        if self.last_tick is None:
            self.last_tick = now
            return
            
        elapsed = now - self.last_tick
        self.last_tick = now
        
        if self.current_turn == 'white':
            self.white_time -= elapsed
            if self.white_time <= 0:
                self.white_time = 0
                self.game_over = True
                self.winner = 'black'
                self.game_over_reason = 'Timeout'
        else:
            self.black_time -= elapsed
            if self.black_time <= 0:
                self.black_time = 0
                self.game_over = True
                self.winner = 'white'
                self.game_over_reason = 'Timeout'

    # ── Initial Position ──────────────────────

    def _setup(self):
        self.board[0] = list('rnbqkbnr')
        self.board[1] = list('pppppppp')
        for r in range(2, 6):
            self.board[r] = [None] * 8
        self.board[6] = list('PPPPPPPP')
        self.board[7] = list('RNBQKBNR')

    # ── Accessors ─────────────────────────────

    def get(self, r, c):
        if 0 <= r < 8 and 0 <= c < 8:
            return self.board[r][c]
        return None

    def color(self, piece):
        if piece is None:
            return None
        return 'white' if piece.isupper() else 'black'

    def is_enemy(self, piece, my_color):
        return piece is not None and self.color(piece) != my_color

    def is_friendly(self, piece, my_color):
        return piece is not None and self.color(piece) == my_color

    # ── Pseudo-Legal Move Generation ──────────

    def pseudo_moves(self, r, c):
        """All candidate moves for a piece (ignoring check)."""
        piece = self.get(r, c)
        if not piece:
            return []
        col = self.color(piece)
        pt  = piece.upper()

        if pt == 'P':  return self._pawn_moves(r, c, col)
        if pt == 'N':  return self._knight_moves(r, c, col)
        if pt == 'B':  return self._slide(r, c, col, [(-1,-1),(-1,1),(1,-1),(1,1)])
        if pt == 'R':  return self._slide(r, c, col, [(-1,0),(1,0),(0,-1),(0,1)])
        if pt == 'Q':  return self._slide(r, c, col, [(-1,-1),(-1,1),(1,-1),(1,1),
                                                       (-1,0),(1,0),(0,-1),(0,1)])
        if pt == 'K':  return self._king_moves(r, c, col)
        return []

    def _pawn_moves(self, r, c, col):
        moves = []
        d = -1 if col == 'white' else 1
        start_row = 6 if col == 'white' else 1

        # Forward one
        nr = r + d
        if 0 <= nr < 8 and self.board[nr][c] is None:
            moves.append((nr, c))
            # Forward two from start
            nr2 = r + 2*d
            if r == start_row and self.board[nr2][c] is None:
                moves.append((nr2, c))

        # Diagonal captures
        for dc in (-1, 1):
            nr, nc = r + d, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                target = self.board[nr][nc]
                if self.is_enemy(target, col):
                    moves.append((nr, nc))
                # En passant
                if self.en_passant and (nr, nc) == self.en_passant:
                    moves.append((nr, nc))
        return moves

    def _knight_moves(self, r, c, col):
        moves = []
        for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),
                        (1,-2),(1,2),(2,-1),(2,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                if not self.is_friendly(self.board[nr][nc], col):
                    moves.append((nr, nc))
        return moves

    def _slide(self, r, c, col, directions):
        moves = []
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 8 and 0 <= nc < 8:
                target = self.board[nr][nc]
                if target is None:
                    moves.append((nr, nc))
                elif self.is_enemy(target, col):
                    moves.append((nr, nc))
                    break
                else:
                    break
                nr += dr
                nc += dc
        return moves

    def _king_moves(self, r, c, col):
        moves = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    if not self.is_friendly(self.board[nr][nc], col):
                        moves.append((nr, nc))

        # ── Castling ──
        enemy = 'black' if col == 'white' else 'white'
        home_row = 7 if col == 'white' else 0

        if r == home_row and c == 4 and not self.is_in_check(col):
            rook_char = 'R' if col == 'white' else 'r'
            # Kingside
            ck = 'K' if col == 'white' else 'k'
            if self.castling[ck]:
                if (self.board[home_row][5] is None and
                    self.board[home_row][6] is None and
                    self.board[home_row][7] == rook_char):
                    if (not self.square_attacked(home_row, 5, enemy) and
                        not self.square_attacked(home_row, 6, enemy)):
                        moves.append((home_row, 6))
            # Queenside
            cq = 'Q' if col == 'white' else 'q'
            if self.castling[cq]:
                if (self.board[home_row][3] is None and
                    self.board[home_row][2] is None and
                    self.board[home_row][1] is None and
                    self.board[home_row][0] == rook_char):
                    if (not self.square_attacked(home_row, 3, enemy) and
                        not self.square_attacked(home_row, 2, enemy)):
                        moves.append((home_row, 2))
        return moves

    # ── Check / Attack Detection ──────────────

    def find_king(self, col):
        king = 'K' if col == 'white' else 'k'
        for r in range(8):
            for c in range(8):
                if self.board[r][c] == king:
                    return (r, c)
        return None

    def _attack_squares(self, r, c, piece):
        """Squares attacked by a piece (for check detection).
        Pawns attack diagonally only."""
        col = self.color(piece)
        pt  = piece.upper()

        if pt == 'P':
            d = -1 if col == 'white' else 1
            return [(r+d, c+dc) for dc in (-1, 1)
                    if 0 <= r+d < 8 and 0 <= c+dc < 8]
        if pt == 'N':
            return self._knight_moves(r, c, col)
        if pt == 'B':
            return self._slide(r, c, col, [(-1,-1),(-1,1),(1,-1),(1,1)])
        if pt == 'R':
            return self._slide(r, c, col, [(-1,0),(1,0),(0,-1),(0,1)])
        if pt == 'Q':
            return self._slide(r, c, col, [(-1,-1),(-1,1),(1,-1),(1,1),
                                            (-1,0),(1,0),(0,-1),(0,1)])
        if pt == 'K':
            return [(r+dr, c+dc)
                    for dr in (-1,0,1) for dc in (-1,0,1)
                    if not (dr == 0 and dc == 0)
                    and 0 <= r+dr < 8 and 0 <= c+dc < 8]
        return []

    def square_attacked(self, row, col, by_color):
        """Is the square attacked by any piece of by_color?"""
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p and self.color(p) == by_color:
                    if (row, col) in self._attack_squares(r, c, p):
                        return True
        return False

    def is_in_check(self, col):
        """Is the given color's king in check?"""
        kp = self.find_king(col)
        if not kp:
            return False
        enemy = 'black' if col == 'white' else 'white'
        return self.square_attacked(kp[0], kp[1], enemy)

    # ── Legal Move Filtering ─────────────────

    def _move_is_legal(self, fr, fc, tr, tc, col):
        """Test if a move leaves own king safe."""
        piece = self.board[fr][fc]
        captured = self.board[tr][tc]
        ep_piece = None
        ep_pos = None

        # Simulate en passant capture removal
        if piece.upper() == 'P' and self.en_passant == (tr, tc):
            ep_pos = (fr, tc)
            ep_piece = self.board[fr][tc]
            self.board[fr][tc] = None

        self.board[tr][tc] = piece
        self.board[fr][fc] = None
        in_check = self.is_in_check(col)
        self.board[fr][fc] = piece
        self.board[tr][tc] = captured

        if ep_pos:
            self.board[ep_pos[0]][ep_pos[1]] = ep_piece

        return not in_check

    def legal_moves(self, r, c):
        """All fully-legal moves for the piece at (r, c)."""
        piece = self.get(r, c)
        if not piece:
            return []
        col = self.color(piece)
        return [(tr, tc) for tr, tc in self.pseudo_moves(r, c)
                if self._move_is_legal(r, c, tr, tc, col)]

    def has_any_legal_moves(self, col):
        """Does the player have at least one legal move?"""
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p and self.color(p) == col:
                    if self.legal_moves(r, c):
                        return True
        return False

    # ── Execute a Move ────────────────────────

    def make_move(self, fr, fc, tr, tc, promo=None, check_end=True):
        """
        Execute a move. Returns (success: bool, error_msg: str).
        promo should be 'Q','R','B', or 'N' for pawn promotion.
        """
        self.update_timer()  # Deduct time spent thinking BEFORE switching turns
        
        piece = self.board[fr][fc]
        if not piece:
            return False, "No piece at that square."
        col = self.color(piece)
        if col != self.current_turn:
            return False, f"It's {self.current_turn}'s turn!"

        legal = self.legal_moves(fr, fc)
        if (tr, tc) not in legal:
            return False, "Illegal move!"

        captured = self.board[tr][tc]
        notation = self._notation(fr, fc, tr, tc, piece, captured)

        # ── En passant capture ──
        if piece.upper() == 'P' and self.en_passant == (tr, tc):
            self.board[fr][tc] = None
            notation += " e.p."

        # ── Move piece ──
        self.board[tr][tc] = piece
        self.board[fr][fc] = None

        # ── Castling rook movement ──
        if piece.upper() == 'K' and abs(fc - tc) == 2:
            if tc == 6:  # Kingside
                self.board[tr][5] = self.board[tr][7]
                self.board[tr][7] = None
                notation = "O-O"
            else:        # Queenside
                self.board[tr][3] = self.board[tr][0]
                self.board[tr][0] = None
                notation = "O-O-O"

        # ── Pawn promotion ──
        promo_row = 0 if col == 'white' else 7
        if piece.upper() == 'P' and tr == promo_row:
            if not promo:
                promo = 'Q'
            promo_piece = promo.upper() if col == 'white' else promo.lower()
            self.board[tr][tc] = promo_piece
            notation += f"={promo.upper()}"

        # ── Update castling rights ──
        if piece.upper() == 'K':
            if col == 'white':
                self.castling['K'] = self.castling['Q'] = False
            else:
                self.castling['k'] = self.castling['q'] = False

        if piece.upper() == 'R':
            if (fr, fc) == (7, 0): self.castling['Q'] = False
            if (fr, fc) == (7, 7): self.castling['K'] = False
            if (fr, fc) == (0, 0): self.castling['q'] = False
            if (fr, fc) == (0, 7): self.castling['k'] = False

        if captured and captured.upper() == 'R':
            if (tr, tc) == (7, 0): self.castling['Q'] = False
            if (tr, tc) == (7, 7): self.castling['K'] = False
            if (tr, tc) == (0, 0): self.castling['q'] = False
            if (tr, tc) == (0, 7): self.castling['k'] = False

        # ── Update en passant target ──
        self.en_passant = None
        if piece.upper() == 'P' and abs(fr - tr) == 2:
            self.en_passant = ((fr + tr) // 2, fc)

        # ── Update 50-move clock ──
        if piece.upper() == 'P' or captured:
            self.halfmove = 0
        else:
            self.halfmove += 1
            
        # ── Update time controls ──
        if getattr(self, 'time_limit', None) is not None and getattr(self, 'last_tick', None) is not None:
            if col == 'white':
                self.white_time += self.increment
            else:
                self.black_time += self.increment

        # ── Check end conditions ──
        enemy = 'black' if col == 'white' else 'white'
        
        if check_end:
            in_check = self.is_in_check(enemy)
            has_moves = self.has_any_legal_moves(enemy)

            if in_check and not has_moves:
                notation += "#"
                self.game_over = True
                self.winner = col
                self.game_over_reason = 'checkmate'
            elif in_check:
                notation += "+"
            elif not has_moves:
                self.game_over = True
                self.winner = None
                self.game_over_reason = 'stalemate'

        if self.halfmove >= 100:
            self.game_over = True
            self.winner = None
            self.game_over_reason = '50-move rule'

        # ── Record move ──
        n = self.fullmove
        if col == 'white':
            self.move_history.append(f"{n}. {notation}")
        else:
            self.move_history.append(f"{n}...{notation}")
            self.fullmove += 1

        self.last_move_coords = ((fr, fc), (tr, tc))
        self.raw_move_history.append((fr, fc, tr, tc, promo))

        self.current_turn = enemy
        return True, ""

    def _notation(self, fr, fc, tr, tc, piece, captured):
        to_sq = square_name(tr, tc)
        if piece.upper() == 'P':
            return f"{chr(fc + ord('a'))}x{to_sq}" if captured else to_sq
        cap = 'x' if captured else '-'
        return f"{piece.upper()}{cap}{to_sq}"


# ═══════════════════════════════════════════════
#  INTERACTIVE MODE  —  Arrow Keys + Enter
# ═══════════════════════════════════════════════

