"""
Post-Game Analysis Engine
=========================

Analyzes a completed game by re-evaluating each position with the AI Engine.
Classifies moves based on the change in centipawn evaluation:
  - Brilliant  (found a better move than engine expected)
  - Great      (top engine move)
  - Good       (minor centipawn loss)
  - Inaccuracy (moderate centipawn loss)
  - Mistake    (large centipawn loss)
  - Blunder    (game-losing centipawn loss)
"""

from board import ChessBoard
from engine import AIEngine
import copy

class GameAnalyzer:
    def __init__(self, depth=3):
        self.engine = AIEngine(depth=depth)
        # Use a high depth but basic personality for raw strength evaluation
        self.engine.weights = {
            'material': 1.0, 'position': 1.0, 'mobility': 1.0,
            'king_safety': 1.0, 'pawn_structure': 1.0, 'king_attack': 1.0
        }
        self.engine.random_pct = 0
        self.engine.use_pst = True
        self.engine.use_book = False  # Evaluate based purely on position

    def analyze_game(self, finished_board, player_color):
        """
        Takes a finished board and re-runs the game from start.
        Returns a list of analysis dicts for the PLAYER'S moves.
        """
        # Recreate a fresh board
        sim_board = ChessBoard()
        
        results = []
        raw_moves = finished_board.raw_move_history
        notation_moves = finished_board.move_history

        # We need to pair raw moves with their string notation.
        # Note: move_history strings are like "1. e4" or "1...e5"
        
        for i, move_tuple in enumerate(raw_moves):
            sr, sc, er, ec, promo = move_tuple
            current_turn = sim_board.current_turn
            notation = notation_moves[i]

            # Only deeply analyze the player's moves to save time
            if current_turn == player_color:
                # 1. Ask engine for the evaluation BEFORE the move
                # To do this, we run a shallow search to get the "expected" score
                # We'll just do depth 2 for speed, or use the engine's depth
                _, expected_score = self.engine._search_root(sim_board, self.engine.depth, self.engine._get_all_moves(sim_board), current_turn == 'white')
                
                # Make the move
                sim_board.make_move(sr, sc, er, ec, promo)
                
                # 2. Evaluate the position AFTER the move
                # If it's white's turn (after black played), the score is from white's perspective
                # so we need to run another search to see how good the position is now
                _, actual_score = self.engine._search_root(sim_board, self.engine.depth, self.engine._get_all_moves(sim_board), sim_board.current_turn == 'white')
                
                # Calculate centipawn loss
                # If player is white, they want HIGH scores.
                # Expected: +150. Actual (after move, evaluated by engine): +30.
                # Loss = Expected - Actual = 120.
                #
                # If player is black, they want LOW scores (negative).
                # Expected: -150. Actual: -30.
                # Loss = Actual - Expected = -30 - (-150) = 120.
                
                if player_color == 'white':
                    cp_loss = expected_score - actual_score
                else:
                    cp_loss = actual_score - expected_score

                # Clamp loss (can't have negative loss unless they found a better move than depth 3 engine)
                cp_loss = max(-50, cp_loss)

                classification = self._classify_move(cp_loss)
                
                results.append({
                    'move_num': (i // 2) + 1,
                    'notation': notation,
                    'cp_loss': cp_loss,
                    'classification': classification,
                    'board_state': copy.deepcopy(sim_board.board)
                })
            else:
                # Computer's move, just apply it
                sim_board.make_move(sr, sc, er, ec, promo)

        return self._generate_report(results)

    def _classify_move(self, cp_loss):
        if cp_loss < 0:
            return "Brilliant"
        elif cp_loss <= 10:
            return "Great"
        elif cp_loss <= 30:
            return "Good"
        elif cp_loss <= 80:
            return "Inaccuracy"
        elif cp_loss <= 200:
            return "Mistake"
        else:
            return "Blunder"

    def _generate_report(self, results):
        if not results:
            return None

        counts = {
            "Brilliant": 0,
            "Great": 0,
            "Good": 0,
            "Inaccuracy": 0,
            "Mistake": 0,
            "Blunder": 0,
        }
        
        blunders = []
        mistakes = []
        total_loss = 0

        for r in results:
            counts[r['classification']] += 1
            total_loss += max(0, r['cp_loss'])
            
            if "Blunder" in r['classification']:
                blunders.append(r)
            elif "Mistake" in r['classification']:
                mistakes.append(r)

        avg_loss = total_loss / max(1, len(results))
        # Accuracy: 0 loss = 100%, 50 loss = 75%, 100 loss = 50%, 200 loss = 0%
        accuracy = max(0.0, 100.0 - (avg_loss / 2.0))

        report = {
            'accuracy': accuracy,
            'counts': counts,
            'blunders': blunders,
            'mistakes': mistakes,
            'full_analysis': results
        }
        return report
