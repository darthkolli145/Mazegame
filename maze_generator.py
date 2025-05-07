import random
import numpy as np

class MazeGenerator:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # Initialize maze with all walls
        # True represents a wall, False represents a path
        self.maze = np.ones((height, width), dtype=bool)
    
    def generate(self):
        """Generate a random maze using Randomized Depth-First Search algorithm"""
        # Start with all walls
        self.maze = np.ones((self.height, self.width), dtype=bool)
        
        # Start at a random cell
        start_x, start_y = 0, 0  # Always start at top-left for consistency
        self.maze[start_y, start_x] = False  # Mark as path
        
        # Call recursive function to carve paths
        self._carve_paths(start_x, start_y)
        
        # Ensure start and end are open
        self.maze[0, 0] = False  # Start (top-left)
        self.maze[self.height-1, self.width-1] = False  # End (bottom-right)
        
        return self.maze
    
    def _carve_paths(self, x, y):
        """Recursive function to carve paths through the maze"""
        # Define the four possible directions to move
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # Down, Right, Up, Left
        
        # Shuffle directions to get randomness
        random.shuffle(directions)
        
        # Try each direction
        for dx, dy in directions:
            new_x, new_y = x + dx*2, y + dy*2  # Move two cells in the chosen direction
            
            # Check if the new position is valid and still a wall
            if (0 <= new_x < self.width and 0 <= new_y < self.height and self.maze[new_y, new_x]):
                # Carve path by making cells False (not walls)
                self.maze[y + dy, x + dx] = False  # Carve wall between current and new cell
                self.maze[new_y, new_x] = False    # Carve the new cell
                
                # Continue from the new cell
                self._carve_paths(new_x, new_y)
    
    def get_maze(self):
        """Return the current maze"""
        return self.maze
    
    def print_maze(self):
        """Print the maze to console for debugging"""
        for y in range(self.height):
            for x in range(self.width):
                if self.maze[y, x]:
                    print("█", end="")  # Wall
                else:
                    print(" ", end="")  # Path
            print() 