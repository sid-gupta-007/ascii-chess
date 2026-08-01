"""
Player Data & Memory System
===========================

Handles local JSON persistence for:
1. Player Profile: Stats, accuracy, "ELO" (skill rating), history.
2. AI Memory: Positions where the AI lost badly, to avoid in future games.
"""

import json
import os

PROFILE_FILE = "player_profile.json"
MEMORY_FILE = "ai_memory.json"

class PlayerProfile:
    def __init__(self):
        self.data = self._load()

    def _load(self):
        if os.path.exists(PROFILE_FILE):
            try:
                with open(PROFILE_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'rating': 800,
            'games_played': 0,
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'avg_accuracy': 0.0,
            'history': []
        }

    def _save(self):
        with open(PROFILE_FILE, 'w') as f:
            json.dump(self.data, f, indent=4)

    def update_after_game(self, result, difficulty_level, accuracy):
        """
        result: 'win', 'loss', or 'draw'
        difficulty_level: 1, 2, or 3
        accuracy: 0.0 to 100.0
        """
        self.data['games_played'] += 1
        
        # Update average accuracy
        n = self.data['games_played']
        old_acc = self.data['avg_accuracy']
        self.data['avg_accuracy'] = ((old_acc * (n - 1)) + accuracy) / n

        # Basic ELO-style rating change
        # Higher difficulty = more points for win, fewer lost for loss
        expected_score = {1: 0.8, 2: 0.5, 3: 0.2}.get(difficulty_level, 0.5)
        
        actual_score = 1 if result == 'win' else (0 if result == 'loss' else 0.5)
        
        k_factor = 32
        rating_change = k_factor * (actual_score - expected_score)
        
        # Bonus for high accuracy, penalty for low
        if accuracy > 90:
            rating_change += 10
        elif accuracy < 40:
            rating_change -= 10
            
        self.data['rating'] = max(100, int(self.data['rating'] + rating_change))
        
        if result == 'win': self.data['wins'] += 1
        elif result == 'loss': self.data['losses'] += 1
        else: self.data['draws'] += 1
        
        self.data['history'].append({
            'result': result,
            'level': difficulty_level,
            'accuracy': round(accuracy, 1),
            'rating_change': int(rating_change)
        })
        
        # Keep history manageable
        if len(self.data['history']) > 50:
            self.data['history'] = self.data['history'][-50:]
            
        self._save()
        return int(rating_change)

    def get_stats_string(self):
        d = self.data
        return (f"Rating: {d['rating']} | "
                f"W: {d['wins']} L: {d['losses']} D: {d['draws']} | "
                f"Avg Acc: {d['avg_accuracy']:.1f}%")


class AIMemory:
    """
    Very simple learning mechanism.
    If the AI blunders a position and loses, it remembers the Zobrist hash
    of that position and assigns a penalty so it avoids it next time.
    """
    def __init__(self):
        self.memory = self._load()

    def _load(self):
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, 'r') as f:
                    # JSON keys are strings, convert back to int hashes
                    data = json.load(f)
                    return {int(k): v for k, v in data.items()}
            except:
                pass
        return {}

    def _save(self):
        with open(MEMORY_FILE, 'w') as f:
            # Convert int keys to strings for JSON
            data = {str(k): v for k, v in self.memory.items()}
            json.dump(data, f)

    def record_bad_position(self, zobrist_hash, penalty_cp=100):
        """Record that a position is bad and should be penalized."""
        # Penalty increases if we see it again
        current = self.memory.get(zobrist_hash, 0)
        self.memory[zobrist_hash] = current - penalty_cp
        self._save()

    def get_penalty(self, zobrist_hash):
        return self.memory.get(zobrist_hash, 0)
