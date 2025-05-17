"""
Enhanced Maze-Solving Algorithm with Powerup Detection

This algorithm demonstrates how to access and utilize the numeric maze matrix:
- 0 = path
- 1 = wall
- 2 = start position
- 3 = goal position 
- 4-11 = powerups:
  - 4 = Speed: Increases movement speed
  - 5 = Teleport: Teleports player closer to goal
  - 6 = Wall_Break: Allows breaking through walls
  - 7 = Score_Multiplier: Multiplies score earned
  - 8 = Time_Freeze: Freezes timer temporarily
  - 9 = Ghost: Allows passing through walls
  - 10 = Decay_Freeze: Stops score decay
  - 11 = Objective: Bonus points

The algorithm receives the full numeric matrix and can detect powerups directly
from the matrix values.
"""

from collections import deque
import heapq
import math

def solve_maze(maze, start_pos, goal_pos):
    """
    Intelligent maze-solving algorithm that considers powerups.
    
    Args:
        maze: 2D numeric matrix where:
              0 = path, 1 = wall, 2 = start, 3 = goal
              4-11 = various powerups (e.g., 4 = Speed, 5 = Teleport, etc.)
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
    
    # Print debug information about powerups in the maze
    print("\nPowerups available in this maze:")
    powerups_found = find_all_powerups(maze, width, height)
    
    # Check if start position is valid
    if start_x < 0 or start_y < 0 or start_x >= width or start_y >= height or maze[start_y][start_x] == 1:
        return [start_pos]  # Stay in place if invalid
    
    # Check if goal is visible and reachable within the visible maze
    goal_visible = (0 <= goal_x < width and 0 <= goal_y < height and maze[goal_y][goal_x] != 1)
    
    if goal_visible and powerups_found:
        # Goal is visible and powerups exist - use modified A* that considers powerups
        return a_star_with_powerups(maze, start_pos, goal_pos, powerups_found)
    elif goal_visible:
        # Goal is visible but no powerups - use regular A* for optimal pathfinding
        return a_star_search(maze, start_pos, goal_pos)
    else:
        # Goal not visible - use intelligent exploration strategy that considers powerups
        return explore_maze(maze, start_pos, goal_pos, width, height)

def find_all_powerups(maze, width, height):
    """
    Scan the entire maze to find all powerups and return them as a list of (type, position) tuples.
    This demonstrates how to detect different powerup types from the numeric matrix.
    """
    powerups = []
    powerup_counts = {i: 0 for i in range(4, 12)}  # Initialize counters for powerup types 4-11
    
    for y in range(height):
        for x in range(width):
            cell_value = maze[y][x]
            if 4 <= cell_value <= 11:  # This is a powerup
                powerup_type = cell_value
                powerups.append((powerup_type, (x, y)))
                powerup_counts[powerup_type] += 1
    
    # Print powerup information
    powerup_names = {
        4: "Speed", 5: "Teleport", 6: "Wall_Break", 
        7: "Score_Multiplier", 8: "Time_Freeze", 
        9: "Ghost", 10: "Decay_Freeze", 11: "Objective"
    }
    
    for powerup_type, count in powerup_counts.items():
        if count > 0:
            print(f"- {powerup_names[powerup_type]} (value {powerup_type}): {count} found")
    
    return powerups

def a_star_with_powerups(maze, start_pos, goal_pos, powerups):
    """
    Modified A* algorithm that considers the value of powerups.
    Prioritizes valuable powerups that are on or near the optimal path.
    """
    start_x, start_y = start_pos
    goal_x, goal_y = goal_pos
    
    # Calculate value of each powerup based on type and location
    powerup_values = {}
    for powerup_type, pos in powerups:
        # Assign base value based on powerup type
        # KEY (4-11): The numeric values in the maze matrix
        # VALUE (5-15): The utility/importance score for the algorithm (not maze values)
        base_value = {
            4: 5,    # Speed (maze value: 4, utility score: 5)
            5: 8,    # Teleport (maze value: 5, utility score: 8)
            6: 10,   # Wall_Break (maze value: 6, utility score: 10)
            7: 10,   # Score_Multiplier (maze value: 7, utility score: 10)
            8: 7,    # Time_Freeze (maze value: 8, utility score: 7)
            9: 15,   # Ghost (maze value: 9, utility score: 15)
            10: 6,   # Decay_Freeze (maze value: 10, utility score: 6)
            11: 12   # Objective (maze value: 11, utility score: 12)
        }.get(powerup_type, 0)
        
        # Adjust value based on distance from path
        dist_to_start = manhattan_distance(start_pos, pos)
        dist_to_goal = manhattan_distance(pos, goal_pos)
        detour_cost = dist_to_start + dist_to_goal - manhattan_distance(start_pos, goal_pos)
        
        # Lower value if requires significant detour
        adjusted_value = base_value - (detour_cost * 0.5)
        if adjusted_value > 0:
            powerup_values[pos] = adjusted_value
    
    # Priority queue for A*: (priority, (x, y), path, collected_powerups)
    queue = [(manhattan_distance(start_pos, goal_pos), start_pos, [start_pos], [])]
    visited = {(start_pos, tuple())}  # Track visited states including collected powerups
    
    while queue:
        _, current, path, collected = heapq.heappop(queue)
        x, y = current
        
        # Found the goal
        if current == goal_pos:
            print(f"Path found collecting {len(collected)} powerups")
            return path
        
        # Check if current position has a powerup
        current_cell_value = maze[y][x]
        if 4 <= current_cell_value <= 11 and current not in collected:
            collected = collected + [current]
        
        # Check all four directions
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            next_pos = (nx, ny)
            
            # Check if valid move - this is how we access the maze matrix
            # Any value other than 1 (wall) is passable
            if is_valid_move(maze, next_pos):
                # Create new state with updated path and powerups
                new_path = path + [next_pos]
                new_collected = collected.copy()
                
                # Check if next position has a powerup
                if next_pos not in collected and next_pos in powerup_values:
                    new_collected.append(next_pos)
                
                state = (next_pos, tuple(new_collected))
                if state not in visited:
                    # Calculate priority based on path length and powerup value
                    path_length_cost = len(new_path)
                    goal_distance = manhattan_distance(next_pos, goal_pos)
                    
                    # Collect value from all powerups in new_collected
                    powerup_value = sum(powerup_values.get(pos, 0) for pos in new_collected)
                    
                    # Lower priority is better, so subtract powerup value
                    priority = path_length_cost + goal_distance - (powerup_value * 0.2)
                    
                    heapq.heappush(queue, (priority, next_pos, new_path, new_collected))
                    visited.add(state)
    
    # No path found
    return [start_pos]

def a_star_search(maze, start_pos, goal_pos):
    """
    Standard A* search algorithm for finding the optimal path when goal is visible.
    Uses Manhattan distance heuristic.
    
    Note how we check maze cells: maze[y][x] != 1 means the cell is not a wall
    and is passable (including paths and powerups).
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
    
    This function can be improved to prioritize frontiers near powerups.
    """
    # Find frontier cells (open cells adjacent to unexplored/wall cells)
    frontiers = find_frontiers(maze, width, height)
    
    # Find all powerups in the visible maze
    powerups = find_all_powerups(maze, width, height)
    powerup_positions = [pos for _, pos in powerups]
    
    if not frontiers:
        # No frontiers found - try to move in any valid direction
        return find_any_valid_move(maze, start_pos)
    
    # Score frontiers based on:
    # 1. Direction toward goal (higher priority)
    # 2. Distance from current position (lower priority)
    # 3. Proximity to powerups (bonus)
    scored_frontiers = []
    for f_pos in frontiers:
        # Direction score - how aligned is this with the direction to the goal?
        direction_score = direction_toward_goal(start_pos, f_pos, goal_pos)
        
        # Distance score - closer is better but less important than direction
        distance = manhattan_distance(start_pos, f_pos)
        distance_score = 1.0 / (distance + 1)  # Avoid division by zero
        
        # Powerup proximity score
        powerup_score = 0
        for p_pos in powerup_positions:
            proximity = 1.0 / (manhattan_distance(f_pos, p_pos) + 1)
            powerup_score += proximity
        
        # Combined score (weighted)
        score = (direction_score * 0.5) + (distance_score * 0.2) + (powerup_score * 0.3)
        
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
            # Skip walls - we can directly check the maze matrix value
            if maze[y][x] == 1:  # Wall
                continue
                
            # Check if this is a frontier cell (adjacent to a wall)
            is_frontier = False
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                # If adjacent cell is out of bounds or a wall, this might be a frontier
                if not (0 <= nx < width and 0 <= ny < height) or maze[ny][nx] == 1:
                    is_frontier = True
                    break
            
            if is_frontier:
                frontiers.append((x, y))
    
    return frontiers

def bfs_path(maze, start_pos, goal_pos):
    """
    Standard BFS to find a path between two points in the visible maze.
    Demonstrates how to check for valid moves using the maze matrix.
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
    Checks each adjacent cell in the maze matrix to find valid moves.
    """
    x, y = start_pos
    
    # Prioritize powerups if they're adjacent
    for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
        nx, ny = x + dx, y + dy
        if is_valid_move(maze, (nx, ny)):
            # Check if this cell contains a powerup (values 4-11)
            if 4 <= maze[ny][nx] <= 11:
                return [start_pos, (nx, ny)]
    
    # Try all four directions in a priority order
    for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
        nx, ny = x + dx, y + dy
        if is_valid_move(maze, (nx, ny)):
            return [start_pos, (nx, ny)]
    
    # No valid moves, stay in place
    return [start_pos]

def is_valid_move(maze, pos):
    """
    Check if a position is a valid move (in bounds and not a wall).
    
    This is the key function that accesses the maze matrix to determine
    if a cell is passable. All values except 1 (wall) are considered passable:
    - 0: Regular path
    - 2: Start position
    - 3: Goal position
    - 4-11: Various powerups
    """
    x, y = pos
    height = len(maze)
    width = len(maze[0]) if height > 0 else 0
    
    if not (0 <= x < width and 0 <= y < height):
        return False
    
    # Check maze value - only walls (value 1) are impassable
    return maze[y][x] != 1

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
Additional Maze Matrix Information:

The maze matrix now uses numeric values instead of booleans:
- 0 = path
- 1 = wall 
- 2 = start position
- 3 = goal position
- 4-11 = powerups:
  - 4 = Speed: Increases movement speed
  - 5 = Teleport: Teleports player closer to goal
  - 6 = Wall_Break: Allows breaking through walls
  - 7 = Score_Multiplier: Multiplies score earned
  - 8 = Time_Freeze: Freezes timer temporarily
  - 9 = Ghost: Allows passing through walls
  - 10 = Decay_Freeze: Stops score decay
  - 11 = Objective: Bonus points

When checking for valid moves, only cells with value 1 (walls) are impassable.
All other values (0, 2, 3, 4-11) are considered valid moves.

This algorithm demonstrates how to:
1. Access the numeric values in the maze matrix
2. Detect different types of powerups
3. Create strategies that consider powerup collection
4. Integrate powerup awareness into pathfinding decisions
""" 