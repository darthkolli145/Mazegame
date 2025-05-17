import pygame
import sys
import random
import numpy as np
from maze_generator import MazeGenerator
from player import Player
from powerup import PowerUp
from portal import Portal
from algorithm_runner import AlgorithmRunner
from scoreboard import Scoreboard
from settings import *
from collections import deque

class MazeGame:
    def __init__(self, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, difficulty="medium"):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption(GAME_TITLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 18)
        
        # Set difficulty
        self.difficulty = difficulty
        self.maze_size = DIFFICULTIES[difficulty]["maze_size"]
        self.time_factor = DIFFICULTIES[difficulty]["time_factor"]
        self.move_penalty = DIFFICULTIES[difficulty]["move_penalty"]
        
        # Reset random seeds
        self.reset_seeds()
        
        # Movement cooldown settings
        self.move_cooldown = 0.5  # 0.5 second cooldown between moves
        self.last_move_time = 0
        self.can_move = True
        
        # Score decay settings
        self.score_decay_active = True
        self.score_decay_rate = self._get_decay_rate()
        self.decay_timer = 0
        self.last_decay_time = 0
        
        # Sequential maze settings
        self.current_level = 1
        self.max_levels = 3  # Three sequential mazes
        self.total_score = 0  # Track score across levels
        self.level_results = []  # Store results of each level
        
        # Game objects
        self.cell_size = CELL_SIZE
        
        # Initialize the maze and find the start/goal positions
        self.maze = self._get_maze_for_level(self.current_level)
        
        # Player starts at top-left by default, but _get_maze_for_level updates this
        # based on the maze pattern's start position (value 3)
        if not hasattr(self, 'player'):
            self.player = Player(0, 0, self.cell_size)
        
        # Goal is at bottom-right by default, but _get_maze_for_level updates this
        # based on the maze pattern's goal position (value 2)
        if not hasattr(self, 'goal_pos'):
            self.goal_pos = (self.maze_size[0] - 1, self.maze_size[1] - 1)
        
        # Track cells that have been visited
        self.visited_cells = set()
        self.visited_cells.add((self.player.x, self.player.y))  # Start cell is already visited
        
        # Powerups and portals
        self.powerups = []
        self.portals = []  # We'll keep this empty list but not use it
        self._generate_powerups(POWERUP_COUNTS[difficulty])
        
        # Debug: Print maze with powerups
        print("\nInitial maze state with powerups:")
        self.print_numeric_maze()
        
        # Scoreboard
        self.scoreboard = Scoreboard()
        
        # Algorithm runner
        self.algorithm_runner = None
        self.algorithm_mode = False
        self.algorithm_speed = ALGORITHM_SPEED
        self.algorithm_timer = 0
        
        # Game state
        self.game_active = True
        self.moves = 0
        self.time_started = pygame.time.get_ticks()
        self.score = 1000  # Start with 1000 points
        self.objectives_collected = 0
        self.total_objectives = 0
    
    def _get_decay_rate(self):
        """Get the score decay rate based on difficulty"""
        rates = {
            "easy": 2,      # 2 points per second
            "medium": 5,    # 5 points per second
            "hard": 10      # 10 points per second
        }
        return rates.get(self.difficulty, 5)
    
    def _generate_powerups(self, count):
        # Reset the count of objectives
        self.total_objectives = 0
        
        # Mapping of powerup types to integer codes in the maze
        powerup_codes = {
            "speed": 4,
            "teleport": 5,
            "wall_break": 6,
            "score_multiplier": 7,
            "time_freeze": 8,
            "ghost": 9,
            "decay_freeze": 10,
            "objective": 11
        }
        
        # Create a mapping of codes to powerup types for later reference
        self.powerup_code_to_type = {v: k for k, v in powerup_codes.items()}
        
        # Use a fixed seed based on difficulty and level for consistent powerup placement
        random.seed(hash(self.difficulty) + self.current_level * 100)
        
        # Keep track of powerups to show on the map until collected
        self.powerups = []
        
        for _ in range(count):
            # Don't place powerups at start, end, or walls
            while True:
                x = random.randint(0, self.maze_size[0] - 1)
                y = random.randint(0, self.maze_size[1] - 1)
                if (x, y) != (self.player.x, self.player.y) and (x, y) != self.goal_pos and self.maze[y][x] == 0:
                    break
            
            # Random powerup type with weighted probabilities
            powerup_types = [
                "speed", "teleport", "wall_break", 
                "score_multiplier", "time_freeze", "ghost", 
                "decay_freeze"  # Powerup to stop score decay
            ]
            
            # Weight more powerful abilities to be less common
            weights = [0.25, 0.20, 0.15, 0.15, 0.05, 0.1, 0.1]  # Weights adjusted after removing vision powerups
            
            # Make certain powerups only available in higher difficulties
            if self.difficulty == "easy":
                weights[2:] = [0.05, 0.05, 0, 0, 0]  # Reduce wall_break and score_multiplier, remove others
            elif self.difficulty == "medium":
                weights[4:] = [0.05, 0, 0.05]  # Reduce time_freeze, remove some, keep decay_freeze
            
            # Normalize weights
            total = sum(weights)
            weights = [w/total for w in weights]
            
            powerup_type = random.choices(powerup_types, weights=weights, k=1)[0]
            
            # Place the powerup in the maze
            powerup_code = powerup_codes[powerup_type]
            self.maze[y][x] = powerup_code
            
            # Also add to powerups list for rendering and tracking
            self.powerups.append(PowerUp(x, y, powerup_type, self.cell_size))
            
            # Increment total objectives
            self.total_objectives += 1
            
        # Also consider adding special objective powerups just for collection
        # Reduced counts based on difficulty:
        # Easy: 0-1, Medium: 1-2, Hard: 1-3
        if self.difficulty == "easy":
            num_objectives = random.randint(0, 1)
        elif self.difficulty == "medium":
            num_objectives = random.randint(1, 2)
        else:  # hard
            num_objectives = random.randint(1, 3)
            
        for _ in range(num_objectives):
            # Try to find a valid spot, but limit attempts to avoid infinite loops
            max_attempts = 50
            attempts = 0
            while attempts < max_attempts:
                x = random.randint(0, self.maze_size[0] - 1)
                y = random.randint(0, self.maze_size[1] - 1)
                if (x, y) != (self.player.x, self.player.y) and (x, y) != self.goal_pos and self.maze[y][x] == 0:
                    valid_spot = True
                    # Check we're not placing on another powerup
                    for p in self.powerups:
                        if p.x == x and p.y == y:
                            valid_spot = False
                            break
                    if valid_spot:
                        # Place the objective powerup in the maze
                        self.maze[y][x] = powerup_codes["objective"]
                        
                        # Create a special "objective" powerup that's just for collection points
                        self.powerups.append(PowerUp(x, y, "objective", self.cell_size))
                        self.total_objectives += 1
                        break
                attempts += 1
    
    def print_numeric_maze(self):
        """Print the current numeric maze values to the console"""
        print("\nMaze Matrix with Numeric Values:")
        print("Legend: 0=Path, 1=Wall, 2=Start, 3=Goal")
        print("4=Speed, 5=Teleport, 6=Wall_Break, 7=Score_Multiplier")
        print("8=Time_Freeze, 9=Ghost, 10=Decay_Freeze, 11=Objective\n")
        
        for y in range(self.maze_size[1]):
            row = []
            for x in range(self.maze_size[0]):
                val = str(self.maze[y][x]).rjust(2)
                row.append(val)
            print(" ".join(row))
        print("\n")

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            elif event.type == pygame.VIDEORESIZE:
                # Update window size
                self.width, self.height = event.size
                self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                # Recalculate UI elements if needed
                self.show_popup("Window Resized", duration=1.0)
            
            elif event.type == pygame.KEYDOWN:
                # Check if movement is allowed based on cooldown
                current_time = pygame.time.get_ticks() / 1000.0  # Current time in seconds
                time_since_last_move = current_time - self.last_move_time
                
                # Apply speed boost to cooldown if active
                effective_cooldown = self.move_cooldown / self.player.get_speed_multiplier()
                
                if not self.algorithm_mode and self.game_active and time_since_last_move >= effective_cooldown:
                    # Player movement
                    if event.key == pygame.K_UP:
                        self.move_player(0, -1)
                        self.last_move_time = current_time
                    elif event.key == pygame.K_DOWN:
                        self.move_player(0, 1)
                        self.last_move_time = current_time
                    elif event.key == pygame.K_LEFT:
                        self.move_player(-1, 0)
                        self.last_move_time = current_time
                    elif event.key == pygame.K_RIGHT:
                        self.move_player(1, 0)
                        self.last_move_time = current_time
                elif not self.algorithm_mode and self.game_active and time_since_last_move < effective_cooldown:
                    # Show cooldown message if trying to move too quickly
                    if event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
                        time_left = effective_cooldown - time_since_last_move
                        self.show_popup(f"Move Cooldown: {time_left:.1f}s", duration=0.3)
                
                # Start algorithm mode
                if event.key == pygame.K_a:
                    self.start_algorithm_mode()
                
                # Reset game
                if event.key == pygame.K_r:
                    self.reset_game()
                
                # Change difficulty
                if event.key == pygame.K_1:
                    self.change_difficulty("easy")
                elif event.key == pygame.K_2:
                    self.change_difficulty("medium")
                elif event.key == pygame.K_3:
                    self.change_difficulty("hard")
                
                # Print maze matrix (debug)
                elif event.key == pygame.K_p:
                    self.print_numeric_maze()
                
                # Quit
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
    
    def move_player(self, dx, dy):
        new_x = self.player.x + dx
        new_y = self.player.y + dy
        
        # Check if move is valid
        is_within_bounds = (0 <= new_x < self.maze_size[0] and 0 <= new_y < self.maze_size[1])
        
        if is_within_bounds:
            cell_value = self.maze[new_y][new_x]
            is_wall = (cell_value == 1)  # Wall is represented by 1
            
            # Check if player can move through wall
            can_pass = False
            
            # Ghost mode allows passing through walls
            if self.player.can_pass_through_walls() and is_wall:
                can_pass = True
                self.show_popup("Passed through wall!")
            
            # Wall break ability allows breaking walls
            elif self.player.can_break_wall() and is_wall:
                if self.player.break_wall():
                    # Break the wall permanently
                    self.maze[new_y][new_x] = 0  # Change from wall (1) to path (0)
                    can_pass = True
                    self.show_popup("Wall broken!")
            
            # Make the move if path is clear or player can pass through
            if (not is_wall) or can_pass:
                # Check for powerups before moving
                if cell_value >= 4:  # Cell contains a powerup
                    # Identify powerup type from cell value
                    powerup_type = self.powerup_code_to_type.get(cell_value)
                    if powerup_type:
                        # Find the matching powerup object
                        collected_powerup = None
                        for powerup in self.powerups[:]:
                            if powerup.x == new_x and powerup.y == new_y:
                                collected_powerup = powerup
                                break
                        
                        if collected_powerup:
                            # Apply the powerup effect
                            self.apply_powerup(collected_powerup)
                            # Remove from tracking list
                            self.powerups.remove(collected_powerup)
                            # Clear the cell in the maze
                            self.maze[new_y][new_x] = 0  # Reset to regular path
                
                # Now move the player
                self.player.move(new_x, new_y)
                self.moves += 1
                
                # Mark this cell as visited
                self.visited_cells.add((new_x, new_y))
                
                # Also mark neighboring cells as visible
                for nx, ny in [(new_x+1, new_y), (new_x-1, new_y), (new_x, new_y+1), (new_x, new_y-1)]:
                    if 0 <= nx < self.maze_size[0] and 0 <= ny < self.maze_size[1]:
                        self.visited_cells.add((nx, ny))
                
                # Check for goal
                if (new_x, new_y) == self.goal_pos or (self.player.x, self.player.y) == self.goal_pos:
                    self.complete_level()
    
    def apply_powerup(self, powerup):
        # Apply powerup effect based on type
        powerup_type = powerup.type
        duration = powerup.duration
        strength = powerup.strength
        
        # Increment objectives collected counter
        self.objectives_collected += 1
        
        # Apply to player object
        self.player.apply_powerup(powerup_type, duration, strength)
        
        # Process type-specific effects
        if powerup_type == "objective":
            # Pure objective powerup - gives bonus points based on current score
            bonus = 300
            self.score += bonus
            self.show_popup(f"+{bonus} Objective Collected!")
            
        elif powerup_type == "speed":
            # Speed boost gives bonus points
            bonus = 100 * strength
            self.score += bonus
            self.show_popup(f"+{bonus} Speed Boost!")
            
        elif powerup_type == "teleport":
            # Teleport closer to the goal
            goal_x, goal_y = self.goal_pos
            current_x, current_y = self.player.x, self.player.y
            
            # Try to find cells closer to goal using BFS
            queue = deque([(current_x, current_y)])
            visited = {(current_x, current_y)}
            parent = {(current_x, current_y): None}
            target = None
            max_distance = min(strength, self.maze_size[0] + self.maze_size[1])
            
            # Directions: right, down, left, up
            directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
            
            # Find a valid cell to teleport to
            distance = 0
            while queue and distance < max_distance:
                size = len(queue)
                for _ in range(size):
                    x, y = queue.popleft()
                    
                    # Check if this is a valid target (closer to goal than current position)
                    curr_dist = abs(current_x - goal_x) + abs(current_y - goal_y)
                    new_dist = abs(x - goal_x) + abs(y - goal_y)
                    
                    if new_dist < curr_dist and not self.maze[y][x]:
                        target = (x, y)
                        self.player.move(x, y)
                        self.show_popup("Teleported!")
                        self.score += 150
                        return
                    
                    # Try each direction
                    for dx, dy in directions:
                        nx, ny = x + dx, y + dy
                        
                        # Check if valid move
                        if (0 <= nx < self.maze_size[0] and 
                            0 <= ny < self.maze_size[1] and 
                            not self.maze[ny][nx] and 
                            (nx, ny) not in visited):
                            queue.append((nx, ny))
                            visited.add((nx, ny))
                            parent[(nx, ny)] = (x, y)
                
                distance += 1
            
            # If no better position found, just give bonus points
            self.score += 150
            self.show_popup("+150 Teleport Failed!")
            
        elif powerup_type == "wall_break":
            # Wall breaker allows player to break walls temporarily
            self.score += 250
            self.show_popup(f"Wall Breaker! ({strength} uses)")
            
        elif powerup_type == "score_multiplier":
            # Score multiplier increases all points
            self.score += 300
            self.show_popup(f"Score x{strength} for {duration}s!")
            
        elif powerup_type == "time_freeze":
            # Time freeze stops the timer
            self.score += 200
            self.show_popup(f"Time Frozen for {duration}s!")
            # When time is frozen, save the current decay time
            self.last_decay_time = pygame.time.get_ticks()
            
        elif powerup_type == "ghost":
            # Ghost mode lets player pass through walls
            self.score += 350
            self.show_popup(f"Ghost Mode for {duration}s!")
            
        elif powerup_type == "decay_freeze":
            # Stop score decay temporarily
            self.score += 250
            self.show_popup(f"Decay Shield for {duration}s!")
    
    def start_algorithm_mode(self):
        # Store current level before resetting
        current_level = self.current_level
        current_total_score = self.total_score
        
        # Reset the current level only, not the entire game
        self.reset_level()
        
        # Restore the level and total score
        self.current_level = current_level
        self.total_score = current_total_score
        
        # Enable algorithm mode (explicitly set this after reset_level which turns it off)
        self.algorithm_mode = True
        self.algorithm_runner = AlgorithmRunner(self.maze, self.maze_size)
        # Pass the visited cells and vision range to the algorithm
        vision_range = self.player.get_vision_range()
        self.algorithm_runner.update_vision(self.visited_cells, vision_range)
        
        # Try to load user's algorithm if specified
        try:
            self.algorithm_runner.load_algorithm_from_file("sample_algorithm.py")
        except Exception as e:
            print(f"Error loading algorithm: {e}")
            # If loading fails, just use the default algorithm
            pass
    
    def run_algorithm_step(self):
        if self.algorithm_runner and self.game_active:
            # Control algorithm speed and respect cooldown
            current_time = pygame.time.get_ticks() / 1000.0  # Current time in seconds
            time_since_last_move = current_time - self.last_move_time
            
            # Apply speed boost to cooldown if active
            effective_cooldown = self.move_cooldown / self.player.get_speed_multiplier()
            
            # Update algorithm's knowledge of visible cells
            vision_range = self.player.get_vision_range()
            self.algorithm_runner.update_vision(self.visited_cells, vision_range)
            
            # Only make a move if the cooldown has elapsed
            if time_since_last_move >= effective_cooldown:
                self.algorithm_timer += 1
                if self.algorithm_timer >= FPS / self.algorithm_speed:
                    self.algorithm_timer = 0
                    next_move = self.algorithm_runner.get_next_move(self.player.x, self.player.y, self.goal_pos)
                    if next_move:
                        dx, dy = next_move
                        self.move_player(dx, dy)
                        # Update last move time
                        self.last_move_time = current_time
                    else:
                        # Algorithm failed to find path
                        self.algorithm_mode = False
    
    def complete_level(self):
        elapsed_time = (pygame.time.get_ticks() - self.time_started) / 1000
        
        # Calculate score based on time, moves, and powerups
        time_score = max(1000 - int(elapsed_time * self.time_factor), 0)
        move_score = max(1000 - self.moves * self.move_penalty, 0)
        
        # Calculate objective score
        if self.total_objectives > 0:
            objective_percentage = self.objectives_collected / self.total_objectives
            objective_score = int(1500 * objective_percentage)  # Max 1500 points for all objectives
            objective_bonus = int(500 * (objective_percentage ** 2))  # Bonus for getting majority
        else:
            objective_score = 0
            objective_bonus = 0
        
        # Display score breakdown
        self.show_popup(f"Level {self.current_level} Complete!", duration=3.0)
        self.show_popup(f"Time Score: {time_score}", duration=3.0)
        self.show_popup(f"Move Score: {move_score}", duration=3.0)
        self.show_popup(f"Objective Score: {objective_score + objective_bonus}", duration=3.0)
        
        # Calculate final score with existing score (from powerups)
        final_score = self.score + time_score + move_score + objective_score + objective_bonus
        
        # Score multiplier based on difficulty
        if self.difficulty == "easy":
            final_score = int(final_score * 0.8)
        elif self.difficulty == "medium":
            final_score = int(final_score * 1.0)
        elif self.difficulty == "hard":
            final_score = int(final_score * 1.5)
        
        # Objective completion bonus (significantly higher bonus for getting all objectives)
        if self.objectives_collected == self.total_objectives and self.total_objectives > 0:
            completion_bonus = int(final_score * 0.25)  # 25% bonus for full completion
            final_score += completion_bonus
            self.show_popup(f"ALL OBJECTIVES! +{completion_bonus} BONUS!", duration=3.0)
        
        # Update score for this level
        self.score = final_score
        self.show_popup(f"Level Score: {final_score}", duration=3.0)
        
        # Temporarily pause gameplay during level transition
        self.game_active = False  
        
        # Use a shorter delay to improve responsiveness
        pygame.time.delay(2000)  # Reduced from 3000ms to 2000ms
        
        # Progress to next level or end game
        self.next_level()
    
    def change_difficulty(self, difficulty):
        if difficulty in DIFFICULTIES:
            self.difficulty = difficulty
            self.reset_game()
    
    def reset_game(self):
        # Update settings for current difficulty
        self.maze_size = DIFFICULTIES[self.difficulty]["maze_size"]
        self.time_factor = DIFFICULTIES[self.difficulty]["time_factor"]
        self.move_penalty = DIFFICULTIES[self.difficulty]["move_penalty"]
        
        # Reset random seeds
        self.reset_seeds()
        
        # Reset level tracking
        self.current_level = 1
        self.total_score = 0
        self.level_results = []
        
        # Reset the current level using the shared method
        self.reset_level()
        
        # Show starting message
        self.show_popup(f"Level 1 Starting!", duration=2.0)
    
    def draw(self):
        self.screen.fill(WHITE)
        
        # Draw maze
        offset_x = (self.width - self.maze_size[0] * self.cell_size) // 2
        offset_y = (self.height - self.maze_size[1] * self.cell_size) // 2
        
        # Draw the maze - now using integer values instead of booleans
        for y in range(self.maze_size[1]):
            for x in range(self.maze_size[0]):
                rect = pygame.Rect(
                    offset_x + x * self.cell_size,
                    offset_y + y * self.cell_size,
                    self.cell_size,
                    self.cell_size
                )
                
                cell_value = self.maze[y][x]
                
                # Draw based on cell value
                if cell_value == 1:  # Wall
                    pygame.draw.rect(self.screen, BLACK, rect)
                elif cell_value == 0:  # Path
                    pygame.draw.rect(self.screen, WHITE, rect, 1)
                elif cell_value >= 4:  # Powerup
                    pygame.draw.rect(self.screen, WHITE, rect, 1)  # Draw path background
                    
                    # Find matching powerup to get color
                    powerup_type = self.powerup_code_to_type.get(cell_value)
                    if powerup_type:
                        # Create small rect for powerup
                        powerup_rect = pygame.Rect(
                            offset_x + x * self.cell_size + self.cell_size // 4,
                            offset_y + y * self.cell_size + self.cell_size // 4,
                            self.cell_size // 2,
                            self.cell_size // 2
                        )
                        
                        # Get powerup color
                        temp_powerup = PowerUp(0, 0, powerup_type, self.cell_size)
                        pygame.draw.rect(self.screen, temp_powerup.get_color(), powerup_rect)
        
        # Draw goal
        goal_rect = pygame.Rect(
            offset_x + self.goal_pos[0] * self.cell_size,
            offset_y + self.goal_pos[1] * self.cell_size,
            self.cell_size,
            self.cell_size
        )
        pygame.draw.rect(self.screen, GREEN, goal_rect)
        
        # Draw player with special effects
        player_rect = pygame.Rect(
            offset_x + self.player.x * self.cell_size + self.cell_size // 4,
            offset_y + self.player.y * self.cell_size + self.cell_size // 4,
            self.cell_size // 2,
            self.cell_size // 2
        )
        
        # Change player color based on active powerups
        player_color = RED
        if self.player.ghost_mode_active:
            player_color = (220, 220, 220)  # Light gray for ghost mode
        elif self.player.wall_break_active:
            player_color = (139, 69, 19)  # Brown for wall break
        elif self.player.has_speed_boost:
            player_color = (255, 0, 0)  # Bright red for speed
        
        pygame.draw.rect(self.screen, player_color, player_rect)
        
        # Draw player effect circle for active powerups
        if self.player.has_speed_boost or self.player.ghost_mode_active or self.player.wall_break_active:
            # Pulsating effect
            pulse = (pygame.time.get_ticks() % 1000) / 1000  # 0 to 1 over time
            pulse_size = self.cell_size // 2 + int(self.cell_size // 4 * pulse)
            
            pulse_rect = pygame.Rect(
                offset_x + self.player.x * self.cell_size + (self.cell_size - pulse_size) // 2,
                offset_y + self.player.y * self.cell_size + (self.cell_size - pulse_size) // 2,
                pulse_size,
                pulse_size
            )
            
            s = pygame.Surface((pulse_size, pulse_size), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (*player_color, 128 - 128 * pulse), (0, 0, pulse_size, pulse_size))
            self.screen.blit(s, (pulse_rect.x, pulse_rect.y))
        
        # Draw UI information
        current_time = pygame.time.get_ticks()
        if self.player.time_freeze_active:
            elapsed_time = self.stored_time if hasattr(self, 'stored_time') else 0
        else:
            elapsed_time = (current_time - self.time_started) / 1000
            # Store current time for time freeze
            self.stored_time = elapsed_time
            
        # Show movement cooldown status
        current_time_sec = current_time / 1000.0
        time_since_last_move = current_time_sec - self.last_move_time
        effective_cooldown = self.move_cooldown / self.player.get_speed_multiplier()
        cooldown_remaining = max(0, effective_cooldown - time_since_last_move)
        
        time_text = self.font.render(f"Time: {elapsed_time:.1f}s", True, BLACK)
        moves_text = self.font.render(f"Moves: {self.moves}", True, BLACK)
        
        # Add cooldown indicator
        if cooldown_remaining > 0:
            cooldown_percent = cooldown_remaining / effective_cooldown
            move_text = self.font.render(f"Move: Cooldown {cooldown_remaining:.1f}s", True, (200, 0, 0))
        else:
            move_text = self.font.render("Move: Ready", True, (0, 150, 0))
            
        # Apply score multiplier if active
        display_score = int(self.score * self.player.get_score_multiplier())
        score_text = self.font.render(f"Score: {display_score}", True, BLACK)
        
        # Show level info and total score
        level_text = self.font.render(f"Level: {self.current_level}/{self.max_levels}", True, BLACK)
        total_score_text = self.font.render(f"Total Score: {self.total_score}", True, BLACK)
        
        # Show score decay rate
        if self.score_decay_active and not self.player.time_freeze_active and not self.player.decay_freeze_active:
            decay_text = self.font.render(f"Decay: -{self.score_decay_rate}/sec", True, (200, 0, 0))  # Red color for decay
        else:
            decay_text = self.font.render("Decay: Paused", True, (0, 150, 0))  # Green for paused
        
        mode_text = self.font.render(
            f"Mode: {'Algorithm' if self.algorithm_mode else 'Player'}", 
            True, 
            BLACK
        )
        difficulty_text = self.font.render(f"Difficulty: {self.difficulty.capitalize()}", True, BLACK)
        
        # Show active powerups
        powerup_text = self.font.render(f"Powerups: {self.player.get_active_powerups_text()}", True, BLACK)
        
        # Show objectives collected
        objective_text = self.font.render(f"Objectives: {self.objectives_collected}/{self.total_objectives}", True, BLACK)
        
        self.screen.blit(time_text, (10, 10))
        self.screen.blit(moves_text, (10, 40))
        self.screen.blit(move_text, (10, 70))
        self.screen.blit(score_text, (10, 100))
        self.screen.blit(decay_text, (10, 130))
        self.screen.blit(mode_text, (10, 160))
        self.screen.blit(difficulty_text, (10, 190))
        self.screen.blit(powerup_text, (10, 220))
        self.screen.blit(objective_text, (10, 250))
        self.screen.blit(level_text, (10, 280))
        self.screen.blit(total_score_text, (10, 310))
        
        # Draw controls info
        controls_text = self.font.render("Controls: Arrows=Move, A=Algorithm, R=Reset, 1/2/3=Difficulty", True, BLACK)
        self.screen.blit(controls_text, (self.width - controls_text.get_width() - 10, 10))
        
        # Draw powerup legend on the right side
        legend_x = self.width - 250  # Increased left margin for more space
        legend_y = 50
        
        # Calculate available space for legend
        available_width = self.width - legend_x - 20  # 20px right margin
        available_height = self.height - legend_y - 50  # 50px bottom margin
        
        # Determine if we should use compact mode (for very small windows)
        compact_mode = available_width < 200 or available_height < 300
        
        if compact_mode:
            # In compact mode, just show colored squares with short labels
            legend_title = self.font.render("POWERUPS:", True, BLACK)
            self.screen.blit(legend_title, (legend_x, legend_y))
            
            compact_powerups = [
                (PowerUp(0, 0, "speed", self.cell_size), "Speed"),
                (PowerUp(0, 0, "teleport", self.cell_size), "Port"),
                (PowerUp(0, 0, "wall_break", self.cell_size), "Break"),
                (PowerUp(0, 0, "score_multiplier", self.cell_size), "Score"),
                (PowerUp(0, 0, "time_freeze", self.cell_size), "Time"),
                (PowerUp(0, 0, "ghost", self.cell_size), "Ghost"),
                (PowerUp(0, 0, "decay_freeze", self.cell_size), "Decay"),
                (PowerUp(0, 0, "objective", self.cell_size), "Points")
            ]
            
            # Determine grid layout based on available space
            items_per_row = max(2, min(5, int(available_width / 60)))
            square_size = max(10, min(15, int(available_width / (items_per_row * 5))))
            
            # Draw compact grid of powerups
            for i, (powerup, label) in enumerate(compact_powerups):
                row = i // items_per_row
                col = i % items_per_row
                
                # Skip if we don't have space
                if row * 40 + 30 > available_height:
                    break
                
                # Draw square
                x_pos = legend_x + col * (available_width // items_per_row)
                y_pos = legend_y + 30 + row * 40
                square_rect = pygame.Rect(x_pos, y_pos, square_size, square_size)
                pygame.draw.rect(self.screen, powerup.get_color(), square_rect)
                
                # Draw compact label
                small_font = pygame.font.SysFont("Arial", 10)
                label_surface = small_font.render(label, True, BLACK)
                self.screen.blit(label_surface, (x_pos + square_size + 2, y_pos))
                
        else:
            # Regular mode with full descriptions
            legend_title = self.font.render("POWERUP LEGEND:", True, BLACK)
            self.screen.blit(legend_title, (legend_x, legend_y))
            
            # Create temporary powerup objects to get colors and descriptions
            legend_powerups = [
                PowerUp(0, 0, "speed", self.cell_size),
                PowerUp(0, 0, "teleport", self.cell_size),
                PowerUp(0, 0, "wall_break", self.cell_size),
                PowerUp(0, 0, "score_multiplier", self.cell_size),
                PowerUp(0, 0, "time_freeze", self.cell_size),
                PowerUp(0, 0, "ghost", self.cell_size),
                PowerUp(0, 0, "decay_freeze", self.cell_size),
                PowerUp(0, 0, "objective", self.cell_size)
            ]
        
            # Adjust font size based on window width
            legend_font_size = max(12, min(18, int(available_width / 15)))
            legend_font = pygame.font.SysFont("Arial", legend_font_size)
            
            # Calculate visible items based on available height
            item_height = 25  # Base height per item
            max_visible_items = min(len(legend_powerups), available_height // item_height)
            
            # Draw each powerup in the legend
            for i, powerup in enumerate(legend_powerups[:max_visible_items]):
                # Draw powerup square
                square_size = max(10, min(15, int(available_width / 20)))
                square_rect = pygame.Rect(legend_x, legend_y + 30 + i * item_height, square_size, square_size)
                pygame.draw.rect(self.screen, powerup.get_color(), square_rect)
                
                # Get powerup description
                full_desc = powerup.get_description()
                parts = full_desc.split(': ')
                
                # Determine if we need to abbreviate text based on available width
                if len(parts) > 1:
                    type_text = parts[0] + ":"
                    desc_text = parts[1]
                    
                    # Render with appropriate size and check if it fits
                    type_surface = legend_font.render(type_text, True, BLACK)
                    desc_surface = legend_font.render(desc_text, True, BLACK)
                    
                    # Check if we need to truncate the description
                    if type_surface.get_width() + desc_surface.get_width() > available_width - square_size - 25:
                        # Try to fit description on second line
                        self.screen.blit(type_surface, (legend_x + square_size + 10, legend_y + 30 + i * item_height))
                        
                        # Truncate description text if needed
                        max_desc_width = available_width - square_size - 30
                        if desc_surface.get_width() > max_desc_width:
                            # Truncate and add ellipsis
                            for j in range(len(desc_text), 0, -1):
                                truncated = desc_text[:j] + "..."
                                temp_surface = legend_font.render(truncated, True, BLACK)
                                if temp_surface.get_width() <= max_desc_width:
                                    desc_text = truncated
                                    break
                        
                        # Render description on second line
                        desc_surface = legend_font.render(desc_text, True, BLACK)
                        self.screen.blit(desc_surface, (legend_x + square_size + 20, legend_y + 30 + i * item_height + item_height//2))
                    else:
                        # Everything fits on one line
                        self.screen.blit(type_surface, (legend_x + square_size + 10, legend_y + 30 + i * item_height))
                        self.screen.blit(desc_surface, (legend_x + square_size + 10 + type_surface.get_width() + 5, 
                                                      legend_y + 30 + i * item_height))
                else:
                    # Simple text, just render it
                    desc_surface = legend_font.render(full_desc, True, BLACK)
                    
                    # Check if we need to truncate
                    if desc_surface.get_width() > available_width - square_size - 15:
                        # Truncate and add ellipsis
                        for j in range(len(full_desc), 0, -1):
                            truncated = full_desc[:j] + "..."
                            temp_surface = legend_font.render(truncated, True, BLACK)
                            if temp_surface.get_width() <= available_width - square_size - 15:
                                desc_surface = temp_surface
                                break
                    
                    self.screen.blit(desc_surface, (legend_x + square_size + 10, legend_y + 30 + i * item_height))
        
        # Draw popups
        if hasattr(self, 'popups'):
            dt = self.clock.get_time() / 1000  # Delta time in seconds
            font_popup = pygame.font.SysFont("Arial", 24)
            
            # Update and draw each popup
            for i, popup in enumerate(self.popups[:]):
                # Decrease duration and update alpha
                popup['duration'] -= dt
                if popup['duration'] <= 0:
                    # Remove expired popups
                    self.popups.remove(popup)
                    continue
                
                # Fade out effect near the end
                if popup['duration'] < 0.5:
                    popup['alpha'] = int(255 * popup['duration'] * 2)
                
                # Render popup
                popup_surface = font_popup.render(popup['message'], True, (255, 255, 0))
                popup_surface.set_alpha(popup['alpha'])
                
                # Center horizontally and position based on y_offset
                popup_x = self.width // 2 - popup_surface.get_width() // 2
                popup_y = self.height // 4 + popup['y_offset']
                
                # Background for better readability
                bg_rect = pygame.Rect(
                    popup_x - 5, 
                    popup_y - 5, 
                    popup_surface.get_width() + 10, 
                    popup_surface.get_height() + 10
                )
                bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
                bg_surface.fill((0, 0, 0, 128))  # Semi-transparent black
                self.screen.blit(bg_surface, (bg_rect.x, bg_rect.y))
                
                # Draw the text
                self.screen.blit(popup_surface, (popup_x, popup_y))
        
        # Draw game over message if completed
        if not self.game_active:
            font_large = pygame.font.SysFont("Arial", 36)
            
            if self.current_level > self.max_levels:
                # Final completion - show total results
                complete_text = font_large.render("All Levels Completed!", True, GREEN)
                self.screen.blit(complete_text, 
                                (self.width // 2 - complete_text.get_width() // 2, 
                                self.height // 2 - complete_text.get_height() // 2 - 60))
                
                # Show cumulative stats
                total_moves = sum(result["moves"] for result in self.level_results) if self.level_results else 0
                total_time = sum(result["time"] for result in self.level_results) if self.level_results else 0
                
                stats_text = self.font.render(f"Total Score: {self.total_score}", True, BLACK)
                self.screen.blit(stats_text, 
                                (self.width // 2 - stats_text.get_width() // 2, 
                                self.height // 2 - 30))
                
                moves_text = self.font.render(f"Total Moves: {total_moves}", True, BLACK)
                self.screen.blit(moves_text, 
                                (self.width // 2 - moves_text.get_width() // 2, 
                                self.height // 2))
                
                time_text = self.font.render(f"Total Time: {total_time:.1f}s", True, BLACK)
                self.screen.blit(time_text, 
                                (self.width // 2 - time_text.get_width() // 2, 
                                self.height // 2 + 30))
            else:
                # Level complete - show level results
                complete_text = font_large.render(f"Level {self.current_level} Completed!", True, GREEN)
                self.screen.blit(complete_text, 
                                (self.width // 2 - complete_text.get_width() // 2, 
                                self.height // 2 - complete_text.get_height() // 2))
            
            press_r_text = self.font.render("Press R to restart", True, BLACK)
            self.screen.blit(press_r_text, 
                            (self.width // 2 - press_r_text.get_width() // 2, 
                            self.height // 2 + 60))
            
            # Display high scores
            scores = self.scoreboard.get_high_scores()
            y_pos = self.height // 2 + 100
            high_score_text = self.font.render("High Scores:", True, BLACK)
            self.screen.blit(high_score_text, (self.width // 2 - 50, y_pos))
            y_pos += 30
            
            for i, (name, score) in enumerate(scores[:5]):
                score_entry = self.font.render(f"{i+1}. {name}: {score}", True, BLACK)
                self.screen.blit(score_entry, (self.width // 2 - 50, y_pos))
                y_pos += 25
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        prev_time = pygame.time.get_ticks()
        self.last_decay_time = prev_time  # Initialize decay timer
        
        while True:
            # Calculate delta time
            current_time = pygame.time.get_ticks()
            dt = (current_time - prev_time) / 1000.0  # Convert to seconds
            prev_time = current_time
            
            self.handle_events()
            
            if self.algorithm_mode and self.game_active:
                self.run_algorithm_step()
            
            # Update game state
            self.update(dt)
            
            # Draw
            self.draw()
            
            # Cap the frame rate
            self.clock.tick(FPS)

    def show_popup(self, message, duration=2.0):
        """Show a popup message on screen"""
        if not hasattr(self, 'popups'):
            self.popups = []
        
        # Add new popup with message, duration and initial alpha
        self.popups.append({
            'message': message,
            'duration': duration,
            'alpha': 255,
            'y_offset': len(self.popups) * 30  # Stack popups vertically
        })

    def update(self, dt):
        """Update game state"""
        # Update player state
        self.player.update(dt)
        
        # Update popups
        if hasattr(self, 'popups'):
            for popup in self.popups[:]:
                popup['duration'] -= dt
                if popup['duration'] <= 0:
                    self.popups.remove(popup)
        
        # Handle score decay based on time
        if self.game_active and self.score_decay_active and not self.player.time_freeze_active and not self.player.decay_freeze_active:
            current_time = pygame.time.get_ticks()
            time_passed = (current_time - self.last_decay_time) / 1000.0  # Convert to seconds
            
            # Update score decay - only decay if it's been at least 1 second
            if time_passed >= 1.0:
                points_to_deduct = int(self.score_decay_rate * time_passed)
                if points_to_deduct > 0:
                    self.score = max(0, self.score - points_to_deduct)  # Don't go below 0
                    self.last_decay_time = current_time
                    
                    # Show decay notification every 5 seconds
                    self.decay_timer += time_passed
                    if self.decay_timer >= 5.0:
                        self.decay_timer = 0
                        if points_to_deduct > 0:
                            # Only show if points were actually deducted
                            decay_rate_per_sec = int(self.score_decay_rate)
                            self.show_popup(f"-{decay_rate_per_sec}/sec Time Penalty", duration=1.0)

    def _get_maze_for_level(self, level):
        """Return a fixed maze for the specified level"""
        # Define the mazes based on difficulty level
        # New representation: 0 = path, 1 = wall, 2 = start, 3 = goal
        # (Previously: 0 = path, 1 = wall, 2 = goal, 3 = start)
        if level == 1:
            # Level 1: Medium complexity maze (15x15) with multiple path options
            pattern = [
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                [1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                [1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1],
                [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1],
                [1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1],
                [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
                [1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1],
                [1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
                [1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1],
                [1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
                [1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1],
                [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1],
                [1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1],
                [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 1],
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            ]
            
        elif level == 2:
            # Level 2: New complex maze with spiral elements, multiple paths, and a central chamber
            pattern = [
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                [1, 2, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
                [1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1],
                [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1],
                [1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1],
                [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1],
                [1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1],
                [1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
                [1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1],
                [1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1],
                [1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1],
                [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
                [1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1],
                [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
                [1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1],
                [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1],
                [1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1],
                [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 1],
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            ]
            
        else:  # level 3
            # Level 3: Advanced labyrinth with chambers, hidden paths, and multiple routes
            pattern = [
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                [1, 2, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
                [1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1],
                [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1],
                [1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1],
                [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 1],
                [1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1],
                [1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1],
                [1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1],
                [1, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
                [1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1],
                [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                [1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1],
                [1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1],
                [1, 0, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 0, 1],
                [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1],
                [1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1],
                [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                [1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1],
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1],
                [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
                [1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1],
                [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 1],
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            ]
        
        # Create a maze of the exact size needed for the pattern
        height = len(pattern)
        width = len(pattern[0])
        maze = np.ones((height, width), dtype=int)  # Changed from bool to int
        
        # Find start and goal positions
        start_pos = None
        goal_pos = None
        
        # Convert pattern directly to maze
        for y in range(height):
            for x in range(width):
                value = pattern[y][x]
                if value == 2:  # Start position
                    start_pos = (x, y)
                    maze[y][x] = 0  # Mark as path
                elif value == 3:  # Goal position
                    goal_pos = (x, y)
                    maze[y][x] = 0  # Mark as path
                else:
                    maze[y][x] = value  # Set the cell value (0 = path, 1 = wall)
        
        # Update player start position if found
        if start_pos:
            self.player = Player(start_pos[0], start_pos[1], self.cell_size)
            # Also update the visited cells to include start position
            self.visited_cells = set()
            self.visited_cells.add(start_pos)
        
        # Update goal position if found
        if goal_pos:
            self.goal_pos = goal_pos
        
        # Update maze_size to match the actual maze dimensions
        self.maze_size = (width, height)
        
        # Verify path exists and print message if it does
        if self._check_path_exists(maze, start_pos, goal_pos):
            print(f"Level {level} maze has a valid path from start to goal.")
        else:
            print(f"WARNING: Level {level} maze has NO valid path from start to goal!")
        
        return maze
    
    def next_level(self):
        """Progress to the next level or end game if all levels complete"""
        # Save current level results
        level_result = {
            "level": self.current_level,
            "score": self.score,
            "moves": self.moves,
            "time": (pygame.time.get_ticks() - self.time_started) / 1000,
            "objectives_collected": self.objectives_collected,
            "total_objectives": self.total_objectives
        }
        self.level_results.append(level_result)
        
        # Add to total score
        self.total_score += self.score
        
        # Check if all levels completed
        if self.current_level >= self.max_levels:
            # Game completed - show final results
            self.show_final_results()
            self.game_active = False
        else:
            # Progress to next level
            self.current_level += 1
            
            # Reset random seeds for next level consistency
            self.reset_seeds()
            
            # Set up next level and make sure game_active is set to True
            self.setup_level()
            self.game_active = True  # Ensure game is active
            self.show_popup(f"Level {self.current_level} Starting!", duration=2.0)
    
    def setup_level(self):
        """Set up the current level"""
        # Use the shared reset_level method
        self.reset_level()
        
        # Reset algorithm runner if in algorithm mode
        if self.algorithm_mode:
            self.algorithm_runner = AlgorithmRunner(self.maze, self.maze_size)
            try:
                self.algorithm_runner.load_algorithm_from_file("sample_algorithm.py")
            except Exception as e:
                print(f"Error loading algorithm: {e}")

    def show_final_results(self):
        """Show final results after all levels are completed"""
        # Calculate total stats
        total_moves = sum(result["moves"] for result in self.level_results)
        total_time = sum(result["time"] for result in self.level_results)
        total_objectives = sum(result["objectives_collected"] for result in self.level_results)
        total_possible = sum(result["total_objectives"] for result in self.level_results)
        
        # Show results
        self.show_popup(f"All Levels Completed!", duration=10.0)
        self.show_popup(f"Total Score: {self.total_score}", duration=10.0)
        self.show_popup(f"Total Moves: {total_moves}", duration=10.0)
        self.show_popup(f"Total Time: {total_time:.1f}s", duration=10.0)
        self.show_popup(f"Objectives: {total_objectives}/{total_possible}", duration=10.0)
        
        # Save to scoreboard with special name
        player_name = "Algorithm" if self.algorithm_mode else "Player"
        self.scoreboard.add_score(f"{player_name} (All Levels)", self.total_score)

    def reset_seeds(self):
        """Reset random seeds for consistent gameplay"""
        # Reset main random seed
        random.seed(42)
        np.random.seed(42)

    def _check_path_exists(self, maze, start=(0, 0), end=None):
        """Verify a path exists between start and end points in the maze"""
        if end is None:
            end = (self.maze_size[0] - 1, self.maze_size[1] - 1)
        
        width, height = self.maze_size
        visited = set()
        queue = [start]
        
        while queue:
            x, y = queue.pop(0)
            if (x, y) == end:
                return True
            
            if (x, y) in visited:
                continue
                
            visited.add((x, y))
            
            # Check all four directions
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < width and 0 <= ny < height and 
                    maze[ny][nx] == 0 and (nx, ny) not in visited):  # Path is represented by 0
                    queue.append((nx, ny))
        
        return False

    def reset_level(self):
        """Reset only the current level, not the entire game progress"""
        # Get maze for current level
        self.maze = self._get_maze_for_level(self.current_level)
        
        # Reset player powerup states if they exist
        if hasattr(self, 'player'):
            # Store the position as it may have been set by _get_maze_for_level
            player_x, player_y = self.player.x, self.player.y
            # Create a fresh player object to reset all powerup states
            self.player = Player(player_x, player_y, self.cell_size)
        
        # Reset visited cells
        self.visited_cells = set()
        if hasattr(self, 'player'):
            self.visited_cells.add((self.player.x, self.player.y))  # Start position is visited
        
        # Reset powerups
        self.powerups = []
        self.portals = []  # We'll keep this empty list but not use it
        self._generate_powerups(POWERUP_COUNTS[self.difficulty])
        
        # Debug: Print maze after regenerating powerups
        print(f"\nReset Level {self.current_level} - Maze with powerups:")
        self.print_numeric_maze()
        
        # Make sure score decay rate is updated
        self.score_decay_rate = self._get_decay_rate()
        
        # Reset algorithm mode
        self.algorithm_mode = False
        self.algorithm_runner = None
        
        # Reset level state
        self.game_active = True
        self.moves = 0
        self.time_started = pygame.time.get_ticks()
        self.score = 1000  # Start with 1000 points
        self.objectives_collected = 0
        self.total_objectives = 0
        
        # Reset movement cooldown
        self.last_move_time = 0
        self.can_move = True
        
        # Reset score decay
        self.decay_timer = 0
        self.last_decay_time = pygame.time.get_ticks()

if __name__ == "__main__":
    game = MazeGame()
    game.run() 