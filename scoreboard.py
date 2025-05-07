import os
import json

class Scoreboard:
    def __init__(self, save_file="maze_scores.json"):
        self.scores = []
        self.save_file = save_file
        self.load_scores()
    
    def add_score(self, player_name, score):
        """Add a new score to the scoreboard"""
        self.scores.append((player_name, score))
        # Sort scores in descending order
        self.scores.sort(key=lambda x: x[1], reverse=True)
        self.save_scores()
    
    def get_high_scores(self, limit=10):
        """Get the top scores"""
        return self.scores[:limit]
    
    def load_scores(self):
        """Load scores from file"""
        try:
            if os.path.exists(self.save_file):
                with open(self.save_file, 'r') as f:
                    self.scores = json.load(f)
            else:
                # Initialize with some default scores if file doesn't exist
                self.scores = [
                    ("AI", 2000),
                    ("Bob", 1800),
                    ("Alice", 1500),
                    ("Charlie", 1200),
                    ("Player", 1000)
                ]
                self.save_scores()
        except Exception as e:
            print(f"Error loading scores: {e}")
            self.scores = []
    
    def save_scores(self):
        """Save scores to file"""
        try:
            with open(self.save_file, 'w') as f:
                json.dump(self.scores, f)
        except Exception as e:
            print(f"Error saving scores: {e}")
    
    def reset_scores(self):
        """Reset all scores"""
        self.scores = []
        self.save_scores() 