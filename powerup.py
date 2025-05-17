class PowerUp:
    def __init__(self, x, y, powerup_type, cell_size):
        """
        Initialize a powerup
        
        Args:
            x, y: Position in the maze grid
            powerup_type: Type of powerup ("speed", "teleport", "wall_break", "score_multiplier", etc.)
            cell_size: Size of each cell for rendering
        """
        self.x = x
        self.y = y
        self.type = powerup_type
        self.cell_size = cell_size
        
        # Initialize timing for animations
        self.animation_time = 0
        self.active = True
        
        # Powerup properties
        self.duration = self._get_duration()
        self.strength = self._get_strength()
    
    def _get_duration(self):
        """Get duration based on powerup type"""
        durations = {
            "speed": 10,         # 10 seconds of speed boost
            "teleport": 0,       # instant effect
            "wall_break": 5,     # 5 seconds to break walls
            "score_multiplier": 20,  # 20 seconds of score multiplier
            "time_freeze": 10,   # 10 seconds time freeze
            "ghost": 8,          # 8 seconds to pass through walls
            "decay_freeze": 15   # 15 seconds of decay freeze
        }
        return durations.get(self.type, 0)
    
    def _get_strength(self):
        """Get strength/effect value based on powerup type"""
        strengths = {
            "speed": 2,          # 2x speed
            "teleport": 5,       # Teleport up to 5 cells closer to goal
            "wall_break": 3,     # Break up to 3 walls
            "score_multiplier": 2.5,  # 2.5x score multiplier
            "time_freeze": 1,    # Freeze time completely
            "ghost": 1           # Pass through walls
        }
        return strengths.get(self.type, 1)
    
    def update(self, dt):
        """Update powerup animation"""
        self.animation_time += dt
        
    def get_color(self):
        """Get powerup color based on type"""
        if self.type == "speed":
            return (255, 0, 0)  # Red
        elif self.type == "teleport":
            return (255, 165, 0)  # Orange
        elif self.type == "wall_break":
            return (139, 69, 19)  # Brown
        elif self.type == "score_multiplier":
            return (255, 215, 0)  # Gold
        elif self.type == "time_freeze":
            return (0, 255, 255)  # Cyan
        elif self.type == "ghost":
            return (220, 220, 220)  # Light Gray
        elif self.type == "objective":
            return (50, 205, 50)  # Lime Green
        elif self.type == "decay_freeze":
            return (255, 20, 147)  # Hot Pink
        else:
            return (128, 0, 128)  # Purple (default)
    
    def get_description(self):
        """Get description text for the powerup"""
        descriptions = {
            "speed": "Speed Boost: Move faster for a short time",
            "teleport": "Teleport: Moves you closer to the goal",
            "wall_break": "Wall Breaker: Break through walls temporarily",
            "score_multiplier": "Score Multiplier: Increases points earned",
            "time_freeze": "Time Freeze: Stops the timer temporarily",
            "ghost": "Ghost Mode: Pass through walls without breaking them",
            "objective": "Objective: Collect for extra points!",
            "decay_freeze": "Decay Shield: Prevents score decay temporarily"
        }
        return descriptions.get(self.type, "Unknown Powerup") 