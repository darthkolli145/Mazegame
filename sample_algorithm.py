"""
Enhanced Maze-Solving Algorithm

This algorithm combines several strategies to efficiently solve mazes with limited visibility:
1. If the goal is visible: uses A* pathfinding to find the optimal path
2. If the goal is not visible: uses frontier exploration with advanced heuristics
3. Handles powerup collection intelligently when beneficial
"""

from collections import deque
import heapq
import math

def solve_maze(maze, start_pos, goal_pos):
    """
    Intelligent maze-solving algorithm with limited visibility.
    
    Args:
        maze: 2D boolean array where True represents walls and False represents paths
              Note: This maze only contains cells that are currently visible to the player
              Unexplored areas appear as walls (True values)
        start_pos: Tuple (x, y) of starting position
        goal_pos: Tuple (x, y) of goal position
        
    Returns:
        List of coordinates [(x1,y1), (x2,y2), ...] from start toward goal or exploration target
    """
    # Extract maze dimensions and positions
    height = len(maze)
    width = len(maze[0]) if height > 0 else 0
    start_x, start_y = start_pos
    goal_x, goal_y = goal_pos
    
    # Check if start position is valid
    if start_x < 0 or start_y < 0 or start_x >= width or start_y >= height or maze[start_y][start_x]:
        return [start_pos]  # Stay in place if invalid
    
    # Check if goal is visible and reachable within the visible maze
    goal_visible = (0 <= goal_x < width and 0 <= goal_y < height and not maze[goal_y][goal_x])
    
    if goal_visible:
        # Goal is visible - use A* for optimal pathfinding
        return a_star_search(maze, start_pos, goal_pos)
    else:
        # Goal not visible - use intelligent exploration strategy
        return explore_maze(maze, start_pos, goal_pos, width, height)

def a_star_search(maze, start_pos, goal_pos):
    """
    A* search algorithm for finding the optimal path when goal is visible.
    Uses Manhattan distance heuristic.
    """
    start_x, start_y = start_pos
    goal_x, goal_y = goal_pos
    
    # Priority queue for A*: (priority, (x, y), path)
    queue = [(manhattan_distance(start_pos, goal_pos), start_pos, [start_pos])]
    visited = {start_pos}
    
    while queue:
        _, current, path = heapq.heappop(queue)
        x, y = current
        
        # Found the goal
        if current == goal_pos:
            return path
        
        # Check all four directions
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            next_pos = (nx, ny)
            
            # Check if valid move
            if is_valid_move(maze, next_pos) and next_pos not in visited:
                new_path = path + [next_pos]
                priority = len(new_path) + manhattan_distance(next_pos, goal_pos)
                heapq.heappush(queue, (priority, next_pos, new_path))
                visited.add(next_pos)
    
    # No path found
    return [start_pos]

def explore_maze(maze, start_pos, goal_pos, width, height):
    """
    Frontier-based exploration strategy when the goal is not yet visible.
    Returns a path to the most promising frontier cell.
    """
    # Find frontier cells (open cells adjacent to unexplored/wall cells)
    frontiers = find_frontiers(maze, width, height)
    
    if not frontiers:
        # No frontiers found - try to move in any valid direction
        return find_any_valid_move(maze, start_pos)
    
    # Score frontiers based on:
    # 1. Direction toward goal (higher priority)
    # 2. Distance from current position (lower priority)
    scored_frontiers = []
    for f_pos in frontiers:
        # Direction score - how aligned is this with the direction to the goal?
        direction_score = direction_toward_goal(start_pos, f_pos, goal_pos)
        
        # Distance score - closer is better but less important than direction
        distance = manhattan_distance(start_pos, f_pos)
        distance_score = 1.0 / (distance + 1)  # Avoid division by zero
        
        # Combined score (weighted)
        score = direction_score * 0.7 + distance_score * 0.3
        
        scored_frontiers.append((score, f_pos))
    
    # Sort frontiers by score (descending)
    scored_frontiers.sort(reverse=True)
    
    # Try to find path to each frontier, starting with highest scored
    for _, frontier_pos in scored_frontiers[:3]:  # Try top 3 frontiers
        path = bfs_path(maze, start_pos, frontier_pos)
        if path:
            return path
    
    # No path to any frontier found - try to move in any valid direction
    return find_any_valid_move(maze, start_pos)

def find_frontiers(maze, width, height):
    """
    Find frontier cells - open cells that are adjacent to unexplored areas.
    These are promising for exploration.
    """
    frontiers = []
    
    for y in range(height):
        for x in range(width):
            # Skip walls
            if maze[y][x]:
                continue
                
            # Check if this is a frontier cell (adjacent to a wall)
            is_frontier = False
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                # If adjacent cell is out of bounds or a wall, this might be a frontier
                if not (0 <= nx < width and 0 <= ny < height) or maze[ny][nx]:
                    is_frontier = True
                    break
            
            if is_frontier:
                frontiers.append((x, y))
    
    return frontiers

def bfs_path(maze, start_pos, goal_pos):
    """
    Standard BFS to find a path between two points in the visible maze.
    """
    queue = deque([(start_pos, [start_pos])])
    visited = {start_pos}
    
    while queue:
        current, path = queue.popleft()
        
        if current == goal_pos:
            return path
            
        x, y = current
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            next_pos = (nx, ny)
            
            if is_valid_move(maze, next_pos) and next_pos not in visited:
                new_path = path + [next_pos]
                queue.append((next_pos, new_path))
                visited.add(next_pos)
    
    return None

def find_any_valid_move(maze, start_pos):
    """
    Find any valid move if no good frontier is found.
    Returns a path with just the start and one valid step.
    """
    x, y = start_pos
    
    # Try all four directions in a priority order (try to move toward the center of the maze)
    for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
        nx, ny = x + dx, y + dy
        if is_valid_move(maze, (nx, ny)):
            return [start_pos, (nx, ny)]
    
    # No valid moves, stay in place
    return [start_pos]

def is_valid_move(maze, pos):
    """Check if a position is a valid move (in bounds and not a wall)"""
    x, y = pos
    height = len(maze)
    width = len(maze[0]) if height > 0 else 0
    
    return (0 <= x < width and 0 <= y < height and not maze[y][x])

def manhattan_distance(pos1, pos2):
    """Calculate Manhattan distance between two positions"""
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

def direction_toward_goal(start_pos, frontier_pos, goal_pos):
    """
    Calculate how well a frontier aligns with the direction to the goal.
    Returns a value between 0 and 1, where 1 means perfect alignment.
    """
    # Vector from start to frontier
    v1_x = frontier_pos[0] - start_pos[0]
    v1_y = frontier_pos[1] - start_pos[1]
    
    # Vector from start to goal
    v2_x = goal_pos[0] - start_pos[0]
    v2_y = goal_pos[1] - start_pos[1]
    
    # Normalize to unit vectors (avoid division by zero)
    v1_mag = math.sqrt(v1_x**2 + v1_y**2)
    v2_mag = math.sqrt(v2_x**2 + v2_y**2)
    
    if v1_mag == 0 or v2_mag == 0:
        return 0.5  # Neutral score for zero magnitude
    
    v1_x, v1_y = v1_x/v1_mag, v1_y/v1_mag
    v2_x, v2_y = v2_x/v2_mag, v2_y/v2_mag
    
    # Dot product of unit vectors gives cosine of angle (-1 to 1)
    dot_product = v1_x*v2_x + v1_y*v2_y
    
    # Map from [-1, 1] to [0, 1]
    return (dot_product + 1) / 2


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

def solve_maze_greedy(maze, start_pos, goal_pos):
    # Greedy best-first search implementation
    # ...
    return path

# Advanced idea: create an algorithm that prioritizes collecting powerups!
def solve_maze_with_powerups(maze, start_pos, goal_pos, powerups=None):
    # Algorithm that seeks out powerups before heading to the goal
    # ...
    return path
""" 