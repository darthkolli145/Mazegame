"""
Game settings for the Maze Runner game
"""

# Game window settings
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
GAME_TITLE = "Maze Runner"
FPS = 30

# Maze settings
DEFAULT_MAZE_WIDTH = 15
DEFAULT_MAZE_HEIGHT = 15
CELL_SIZE = 30

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
    "easy": 3,
    "medium": 5,
    "hard": 7
}

# Portal settings
PORTAL_PAIR_COUNTS = {
    "easy": 2,
    "medium": 3,
    "hard": 4
}

# Game difficulty settings
DIFFICULTIES = {
    "easy": {
        "maze_size": (10, 10),
        "time_factor": 5,  # Lower time factor means more time available
        "move_penalty": 2  # Lower move penalty means less score reduction
    },
    "medium": {
        "maze_size": (15, 15),
        "time_factor": 10,
        "move_penalty": 5
    },
    "hard": {
        "maze_size": (20, 20),
        "time_factor": 15,
        "move_penalty": 8
    }
}

# Algorithm settings
ALGORITHM_SPEED = 10  # Steps per second

# You can modify these settings to change game behavior 