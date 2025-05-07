# Maze Game

A Python maze game with powerups, portals, and support for custom maze-solving algorithms.

## Features

- Randomly generated mazes
- Powerups (speed, reveal, teleport)
- Teleportation portals
- Custom algorithm support
- Scoring system
- High score tracking
- Multiple difficulty levels

## Installation

1. Clone this repository
2. Install the required packages:
```
pip install -r requirements.txt
```

## Controls

- **Arrow Keys**: Move player
- **A**: Run algorithm mode (default uses BFS)
- **R**: Reset/restart game
- **1/2/3**: Change difficulty (Easy/Medium/Hard)
- **ESC**: Quit game

## Difficulty Levels

- **Easy (1)**: Smaller maze (10x10), fewer powerups and portals, more forgiving scoring.
- **Medium (2)**: Medium maze (15x15), balanced powerups and portals.
- **Hard (3)**: Larger maze (20x20), more powerups and portals, stricter scoring but higher score multiplier.

## Powerups

- **Red**: Speed boost (bonus points)
- **Blue**: Reveal (shows path to exit)
- **Orange**: Teleport (moves you closer to the goal)

## Creating Your Own Algorithm

You can create your own maze-solving algorithm to compete for the highest score.

1. Create a Python file with a function called `solve_maze` that takes:
   - `maze`: 2D boolean array where `True` represents walls and `False` represents paths
   - `start_pos`: Tuple of (x, y) for starting position
   - `goal_pos`: Tuple of (x, y) for goal position

2. Return a list of (x, y) coordinates from start to goal
   
### Example Algorithm:

```python
def solve_maze(maze, start_pos, goal_pos):
    # Your algorithm here...
    # Example: return a simple path [(0,0), (1,0), (1,1), ...]
    
    # Use the maze grid where True is a wall, False is a path
    
    path = []
    # ... your pathfinding code ...
    
    return path
```

3. To use your custom algorithm, save it as `sample_algorithm.py` (it will be loaded automatically) or modify the `maze_game.py` file:

```python
# In the MazeGame class, inside start_algorithm_mode method:
self.algorithm_runner = AlgorithmRunner(self.maze, self.maze_size)
self.algorithm_runner.load_algorithm_from_file("your_algorithm_file.py")
```

### Algorithm Competition

Create the most efficient maze-solving algorithm to get the highest score! Compare your algorithm against others by:

1. Testing on different difficulty levels
2. Optimizing for shortest path
3. Adding logic to collect powerups strategically 
4. Creating logic to use portals effectively

## Scoring

Scores are calculated based on:
- Time to complete the maze (faster = higher score)
- Number of moves (fewer = higher score)
- Powerups collected (more = higher score)
- Difficulty level (higher difficulty = score multiplier)

## Customization

You can customize game behavior by modifying the `settings.py` file, including:
- Window size
- Maze dimensions
- Difficulty parameters
- Colors and appearance
- Powerup/portal quantities

## Running the Game

```
python maze_game.py
```
