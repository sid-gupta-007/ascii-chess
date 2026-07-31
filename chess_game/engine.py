import copy
import random

PIECE_VALUES = {
    'P': 10, 'N': 30, 'B': 30, 'R': 50, 'Q': 90, 'K': 900,
    'p': -10, 'n': -30, 'b': -30, 'r': -50, 'q': -90, 'k': -900
}

class AIEngine:
    def __init__(self, depth=2):
        self.depth = depth

    def evaluate(self, board):
        score = 0
        for r in range(8):
            for c in range(8):
                piece = board.get(r, c)
                if piece:
                    score += PIECE_VALUES.get(piece, 0)
        return score

    def get_best_move(self, board):
        # Gather all legal moves for current player
        moves = self.get_all_moves(board, board.current_turn)
        if not moves:
            return None

        best_move = None
        maximizing = (board.current_turn == 'white')
        
        if maximizing:
            best_score = -float('inf')
        else:
            best_score = float('inf')

        # Shuffle moves to add variety
        random.shuffle(moves)

        for move in moves:
            sr, sc, er, ec = move
            promo = 'Q' if board.get(sr, sc).upper() == 'P' and (er == 0 or er == 7) else None

            sim_board = copy.deepcopy(board)
            sim_board.make_move(sr, sc, er, ec, promo)
            
            score = self.minimax(sim_board, self.depth - 1, not maximizing)
            
            if maximizing:
                if score > best_score:
                    best_score = score
                    best_move = (sr, sc, er, ec, promo)
            else:
                if score < best_score:
                    best_score = score
                    best_move = (sr, sc, er, ec, promo)

        if not best_move and moves:
            sr, sc, er, ec = random.choice(moves)
            promo = 'Q' if board.get(sr, sc).upper() == 'P' and (er == 0 or er == 7) else None
            best_move = (sr, sc, er, ec, promo)

        return best_move

    def minimax(self, board, depth, maximizing):
        if depth == 0 or board.game_over:
            return self.evaluate(board)

        moves = self.get_all_moves(board, board.current_turn)
        if not moves:
            return self.evaluate(board)
            
        if maximizing:
            best = -float('inf')
            for move in moves:
                sr, sc, er, ec = move
                promo = 'Q' if board.get(sr, sc).upper() == 'P' and (er == 0 or er == 7) else None
                sim = copy.deepcopy(board)
                sim.make_move(sr, sc, er, ec, promo)
                best = max(best, self.minimax(sim, depth - 1, False))
            return best
        else:
            best = float('inf')
            for move in moves:
                sr, sc, er, ec = move
                promo = 'Q' if board.get(sr, sc).upper() == 'P' and (er == 0 or er == 7) else None
                sim = copy.deepcopy(board)
                sim.make_move(sr, sc, er, ec, promo)
                best = min(best, self.minimax(sim, depth - 1, True))
            return best

    def get_all_moves(self, board, color):
        moves = []
        for r in range(8):
            for c in range(8):
                piece = board.get(r, c)
                if piece and board.color(piece) == color:
                    legal_targets = board.legal_moves(r, c)
                    for (er, ec) in legal_targets:
                        moves.append((r, c, er, ec))
        return moves
