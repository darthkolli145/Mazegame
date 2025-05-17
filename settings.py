"""
Game settings for the Maze Runner game
"""

# Game window settings
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800
GAME_TITLE = "Maze Runner"
FPS = 30

# Maze settings
DEFAULT_MAZE_WIDTH = 15
DEFAULT_MAZE_HEIGHT = 15
CELL_SIZE = 25  # Reduced cell size to fit larger mazes on screen

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)

# Powerup settings
POWERUP_COUNTS = {
    "easy": 1,
    "medium": 2,
    "hard": 3
}

# Portal settings
PORTAL_PAIR_COUNTS = {
    "easy": 1,
    "medium": 1,
    "hard": 2
}

# Game difficulty settings
DIFFICULTIES = {
    "easy": {
        "maze_size": (15, 15),    # Level 1 maze size
        "time_factor": 5,         # Lower time factor means more time available
        "move_penalty": 2         # Lower move penalty means less score reduction
    },
    "medium": {
        "maze_size": (19, 19),    # Level 2 maze size
        "time_factor": 10,
        "move_penalty": 5
    },
    "hard": {
        "maze_size": (23, 23),    # Level 3 maze size
        "time_factor": 15,
        "move_penalty": 8
    }
}

# Algorithm settings
ALGORITHM_SPEED = 10  # Steps per second

# You can modify these settings to change game behavior 