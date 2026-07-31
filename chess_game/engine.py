"""
Chess Engine
============================================

HOW THIS ENGINE WORKS (for learning):
--------------------------------------
1. SEARCH: The engine "thinks" by recursively trying every possible move,
   then every response, then every counter-response... up to a certain depth.
   
   - Alpha-Beta Pruning: Skips branches that can't possibly be better than
     what we've already found. Like saying "I already found a move that wins
     a knight. This other branch loses my queen on move 1, so no matter what
     happens after, it's worse. Skip it."
   
   - Quiescence Search: When we hit our depth limit, don't stop if pieces
     are being traded. Keep searching captures until things calm down.
     This prevents: "I'm winning!" → next move opponent takes your queen.
   
   - Move Ordering: Check the best-looking moves first (captures, checks).
     This makes alpha-beta prune WAY more branches.

2. EVALUATION: When we reach the bottom of the search tree, we need to
   answer: "Who's winning in this position?" We score it using:
   
   - Material: Count pieces. Queen=900, Rook=500, Bishop=330, Knight=320, Pawn=100
   - Piece-Square Tables: Bonus/penalty for WHERE each piece sits.
     Knight in center = +20, knight on edge = -40.
   - Pawn Structure: Doubled pawns = bad. Passed pawns = good.
   - King Safety: Pawns shielding your king = good.
   - Mobility: More legal moves = more flexibility = good.

3. OPENING BOOK: For the first few moves, play known good moves from a
   dictionary instead of searching. Saves time and plays proper openings.

4. PERSONALITIES: Same engine, different evaluation weights.
   "The Attacker" values mobility 1.5x. "The Wall" values king safety 1.5x.
   Completely different playstyles from the same code.
"""

import copy
import random
import time

# ═══════════════════════════════════════════════
#  PIECE VALUES (in centipawns: 100 = 1 pawn)
# ═══════════════════════════════════════════════
# WHY these numbers? They're the standard values refined over decades.
# Bishop slightly > Knight because two bishops together are very strong.

PIECE_VALUES = {
    'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000,
    'p': 100, 'n': 320, 'b': 330, 'r': 500, 'q': 900, 'k': 20000,
}

# ═══════════════════════════════════════════════
#  PIECE-SQUARE TABLES
# ═══════════════════════════════════════════════
# Each table is 64 values (8x8 board) from WHITE's perspective.
# Positive = good square for this piece. Negative = bad square.
# For BLACK, we mirror the table vertically.
#
# These encode chess knowledge like:
# - Knights love the center, hate the edges
# - Pawns should advance, especially center pawns
# - King should castle in middlegame, centralize in endgame

# fmt: off
PAWN_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,   # rank 8 (promotion rank - never has pawns)
    50, 50, 50, 50, 50, 50, 50, 50,   # rank 7 (about to promote = very valuable)
    10, 10, 20, 30, 30, 20, 10, 10,   # rank 6
     5,  5, 10, 25, 25, 10,  5,  5,   # rank 5
     0,  0,  0, 20, 20,  0,  0,  0,   # rank 4 (center pawns get bonus)
     5, -5,-10,  0,  0,-10, -5,  5,   # rank 3
     5, 10, 10,-20,-20, 10, 10,  5,   # rank 2 (starting pos, penalize blocking center)
     0,  0,  0,  0,  0,  0,  0,  0,   # rank 1 (never has pawns)
]

KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,   # edges are TERRIBLE for knights
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,   # center is PERFECT
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]

BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,   # bishops like long diagonals
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]

ROOK_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,   # 7th rank rooks are powerful
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0,   # slight bonus near castled king
]

QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,   # queen likes center but don't rush her out
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
]

# King MIDDLEGAME: hide behind pawns, castle
KING_MG_TABLE = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,   # castled positions are great
     20, 30, 10,  0,  0, 10, 30, 20,   # g1/c1 = castled king = very safe
]

# King ENDGAME: go to the center!
KING_EG_TABLE = [
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,   # center is king in endgame
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50,
]

PST = {
    'P': PAWN_TABLE, 'N': KNIGHT_TABLE, 'B': BISHOP_TABLE,
    'R': ROOK_TABLE, 'Q': QUEEN_TABLE, 'K': KING_MG_TABLE,
}
# fmt: on


# ═══════════════════════════════════════════════
#  OPENING BOOK
# ═══════════════════════════════════════════════
# Each entry: move_history_as_coords → list of good next moves
# Stored as tuples: (from_row, from_col, to_row, to_col)
# Multiple options per position add variety.

OPENING_BOOK = {
    # ── White's first move ──
    (): [
        (6, 4, 4, 4),  # 1. e4 (King's pawn)
        (6, 3, 4, 3),  # 1. d4 (Queen's pawn)
        (6, 2, 4, 2),  # 1. c4 (English)
        (7, 6, 5, 5),  # 1. Nf3 (Reti)
    ],

    # ── After 1. e4 ──
    ((6,4,4,4),): [
        (1, 4, 3, 4),  # 1...e5
        (1, 2, 3, 2),  # 1...c5 (Sicilian)
        (1, 4, 2, 4),  # 1...e6 (French)
        (1, 2, 2, 2),  # 1...c6 (Caro-Kann)
    ],

    # ── After 1. e4 e5 ──
    ((6,4,4,4), (1,4,3,4)): [
        (7, 6, 5, 5),  # 2. Nf3 (most common)
    ],

    # ── After 1. e4 e5 2. Nf3 ──
    ((6,4,4,4), (1,4,3,4), (7,6,5,5)): [
        (0, 1, 2, 2),  # 2...Nc6 (normal)
    ],

    # ── After 1. e4 e5 2. Nf3 Nc6 → Italian or Ruy Lopez ──
    ((6,4,4,4), (1,4,3,4), (7,6,5,5), (0,1,2,2)): [
        (7, 5, 4, 2),  # 3. Bc4 (Italian)
        (7, 5, 3, 1),  # 3. Bb5 (Ruy Lopez)
        (6, 3, 4, 3),  # 3. d4 (Scotch)
    ],

    # ── After 1. e4 c5 (Sicilian) ──
    ((6,4,4,4), (1,2,3,2)): [
        (7, 6, 5, 5),  # 2. Nf3
    ],
    ((6,4,4,4), (1,2,3,2), (7,6,5,5)): [
        (1, 3, 2, 3),  # 2...d6
        (0, 1, 2, 2),  # 2...Nc6
    ],

    # ── After 1. d4 ──
    ((6,3,4,3),): [
        (1, 3, 3, 3),  # 1...d5
        (0, 6, 2, 5),  # 1...Nf6
    ],

    # ── After 1. d4 d5 ──
    ((6,3,4,3), (1,3,3,3)): [
        (6, 2, 4, 2),  # 2. c4 (Queen's Gambit)
        (7, 2, 4, 5),  # 2. Bf4 (London System)
    ],

    # ── After 1. d4 Nf6 ──
    ((6,3,4,3), (0,6,2,5)): [
        (6, 2, 4, 2),  # 2. c4
    ],
    ((6,3,4,3), (0,6,2,5), (6,2,4,2)): [
        (1, 6, 2, 6),  # 2...g6 (King's Indian)
        (1, 4, 2, 4),  # 2...e6 (Nimzo/QGD setup)
    ],

    # ── After 1. d4 d5 2. c4 (Queen's Gambit) ──
    ((6,3,4,3), (1,3,3,3), (6,2,4,2)): [
        (1, 4, 2, 4),  # 2...e6 (QGD)
        (3, 3, 4, 2),  # 2...dxc4 (QGA)
    ],
}


# ═══════════════════════════════════════════════
#  PERSONALITY SYSTEM
# ═══════════════════════════════════════════════
# Each personality is a dict of weight multipliers for the evaluation.
# Same engine code, completely different playstyle!

PERSONALITIES = {
    'attacker': {
        'name': '🗡️  The Attacker',
        'desc': 'Aggressive. Sacrifices for initiative.',
        'material': 0.9,       # slightly less afraid to sacrifice
        'position': 1.0,
        'mobility': 1.5,       # LOVES having lots of moves
        'king_safety': 0.6,    # not scared about own king
        'pawn_structure': 0.7,
        'king_attack': 1.8,    # LIVES to attack opponent's king
        'depth': 3,
        'random_pct': 0,
    },
    'wall': {
        'name': '🛡️  The Wall',
        'desc': 'Ultra-defensive. Gives nothing away.',
        'material': 1.2,       # very material-conscious
        'position': 1.0,
        'mobility': 0.8,
        'king_safety': 1.8,    # obsessed with king safety
        'pawn_structure': 1.5,  # loves solid pawns
        'king_attack': 0.5,    # doesn't push for attacks
        'depth': 3,
        'random_pct': 0,
    },
    'gambler': {
        'name': '🎲  The Gambler',
        'desc': 'Unpredictable. Brilliant or terrible.',
        'material': 1.0,
        'position': 1.0,
        'mobility': 1.0,
        'king_safety': 1.0,
        'pawn_structure': 1.0,
        'king_attack': 1.0,
        'depth': 3,
        'random_pct': 30,      # 30% chance of random move!
    },
    'grinder': {
        'name': '⚙️  The Grinder',
        'desc': 'Trades pieces. Squeezes endgames.',
        'material': 1.3,       # loves being ahead in material
        'position': 1.2,
        'mobility': 0.7,
        'king_safety': 1.0,
        'pawn_structure': 1.4,  # pawn endings are their bread and butter
        'king_attack': 0.6,
        'depth': 3,
        'random_pct': 0,
    },
    'scholar': {
        'name': '📚  The Scholar',
        'desc': 'Theory nerd. Strong openings.',
        'material': 1.0,
        'position': 1.3,       # very positional
        'mobility': 1.0,
        'king_safety': 1.0,
        'pawn_structure': 1.2,
        'king_attack': 0.8,
        'depth': 3,
        'random_pct': 0,
        'book_depth': 20,      # follows book much longer
    },
}

# Difficulty presets (used when player picks a level instead of personality)
DIFFICULTY = {
    1: {'depth': 2, 'random_pct': 25, 'use_pst': False, 'use_book': False},  # Easy
    2: {'depth': 3, 'random_pct': 0,  'use_pst': True,  'use_book': True},   # Medium
    3: {'depth': 4, 'random_pct': 0,  'use_pst': True,  'use_book': True},   # Hard
}


# ═══════════════════════════════════════════════
#  ZOBRIST HASHING
# ═══════════════════════════════════════════════
# Fast way to uniquely identify a chess position.
# Each (piece, square) gets a random 64-bit number.
# Position hash = XOR of all piece-square numbers.
# Why XOR? It's reversible: hash ^ piece_added ^ piece_removed = new hash

_ZOBRIST_RNG = random.Random(42)  # Fixed seed = same numbers every run
ZOBRIST_PIECES = {}
for _p in 'PNBRQKpnbrqk':
    ZOBRIST_PIECES[_p] = [_ZOBRIST_RNG.getrandbits(64) for _ in range(64)]
ZOBRIST_BLACK_TO_MOVE = _ZOBRIST_RNG.getrandbits(64)
ZOBRIST_CASTLING = {k: _ZOBRIST_RNG.getrandbits(64) for k in 'KQkq'}
ZOBRIST_EP = [_ZOBRIST_RNG.getrandbits(64) for _ in range(8)]  # one per file


def zobrist_hash(board):
    """Compute the Zobrist hash of a ChessBoard position."""
    h = 0
    for r in range(8):
        for c in range(8):
            piece = board.get(r, c)
            if piece:
                h ^= ZOBRIST_PIECES[piece][r * 8 + c]
    if board.current_turn == 'black':
        h ^= ZOBRIST_BLACK_TO_MOVE
    for k in 'KQkq':
        if board.castling.get(k, False):
            h ^= ZOBRIST_CASTLING[k]
    if board.en_passant:
        h ^= ZOBRIST_EP[board.en_passant[1]]
    return h


# ═══════════════════════════════════════════════
#  THE ENGINE
# ═══════════════════════════════════════════════

class AIEngine:
    """
    The chess AI. Call get_best_move(board) and it returns the best move.
    
    Usage:
        engine = AIEngine(depth=3)                    # by difficulty level
        engine = AIEngine(personality='attacker')     # by personality
        move = engine.get_best_move(board)
        # move = (from_row, from_col, to_row, to_col, promotion_piece_or_None)
    """

    def __init__(self, depth=3, personality=None, level=None):
        # Personality mode
        if personality and personality in PERSONALITIES:
            p = PERSONALITIES[personality]
            self.depth = p['depth']
            self.weights = {
                'material': p['material'],
                'position': p['position'],
                'mobility': p['mobility'],
                'king_safety': p['king_safety'],
                'pawn_structure': p['pawn_structure'],
                'king_attack': p.get('king_attack', 1.0),
            }
            self.random_pct = p['random_pct']
            self.use_pst = True
            self.use_book = True
            self.personality = personality
        # Difficulty level mode
        elif level and level in DIFFICULTY:
            d = DIFFICULTY[level]
            self.depth = d['depth']
            self.weights = {k: 1.0 for k in
                           ['material','position','mobility',
                            'king_safety','pawn_structure','king_attack']}
            self.random_pct = d['random_pct']
            self.use_pst = d['use_pst']
            self.use_book = d['use_book']
            self.personality = None
        # Raw depth mode (backward compatible)
        else:
            self.depth = depth
            self.weights = {k: 1.0 for k in
                           ['material','position','mobility',
                            'king_safety','pawn_structure','king_attack']}
            self.random_pct = 0
            self.use_pst = True
            self.use_book = True
            self.personality = None

        # Transposition table: hash → (depth, score, flag, best_move)
        # flag: 'exact', 'lower', 'upper'
        self.tt = {}
        self.tt_hits = 0

        # Killer moves: moves that caused beta cutoffs, indexed by depth
        self.killers = [[None, None] for _ in range(64)]

        # Stats for debugging
        self.nodes_searched = 0

    # ── MAIN ENTRY POINT ─────────────────────

    def get_best_move(self, board):
        """Find the best move for the current position."""
        self.nodes_searched = 0
        self.tt_hits = 0
        start_time = time.time()

        # 1. Check opening book first
        if self.use_book:
            book_move = self._book_lookup(board)
            if book_move:
                sr, sc, er, ec = book_move
                promo = self._get_promo(board, sr, sc, er, ec)
                return (sr, sc, er, ec, promo)

        # 2. Get all legal moves
        moves = self._get_all_moves(board)
        if not moves:
            return None

        # 3. Random move chance (for Easy mode / Gambler)
        if self.random_pct > 0 and random.randint(1, 100) <= self.random_pct:
            sr, sc, er, ec = random.choice(moves)
            promo = self._get_promo(board, sr, sc, er, ec)
            return (sr, sc, er, ec, promo)

        # 4. Iterative deepening: search depth 1, then 2, ... up to max
        #    Each iteration's best move orders the next iteration
        best_move = None
        maximizing = (board.current_turn == 'white')

        for d in range(1, self.depth + 1):
            move, score = self._search_root(board, d, moves, maximizing)
            if move:
                best_move = move
                # Put the best move first for next iteration
                if move in moves:
                    moves.remove(move)
                    moves.insert(0, move)

        # Fallback
        if not best_move and moves:
            sr, sc, er, ec = random.choice(moves)
            promo = self._get_promo(board, sr, sc, er, ec)
            return (sr, sc, er, ec, promo)

        elapsed = time.time() - start_time
        return best_move

    # ── ROOT SEARCH ──────────────────────────

    def _search_root(self, board, depth, moves, maximizing):
        """Search at the root level, returning (best_move_tuple, score)."""
        alpha = -999999
        beta = 999999
        best_move = None
        best_score = -999999 if maximizing else 999999

        ordered = self._order_moves(board, moves, 0)

        for sr, sc, er, ec in ordered:
            promo = self._get_promo(board, sr, sc, er, ec)
            sim = board.clone()
            sim.make_move(sr, sc, er, ec, promo)

            # Check extension: if this move gives check, search 1 deeper
            extension = 1 if sim.is_in_check(sim.current_turn) else 0

            if maximizing:
                score = self._alpha_beta(sim, depth - 1 + extension,
                                         alpha, beta, False)
                if score > best_score:
                    best_score = score
                    best_move = (sr, sc, er, ec, promo)
                alpha = max(alpha, score)
            else:
                score = self._alpha_beta(sim, depth - 1 + extension,
                                         alpha, beta, True)
                if score < best_score:
                    best_score = score
                    best_move = (sr, sc, er, ec, promo)
                beta = min(beta, score)

        return best_move, best_score

    # ── ALPHA-BETA SEARCH ────────────────────

    def _alpha_beta(self, board, depth, alpha, beta, maximizing):
        """
        Alpha-Beta pruning — the core search algorithm.
        
        alpha = best score the MAXIMIZER can guarantee (starts at -infinity)
        beta  = best score the MINIMIZER can guarantee (starts at +infinity)
        
        If alpha >= beta, we PRUNE (skip remaining moves) because:
        - The maximizer already has a move scoring `alpha`
        - The minimizer already has a move scoring `beta`
        - Since alpha >= beta, neither side will allow this branch to happen
        """
        self.nodes_searched += 1

        # Check transposition table
        h = zobrist_hash(board)
        tt_entry = self.tt.get(h)
        if tt_entry and tt_entry[0] >= depth:
            self.tt_hits += 1
            tt_depth, tt_score, tt_flag, tt_move = tt_entry
            if tt_flag == 'exact':
                return tt_score
            elif tt_flag == 'lower':
                alpha = max(alpha, tt_score)
            elif tt_flag == 'upper':
                beta = min(beta, tt_score)
            if alpha >= beta:
                return tt_score

        # Base case: reached depth limit → quiescence search
        if depth <= 0:
            return self._quiescence(board, alpha, beta, maximizing)

        # Game over check
        if board.game_over:
            return self._eval_terminal(board)

        moves = self._get_all_moves(board)
        if not moves:
            # No moves = checkmate or stalemate
            if board.is_in_check(board.current_turn):
                # Checkmate: very bad for the side to move
                return -99999 if maximizing else 99999
            return 0  # Stalemate = draw

        ordered = self._order_moves(board, moves, depth)
        best_score = -999999 if maximizing else 999999
        best_move = None
        original_alpha = alpha

        for sr, sc, er, ec in ordered:
            promo = self._get_promo(board, sr, sc, er, ec)
            sim = board.clone()
            sim.make_move(sr, sc, er, ec, promo)

            # Check extension
            extension = 1 if sim.is_in_check(sim.current_turn) else 0

            if maximizing:
                score = self._alpha_beta(sim, depth - 1 + extension,
                                         alpha, beta, False)
                if score > best_score:
                    best_score = score
                    best_move = (sr, sc, er, ec)
                alpha = max(alpha, score)
            else:
                score = self._alpha_beta(sim, depth - 1 + extension,
                                         alpha, beta, True)
                if score < best_score:
                    best_score = score
                    best_move = (sr, sc, er, ec)
                beta = min(beta, score)

            # PRUNING: this is where the magic happens!
            if alpha >= beta:
                # Store as killer move (non-capture that caused cutoff)
                if board.get(er, ec) is None and depth < 64:
                    self.killers[depth] = [
                        (sr, sc, er, ec),
                        self.killers[depth][0]
                    ]
                break

        # Store in transposition table
        if best_score <= original_alpha:
            flag = 'upper'
        elif best_score >= beta:
            flag = 'lower'
        else:
            flag = 'exact'
        self.tt[h] = (depth, best_score, flag, best_move)

        return best_score

    # ── QUIESCENCE SEARCH ────────────────────

    def _quiescence(self, board, alpha, beta, maximizing):
        """
        Continue searching CAPTURE MOVES only until position is quiet.
        
        This prevents the "horizon effect":
        Without this, the engine might think "I'm up a pawn!" but can't see
        that on the very next move, opponent captures our queen.
        """
        self.nodes_searched += 1

        stand_pat = self.evaluate(board)

        if maximizing:
            if stand_pat >= beta:
                return beta
            alpha = max(alpha, stand_pat)
        else:
            if stand_pat <= alpha:
                return alpha
            beta = min(beta, stand_pat)

        # Only search CAPTURES (not all moves)
        captures = self._get_captures(board)

        for sr, sc, er, ec in captures:
            promo = self._get_promo(board, sr, sc, er, ec)
            sim = board.clone()
            sim.make_move(sr, sc, er, ec, promo)

            score = self._quiescence(sim, alpha, beta, not maximizing)

            if maximizing:
                if score >= beta:
                    return beta
                alpha = max(alpha, score)
            else:
                if score <= alpha:
                    return alpha
                beta = min(beta, score)

        return alpha if maximizing else beta

    # ── MOVE ORDERING ────────────────────────

    def _order_moves(self, board, moves, depth):
        """
        Order moves so the best-looking ones are checked first.
        Good ordering = alpha-beta prunes more branches = much faster.
        
        Order:
        1. Captures (sorted by MVV/LVA — capture valuable pieces with cheap ones first)
        2. Killer moves (non-captures that caused cutoffs at same depth before)
        3. Everything else
        """
        scored = []
        for move in moves:
            sr, sc, er, ec = move
            score = 0
            target = board.get(er, ec)
            attacker = board.get(sr, sc)

            # MVV/LVA: Most Valuable Victim / Least Valuable Attacker
            # Capturing a queen with a pawn = great (score: 900 - 100 + 10000 = 10800)
            # Capturing a pawn with a queen = meh (score: 100 - 900 + 10000 = 9200)
            if target:
                victim_val = PIECE_VALUES.get(target.upper(), 0)
                attacker_val = PIECE_VALUES.get(attacker.upper(), 0) if attacker else 0
                score = victim_val - attacker_val + 10000  # captures always first

            # Killer move bonus
            elif depth < 64 and move in self.killers[depth]:
                score = 5000

            # Pawn promotion bonus
            if attacker and attacker.upper() == 'P' and (er == 0 or er == 7):
                score += 8000

            scored.append((score, move))

        scored.sort(key=lambda x: -x[0])
        return [m for _, m in scored]

    # ── EVALUATION FUNCTION ──────────────────

    def evaluate(self, board):
        """
        Evaluate a position. Positive = white is better, negative = black.
        """
        if board.game_over:
            return self._eval_terminal(board)

        # ── Memory Check (Avoid blunders) ──
        # If this position is in memory, apply the penalty.
        # This gives the engine a basic form of learning!
        h = zobrist_hash(board)
        if not hasattr(self, 'memory'):
            try:
                from player_data import AIMemory
                self.memory = AIMemory()
            except ImportError:
                self.memory = None
                
        memory_penalty = self.memory.get_penalty(h) if self.memory else 0

        w = self.weights
        score = 0 + memory_penalty

        # Count total material for endgame detection
        total_material = 0
        white_bishops = 0
        black_bishops = 0

        # ── Material + Piece-Square Tables ──
        for r in range(8):
            for c in range(8):
                piece = board.get(r, c)
                if not piece:
                    continue

                pt = piece.upper()
                val = PIECE_VALUES.get(pt, 0)
                total_material += val

                if piece.isupper():  # White
                    score += val * w['material']
                    if self.use_pst and pt in PST:
                        score += PST[pt][r * 8 + c] * w['position']
                    if pt == 'B':
                        white_bishops += 1
                else:  # Black
                    score -= val * w['material']
                    if self.use_pst and pt in PST:
                        # Mirror table for black (flip row)
                        score -= PST[pt][(7 - r) * 8 + c] * w['position']
                    if pt == 'B':
                        black_bishops += 1

        # ── Endgame King Table ──
        # If little material left, use endgame king table instead
        is_endgame = total_material < 2600  # roughly: no queens, few pieces
        if is_endgame and self.use_pst:
            wk = board.find_king('white')
            bk = board.find_king('black')
            if wk:
                # Remove middlegame king score, add endgame
                score -= KING_MG_TABLE[wk[0] * 8 + wk[1]] * w['position']
                score += KING_EG_TABLE[wk[0] * 8 + wk[1]] * w['position']
            if bk:
                score += KING_MG_TABLE[(7 - bk[0]) * 8 + bk[1]] * w['position']
                score -= KING_EG_TABLE[(7 - bk[0]) * 8 + bk[1]] * w['position']

        # ── Bishop Pair ──
        if white_bishops >= 2:
            score += 30 * w['material']
        if black_bishops >= 2:
            score -= 30 * w['material']

        # ── Mobility ──
        white_mobility = len(self._get_all_moves_for_color(board, 'white'))
        black_mobility = len(self._get_all_moves_for_color(board, 'black'))
        score += (white_mobility - black_mobility) * 3 * w['mobility']

        # ── Pawn Structure ──
        score += self._eval_pawns(board) * w['pawn_structure']

        # ── King Safety ──
        score += self._eval_king_safety(board) * w['king_safety']

        return int(score)

    def _eval_terminal(self, board):
        """Score for game-over positions."""
        if board.winner == 'white':
            return 99999
        elif board.winner == 'black':
            return -99999
        return 0  # draw

    def _eval_pawns(self, board):
        """Evaluate pawn structure: doubled, isolated, passed pawns."""
        score = 0
        white_pawns_per_file = [0] * 8
        black_pawns_per_file = [0] * 8

        # Count pawns per file
        for r in range(8):
            for c in range(8):
                p = board.get(r, c)
                if p == 'P':
                    white_pawns_per_file[c] += 1
                elif p == 'p':
                    black_pawns_per_file[c] += 1

        for c in range(8):
            # Doubled pawns (2+ pawns on same file = bad)
            if white_pawns_per_file[c] > 1:
                score -= 15 * (white_pawns_per_file[c] - 1)
            if black_pawns_per_file[c] > 1:
                score += 15 * (black_pawns_per_file[c] - 1)

            # Isolated pawns (no friendly pawns on adjacent files)
            if white_pawns_per_file[c] > 0:
                left = white_pawns_per_file[c - 1] if c > 0 else 0
                right = white_pawns_per_file[c + 1] if c < 7 else 0
                if left == 0 and right == 0:
                    score -= 20

            if black_pawns_per_file[c] > 0:
                left = black_pawns_per_file[c - 1] if c > 0 else 0
                right = black_pawns_per_file[c + 1] if c < 7 else 0
                if left == 0 and right == 0:
                    score += 20

        # Passed pawns (no enemy pawns can block or capture)
        for r in range(8):
            for c in range(8):
                p = board.get(r, c)
                if p == 'P':
                    # Check if any black pawns ahead on same or adjacent files
                    is_passed = True
                    for check_r in range(0, r):
                        for dc in (-1, 0, 1):
                            cc = c + dc
                            if 0 <= cc < 8 and board.get(check_r, cc) == 'p':
                                is_passed = False
                                break
                        if not is_passed:
                            break
                    if is_passed:
                        # Bonus increases as pawn advances (closer to promotion)
                        score += (7 - r) * 10

                elif p == 'p':
                    is_passed = True
                    for check_r in range(r + 1, 8):
                        for dc in (-1, 0, 1):
                            cc = c + dc
                            if 0 <= cc < 8 and board.get(check_r, cc) == 'P':
                                is_passed = False
                                break
                        if not is_passed:
                            break
                    if is_passed:
                        score -= r * 10

        return score

    def _eval_king_safety(self, board):
        """Evaluate king safety based on pawn shield."""
        score = 0

        # White king safety
        wk = board.find_king('white')
        if wk:
            kr, kc = wk
            # Check pawn shield (pawns in front of king)
            shield_bonus = 0
            for dc in (-1, 0, 1):
                sc = kc + dc
                if 0 <= sc < 8:
                    # Check 1-2 rows in front of king
                    if kr - 1 >= 0 and board.get(kr - 1, sc) == 'P':
                        shield_bonus += 10
                    elif kr - 2 >= 0 and board.get(kr - 2, sc) == 'P':
                        shield_bonus += 5
            score += shield_bonus

        # Black king safety
        bk = board.find_king('black')
        if bk:
            kr, kc = bk
            shield_bonus = 0
            for dc in (-1, 0, 1):
                sc = kc + dc
                if 0 <= sc < 8:
                    if kr + 1 < 8 and board.get(kr + 1, sc) == 'p':
                        shield_bonus += 10
                    elif kr + 2 < 8 and board.get(kr + 2, sc) == 'p':
                        shield_bonus += 5
            score -= shield_bonus

        return score

    # ── HELPER METHODS ───────────────────────

    def _book_lookup(self, board):
        """Check if current position matches any opening book line."""
        # Convert move history to coordinate tuples
        # The board stores moves as notation strings, but we need coords.
        # We use last_move_coords stored by board for matching.
        # Build key from move count — simple approach using move_history length
        history_len = len(board.move_history)

        # Try to match by replaying from start
        # Simple approach: just check if we're in early game with few moves
        if history_len > 12:  # Past opening phase
            return None

        # Build the key: sequence of (sr, sc, er, ec) tuples
        # We can't easily reconstruct this from notation, so we use a
        # different approach: match by board position against known positions
        # For simplicity, only use book for first move
        key = self._build_book_key(board)
        if key is not None and key in OPENING_BOOK:
            candidates = OPENING_BOOK[key]
            # Verify the move is actually legal
            legal = self._get_all_moves(board)
            valid = [m for m in candidates if m in legal]
            if valid:
                return random.choice(valid)
        return None

    def _build_book_key(self, board):
        """Build the opening book lookup key from board state."""
        # For this to work properly, we need to track move coordinates
        # throughout the game. Since board.last_move_coords only stores
        # the LAST move, we use a simpler approach:
        # Store the full coordinate history on the engine instance.
        if not hasattr(self, '_move_coord_history'):
            self._move_coord_history = ()

        return self._move_coord_history

    def record_move(self, sr, sc, er, ec):
        """Call this after each move to update the book tracking."""
        if not hasattr(self, '_move_coord_history'):
            self._move_coord_history = ()
        self._move_coord_history = self._move_coord_history + ((sr, sc, er, ec),)

    def _get_promo(self, board, sr, sc, er, ec):
        """Determine promotion piece if applicable."""
        piece = board.get(sr, sc)
        if piece and piece.upper() == 'P' and (er == 0 or er == 7):
            return 'Q'  # Always promote to queen (best choice 99% of time)
        return None

    def _get_all_moves(self, board):
        """Get all legal moves for the current player."""
        return self._get_all_moves_for_color(board, board.current_turn)

    def _get_all_moves_for_color(self, board, color):
        """Get all legal moves for a specific color."""
        moves = []
        for r in range(8):
            for c in range(8):
                piece = board.get(r, c)
                if piece and board.color(piece) == color:
                    for er, ec in board.legal_moves(r, c):
                        moves.append((r, c, er, ec))
        return moves

    def _get_captures(self, board):
        """Get only capture moves for current player (for quiescence)."""
        captures = []
        for r in range(8):
            for c in range(8):
                piece = board.get(r, c)
                if piece and board.color(piece) == board.current_turn:
                    for er, ec in board.legal_moves(r, c):
                        target = board.get(er, ec)
                        # Include captures and en passant
                        if target is not None:
                            captures.append((r, c, er, ec))
                        elif (piece.upper() == 'P' and
                              board.en_passant and
                              (er, ec) == board.en_passant):
                            captures.append((r, c, er, ec))
        return captures

    def learn_from_loss(self, board, ai_color):
        """
        When the AI loses, penalize the last few positions it was in.
        This forms a persistent memory of fatal traps and mistakes,
        allowing the AI to avoid them in future games.
        """
        if not hasattr(self, 'memory') or not self.memory:
            try:
                from player_data import AIMemory
                self.memory = AIMemory()
            except ImportError:
                return

        # Reconstruct the game and penalize the final critical states
        from board import ChessBoard
        sim_board = ChessBoard()
        
        total_moves = len(board.raw_move_history)
        
        for i, move in enumerate(board.raw_move_history):
            # We only penalize positions where it was the AI's turn to choose a move
            if sim_board.current_turn == ai_color:
                moves_until_loss = total_moves - i
                
                # If we are within the last 5 full moves (10 half-moves) of the loss
                if moves_until_loss <= 10:
                    h = zobrist_hash(sim_board)
                    # The closer to the loss, the heavier the penalty
                    penalty = 50 + (10 - moves_until_loss) * 20
                    self.memory.record_bad_position(h, penalty_cp=penalty)
                    
            sr, sc, er, ec, promo = move
            sim_board.make_move(sr, sc, er, ec, promo)
