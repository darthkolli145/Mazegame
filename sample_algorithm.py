"""
Sample Maze-Solving Algorithm

This is a template for creating your own maze-solving algorithm.
The function solve_maze must return a list of (x,y) coordinates.
"""

from collections import deque

def solve_maze(maze, start_pos, goal_pos):
    """
    Breadth-First Search algorithm to find the shortest path through a maze.
    
    Args:
        maze: 2D boolean array where True represents walls and False represents paths
        start_pos: Tuple (x, y) of starting position
        goal_pos: Tuple (x, y) of goal position
        
    Returns:
        List of coordinates [(x1,y1), (x2,y2), ...] from start to goal
    """
    start_x, start_y = start_pos
    goal_x, goal_y = goal_pos
    
    # Extract maze dimensions
    height = len(maze)
    width = len(maze[0]) if height > 0 else 0
    
    # Check if start or goal are walls
    if maze[start_y][start_x] or maze[goal_y][goal_x]:
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
            if (0 <= nx < width and 
                0 <= ny < height and 
                not maze[ny][nx] and 
                (nx, ny) not in visited):
                queue.append((nx, ny))
                visited[(nx, ny)] = (x, y)
    
    # No path found
    return []


"""
# Here's how you could implement other algorithms:

def solve_maze_depth_first(maze, start_pos, goal_pos):
    # DFS implementation
    # ...
    return path

def solve_maze_a_star(maze, start_pos, goal_pos):
    # A* implementation
    # ...
    return path

def solve_maze_wall_follower(maze, start_pos, goal_pos):
    # Wall follower implementation
    # ...
    return path

# You can try genetic algorithms, neural networks, etc.
""" 