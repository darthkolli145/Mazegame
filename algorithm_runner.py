import importlib.util
import sys
from collections import deque

class AlgorithmRunner:
    def __init__(self, maze, maze_size):
        self.maze = maze
        self.maze_size = maze_size
        self.custom_algorithm = None
        self.path = []
        self.current_path_index = 0
        self.loaded_algorithm = False
    
    def load_algorithm_from_file(self, file_path):
        """
        Load a user-defined algorithm from a Python file.
        The file should contain a function called 'solve_maze'
        """
        try:
            # Load the module from file path
            spec = importlib.util.spec_from_file_location("custom_algorithm", file_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules["custom_algorithm"] = module
            spec.loader.exec_module(module)
            
            # Check if the required function exists
            if hasattr(module, 'solve_maze'):
                self.custom_algorithm = module.solve_maze
                self.loaded_algorithm = True
                return True
            else:
                print("Error: The file does not contain a 'solve_maze' function.")
                return False
        except Exception as e:
            print(f"Error loading algorithm: {e}")
            return False
    
    def compute_path(self, start_pos, goal_pos):
        """Compute a path through the maze"""
        if self.loaded_algorithm and self.custom_algorithm:
            # Use the user-defined algorithm
            try:
                self.path = self.custom_algorithm(self.maze, start_pos, goal_pos)
                self.current_path_index = 0
                return True
            except Exception as e:
                print(f"Error executing user algorithm: {e}")
                # Fall back to default algorithm
                self.path = self._default_algorithm(start_pos, goal_pos)
                self.current_path_index = 0
                return True
        else:
            # Use default algorithm
            self.path = self._default_algorithm(start_pos, goal_pos)
            self.current_path_index = 0
            return True
    
    def _default_algorithm(self, start_pos, goal_pos):
        """
        Default algorithm - Breadth-First Search
        Returns a list of (x, y) coordinates forming a path from start to goal
        """
        start_x, start_y = start_pos
        goal_x, goal_y = goal_pos
        
        # Check if start or goal are walls
        if self.maze[start_y][start_x] or self.maze[goal_y][goal_x]:
            return []
        
        # Directions: right, down, left, up
        directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        
        # BFS queue
        queue = deque([(start_x, start_y)])
        
        # Track visited cells and the path taken
        visited = {(start_x, start_y): None}  # (x,y): (parent_x, parent_y)
        
        # BFS
        while queue:
            x, y = queue.popleft()
            
            # Goal check
            if (x, y) == (goal_x, goal_y):
                # Reconstruct path
                path = []
                current = (x, y)
                while current != (start_x, start_y):
                    path.append(current)
                    current = visited[current]
                path.append((start_x, start_y))
                path.reverse()
                return path
            
            # Try each direction
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                
                # Check if valid move
                if (0 <= nx < self.maze_size[0] and 
                    0 <= ny < self.maze_size[1] and 
                    not self.maze[ny][nx] and 
                    (nx, ny) not in visited):
                    queue.append((nx, ny))
                    visited[(nx, ny)] = (x, y)
        
        # No path found
        return []
    
    def get_next_move(self, current_x, current_y, goal_pos):
        """
        Get the next move from the computed path
        Returns a tuple (dx, dy) to move the player
        """
        if not self.path:
            # No path computed yet, compute it
            self.compute_path((current_x, current_y), goal_pos)
            if not self.path:
                return None  # No path found
        
        if self.current_path_index >= len(self.path) - 1:
            return None  # End of path
        
        # Get next position from path
        next_x, next_y = self.path[self.current_path_index + 1]
        
        # Convert to direction
        dx = next_x - current_x
        dy = next_y - current_y
        
        self.current_path_index += 1
        return (dx, dy)
    
    def reset(self):
        """Reset the algorithm runner"""
        self.path = []
        self.current_path_index = 0 