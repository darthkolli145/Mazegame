import importlib.util
import sys
from collections import deque
import numpy as np

class AlgorithmRunner:
    def __init__(self, maze, maze_size):
        self.maze = maze
        self.maze_size = maze_size
        self.custom_algorithm = None
        self.path = []
        self.current_path_index = 0
        self.loaded_algorithm = False
        self.visited_cells = set()  # Track cells visited by player
        self.vision_range = 4  # Default vision range
    
    def update_vision(self, visited_cells, vision_range=4):
        """
        Update the vision information with player's current data
        
        Args:
            visited_cells: Set of (x,y) coordinates that player has visited
            vision_range: Current vision range of player
        """
        self.visited_cells = visited_cells.copy()
        self.vision_range = vision_range
    
    def is_cell_visible(self, x, y, player_x, player_y):
        """
        Check if a cell is visible to the player based on visited cells and vision range
        
        Args:
            x, y: Coordinates of the cell to check
            player_x, player_y: Current player position
        """
        # Cell is visible if it has been visited
        if (x, y) in self.visited_cells:
            return True
        
        # Cell is visible if it's within vision range
        dist_x = abs(x - player_x)
        dist_y = abs(y - player_y)
        # Use Manhattan distance for visibility check
        return (dist_x + dist_y) <= self.vision_range * 1.5
    
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
                # Create a fog of war version of the maze
                visible_maze = self._get_visible_maze(start_pos)
                
                self.path = self.custom_algorithm(visible_maze, start_pos, goal_pos)
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
    
    def _get_visible_maze(self, player_pos):
        """
        Create a copy of the maze with full visibility
        """
        # Simply return a copy of the actual maze - no fog of war
        maze_copy = np.copy(self.maze)
        
        # Print debug info about the maze
        player_x, player_y = player_pos
        print(f"\nAlgorithm is using maze with:")
        print(f"- Size: {self.maze_size[0]}x{self.maze_size[1]}")
        print(f"- Player position: ({player_x}, {player_y})")
        
        # Check for powerups in the maze
        powerup_counts = {}
        for y in range(self.maze_size[1]):
            for x in range(self.maze_size[0]):
                value = maze_copy[y][x]
                if value >= 4:  # Powerup
                    powerup_counts[value] = powerup_counts.get(value, 0) + 1
        
        if powerup_counts:
            print("- Powerups present in the maze:")
            for code, count in powerup_counts.items():
                powerup_name = {
                    4: "Speed", 5: "Teleport", 6: "Wall Break", 
                    7: "Score Multiplier", 8: "Time Freeze", 
                    9: "Ghost", 10: "Decay Freeze", 11: "Objective"
                }.get(code, f"Unknown ({code})")
                print(f"  - {powerup_name}: {count}")
        else:
            print("- No powerups present in the maze")
        
        return maze_copy
    
    def _default_algorithm(self, start_pos, goal_pos):
        """
        Default algorithm - Breadth-First Search
        Only considers cells that are visible to the player
        Returns a list of (x, y) coordinates forming a path from start to goal
        """
        start_x, start_y = start_pos
        goal_x, goal_y = goal_pos
        
        # Get the maze with fog of war applied
        visible_maze = self._get_visible_maze(start_pos)
        
        # Check if start or goal are walls in the visible maze
        if visible_maze[start_y][start_x] == 1 or self.maze[goal_y][goal_x] == 1:
            return []
        
        # If goal is not visible yet, find the closest visible cell to explore
        if not self.is_cell_visible(goal_x, goal_y, start_x, start_y):
            # Instead of direct path to invisible goal, move toward unexplored areas
            return self._explore_toward_goal(start_pos, goal_pos, visible_maze)
        
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
                
                # Check if valid move - Path (0) or Powerup (≥4)
                if (0 <= nx < self.maze_size[0] and 
                    0 <= ny < self.maze_size[1] and 
                    visible_maze[ny][nx] != 1 and  # Not a wall
                    (nx, ny) not in visited):
                    queue.append((nx, ny))
                    visited[(nx, ny)] = (x, y)
        
        # No path found
        return []
    
    def _explore_toward_goal(self, start_pos, goal_pos, visible_maze):
        """
        When the goal is not visible, this method finds an exploration path
        toward the general direction of the goal
        """
        start_x, start_y = start_pos
        goal_x, goal_y = goal_pos
        
        # Find the frontiers - cells at the edge of visibility
        frontiers = []
        
        for y in range(self.maze_size[1]):
            for x in range(self.maze_size[0]):
                # Skip walls and invisible areas
                if visible_maze[y][x] == 1:  # Wall
                    continue
                
                # Check if this cell is at the frontier
                is_frontier = False
                for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                    nx, ny = x + dx, y + dy
                    if (0 <= nx < self.maze_size[0] and 
                        0 <= ny < self.maze_size[1] and 
                        self.is_cell_visible(nx, ny, start_x, start_y) and 
                        visible_maze[ny][nx] != 1):  # Not a wall
                        is_frontier = True
                        break
                
                if is_frontier:
                    # Calculate heuristic: distance to goal
                    dist_to_goal = abs(x - goal_x) + abs(y - goal_y)
                    frontiers.append((x, y, dist_to_goal))
        
        if not frontiers:
            # No frontiers found, return a path that just sits still
            return [(start_x, start_y)]
        
        # Sort frontiers by distance to goal (heuristic)
        frontiers.sort(key=lambda f: f[2])
        
        # Try to find a path to the best frontier
        best_path = []
        
        for frontier_x, frontier_y, _ in frontiers[:3]:  # Try top 3 frontiers
            # BFS to find path to frontier
            queue = deque([(start_x, start_y)])
            visited = {(start_x, start_y): None}
            
            found = False
            while queue and not found:
                x, y = queue.popleft()
                
                if (x, y) == (frontier_x, frontier_y):
                    # Found path to frontier
                    path = []
                    current = (x, y)
                    while current != (start_x, start_y):
                        path.append(current)
                        current = visited[current]
                    path.append((start_x, start_y))
                    path.reverse()
                    
                    if len(path) > 1:  # Only return if we have a real path
                        best_path = path
                        found = True
                        break
                
                # Try each direction
                for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                    nx, ny = x + dx, y + dy
                    
                    # Check if valid move in visible maze - Path (0) or Powerup (≥4)
                    if (0 <= nx < self.maze_size[0] and 
                        0 <= ny < self.maze_size[1] and 
                        visible_maze[ny][nx] != 1 and  # Not a wall 
                        (nx, ny) not in visited and
                        self.is_cell_visible(nx, ny, start_x, start_y)):
                        queue.append((nx, ny))
                        visited[(nx, ny)] = (x, y)
            
            if best_path:
                # Found at least one good path, use it
                return best_path
        
        # No path found to any frontier, just return a single step in any valid direction
        for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
            nx, ny = start_x + dx, start_y + dy
            if (0 <= nx < self.maze_size[0] and 
                0 <= ny < self.maze_size[1] and 
                visible_maze[ny][nx] != 1):  # Not a wall
                return [(start_x, start_y), (nx, ny)]
        
        # No valid moves, return just the current position
        return [(start_x, start_y)]
    
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
            # End of path, recompute path with updated vision
            self.compute_path((current_x, current_y), goal_pos)
            self.current_path_index = 0
            if not self.path or len(self.path) <= 1:
                return None  # No path found
        
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