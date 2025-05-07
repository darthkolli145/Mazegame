import pygame
import sys
import random
from maze_generator import MazeGenerator
from player import Player
from powerup import PowerUp
from portal import Portal
from algorithm_runner import AlgorithmRunner
from scoreboard import Scoreboard
from settings import *

class MazeGame:
    def __init__(self, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, difficulty="medium"):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(GAME_TITLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 18)
        
        # Set difficulty
        self.difficulty = difficulty
        self.maze_size = DIFFICULTIES[difficulty]["maze_size"]
        self.time_factor = DIFFICULTIES[difficulty]["time_factor"]
        self.move_penalty = DIFFICULTIES[difficulty]["move_penalty"]
        
        # Game objects
        self.cell_size = CELL_SIZE
        self.maze_generator = MazeGenerator(self.maze_size[0], self.maze_size[1])
        self.maze = self.maze_generator.generate()
        
        # Player starts at top-left
        self.player = Player(0, 0, self.cell_size)
        
        # Goal is at bottom-right
        self.goal_pos = (self.maze_size[0] - 1, self.maze_size[1] - 1)
        
        # Powerups and portals
        self.powerups = []
        self.portals = []
        self._generate_powerups(POWERUP_COUNTS[difficulty])
        self._generate_portals(PORTAL_PAIR_COUNTS[difficulty])
        
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
        self.score = 0
    
    def _generate_powerups(self, count):
        for _ in range(count):
            # Don't place powerups at start, end, or walls
            while True:
                x = random.randint(0, self.maze_size[0] - 1)
                y = random.randint(0, self.maze_size[1] - 1)
                if (x, y) != (0, 0) and (x, y) != self.goal_pos and not self.maze[y][x]:
                    break
            
            # Random powerup type
            powerup_type = random.choice(["speed", "reveal", "teleport"])
            self.powerups.append(PowerUp(x, y, powerup_type, self.cell_size))
    
    def _generate_portals(self, pairs):
        for i in range(pairs):
            # First portal of the pair
            while True:
                x1 = random.randint(0, self.maze_size[0] - 1)
                y1 = random.randint(0, self.maze_size[1] - 1)
                if (x1, y1) != (0, 0) and (x1, y1) != self.goal_pos and not self.maze[y1][x1]:
                    valid_spot = True
                    for p in self.portals:
                        if p.x == x1 and p.y == y1:
                            valid_spot = False
                            break
                    for p in self.powerups:
                        if p.x == x1 and p.y == y1:
                            valid_spot = False
                            break
                    if valid_spot:
                        break
            
            # Second portal of the pair
            while True:
                x2 = random.randint(0, self.maze_size[0] - 1)
                y2 = random.randint(0, self.maze_size[1] - 1)
                if (x2, y2) != (0, 0) and (x2, y2) != self.goal_pos and (x2, y2) != (x1, y1) and not self.maze[y2][x2]:
                    valid_spot = True
                    for p in self.portals:
                        if p.x == x2 and p.y == y2:
                            valid_spot = False
                            break
                    for p in self.powerups:
                        if p.x == x2 and p.y == y2:
                            valid_spot = False
                            break
                    if valid_spot:
                        break
            
            # Create linked portals
            portal1 = Portal(x1, y1, (x2, y2), i, self.cell_size)
            portal2 = Portal(x2, y2, (x1, y1), i, self.cell_size)
            self.portals.append(portal1)
            self.portals.append(portal2)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if not self.algorithm_mode and self.game_active:
                    # Player movement
                    if event.key == pygame.K_UP:
                        self.move_player(0, -1)
                    elif event.key == pygame.K_DOWN:
                        self.move_player(0, 1)
                    elif event.key == pygame.K_LEFT:
                        self.move_player(-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        self.move_player(1, 0)
                
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
                
                # Quit
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
    
    def move_player(self, dx, dy):
        new_x = self.player.x + dx
        new_y = self.player.y + dy
        
        # Check if move is valid (within bounds and not a wall)
        if (0 <= new_x < self.maze_size[0] and 
            0 <= new_y < self.maze_size[1] and 
            not self.maze[new_y][new_x]):
            self.player.move(new_x, new_y)
            self.moves += 1
            
            # Check for powerups
            for powerup in self.powerups[:]:
                if powerup.x == new_x and powerup.y == new_y:
                    self.apply_powerup(powerup)
                    self.powerups.remove(powerup)
            
            # Check for portals
            for portal in self.portals:
                if portal.x == new_x and portal.y == new_y:
                    # Teleport to linked portal
                    self.player.move(portal.target[0], portal.target[1])
                    break
            
            # Check for goal
            if (new_x, new_y) == self.goal_pos or (self.player.x, self.player.y) == self.goal_pos:
                self.complete_level()
    
    def apply_powerup(self, powerup):
        if powerup.type == "speed":
            # Give the player bonus points for speed boost
            self.score += 100
        elif powerup.type == "reveal":
            # Reveal a path to the goal (for now just add points)
            self.score += 200
        elif powerup.type == "teleport":
            # Randomly teleport closer to the goal
            goal_x, goal_y = self.goal_pos
            current_x, current_y = self.player.x, self.player.y
            
            # Try to move closer to goal
            if random.choice([True, False]):
                new_x = current_x + (1 if goal_x > current_x else -1)
                new_y = current_y
            else:
                new_x = current_x
                new_y = current_y + (1 if goal_y > current_y else -1)
            
            # Ensure the new position is valid
            if (0 <= new_x < self.maze_size[0] and 
                0 <= new_y < self.maze_size[1] and 
                not self.maze[new_y][new_x]):
                self.player.move(new_x, new_y)
            
            self.score += 150
    
    def start_algorithm_mode(self):
        # Reset for a fair comparison
        self.reset_game()
        self.algorithm_mode = True
        self.algorithm_runner = AlgorithmRunner(self.maze, self.maze_size)
        
        # Try to load user's algorithm if specified
        try:
            self.algorithm_runner.load_algorithm_from_file("sample_algorithm.py")
        except:
            # If loading fails, just use the default algorithm
            pass
    
    def run_algorithm_step(self):
        if self.algorithm_runner and self.game_active:
            # Control algorithm speed
            self.algorithm_timer += 1
            if self.algorithm_timer >= FPS / self.algorithm_speed:
                self.algorithm_timer = 0
                next_move = self.algorithm_runner.get_next_move(self.player.x, self.player.y, self.goal_pos)
                if next_move:
                    dx, dy = next_move
                    self.move_player(dx, dy)
                else:
                    # Algorithm failed to find path
                    self.algorithm_mode = False
    
    def complete_level(self):
        elapsed_time = (pygame.time.get_ticks() - self.time_started) / 1000
        # Calculate score based on time, moves, and powerups
        time_score = max(1000 - int(elapsed_time * self.time_factor), 0)
        move_score = max(1000 - self.moves * self.move_penalty, 0)
        
        final_score = self.score + time_score + move_score
        
        # Score multiplier based on difficulty
        if self.difficulty == "easy":
            final_score = int(final_score * 0.8)
        elif self.difficulty == "medium":
            final_score = int(final_score * 1.0)
        elif self.difficulty == "hard":
            final_score = int(final_score * 1.5)
        
        player_name = "Algorithm" if self.algorithm_mode else "Player"
        self.scoreboard.add_score(player_name, final_score)
        self.game_active = False
    
    def change_difficulty(self, difficulty):
        if difficulty in DIFFICULTIES:
            self.difficulty = difficulty
            self.reset_game()
    
    def reset_game(self):
        # Update settings for current difficulty
        self.maze_size = DIFFICULTIES[self.difficulty]["maze_size"]
        self.time_factor = DIFFICULTIES[self.difficulty]["time_factor"]
        self.move_penalty = DIFFICULTIES[self.difficulty]["move_penalty"]
        
        # Create a new maze generator with the current size
        self.maze_generator = MazeGenerator(self.maze_size[0], self.maze_size[1])
        self.maze = self.maze_generator.generate()
        
        # Reset player and goal
        self.player = Player(0, 0, self.cell_size)
        self.goal_pos = (self.maze_size[0] - 1, self.maze_size[1] - 1)
        
        # Reset powerups and portals
        self.powerups = []
        self.portals = []
        self._generate_powerups(POWERUP_COUNTS[self.difficulty])
        self._generate_portals(PORTAL_PAIR_COUNTS[self.difficulty])
        
        # Reset algorithm runner
        self.algorithm_mode = False
        self.algorithm_runner = None
        
        # Reset game state
        self.game_active = True
        self.moves = 0
        self.time_started = pygame.time.get_ticks()
        self.score = 0
    
    def draw(self):
        self.screen.fill(WHITE)
        
        # Draw maze
        offset_x = (self.width - self.maze_size[0] * self.cell_size) // 2
        offset_y = (self.height - self.maze_size[1] * self.cell_size) // 2
        
        for y in range(self.maze_size[1]):
            for x in range(self.maze_size[0]):
                rect = pygame.Rect(
                    offset_x + x * self.cell_size,
                    offset_y + y * self.cell_size,
                    self.cell_size,
                    self.cell_size
                )
                if self.maze[y][x]:  # Wall
                    pygame.draw.rect(self.screen, BLACK, rect)
                else:  # Path
                    pygame.draw.rect(self.screen, WHITE, rect, 1)
        
        # Draw goal
        goal_rect = pygame.Rect(
            offset_x + self.goal_pos[0] * self.cell_size,
            offset_y + self.goal_pos[1] * self.cell_size,
            self.cell_size,
            self.cell_size
        )
        pygame.draw.rect(self.screen, GREEN, goal_rect)
        
        # Draw powerups
        for powerup in self.powerups:
            color = RED if powerup.type == "speed" else BLUE if powerup.type == "reveal" else ORANGE
            powerup_rect = pygame.Rect(
                offset_x + powerup.x * self.cell_size + self.cell_size // 4,
                offset_y + powerup.y * self.cell_size + self.cell_size // 4,
                self.cell_size // 2,
                self.cell_size // 2
            )
            pygame.draw.rect(self.screen, color, powerup_rect)
        
        # Draw portals
        for portal in self.portals:
            portal_rect = pygame.Rect(
                offset_x + portal.x * self.cell_size + self.cell_size // 4,
                offset_y + portal.y * self.cell_size + self.cell_size // 4,
                self.cell_size // 2,
                self.cell_size // 2
            )
            # Use different colors for different portal pairs
            color_value = 100 + (portal.id * 50) % 155
            portal_color = (color_value, 0, color_value)
            pygame.draw.ellipse(self.screen, portal_color, portal_rect)
        
        # Draw player
        player_rect = pygame.Rect(
            offset_x + self.player.x * self.cell_size + self.cell_size // 4,
            offset_y + self.player.y * self.cell_size + self.cell_size // 4,
            self.cell_size // 2,
            self.cell_size // 2
        )
        pygame.draw.rect(self.screen, RED, player_rect)
        
        # Draw UI information
        elapsed_time = (pygame.time.get_ticks() - self.time_started) / 1000
        time_text = self.font.render(f"Time: {elapsed_time:.1f}s", True, BLACK)
        moves_text = self.font.render(f"Moves: {self.moves}", True, BLACK)
        score_text = self.font.render(f"Score: {self.score}", True, BLACK)
        mode_text = self.font.render(
            f"Mode: {'Algorithm' if self.algorithm_mode else 'Player'}", 
            True, 
            BLACK
        )
        difficulty_text = self.font.render(f"Difficulty: {self.difficulty.capitalize()}", True, BLACK)
        
        self.screen.blit(time_text, (10, 10))
        self.screen.blit(moves_text, (10, 40))
        self.screen.blit(score_text, (10, 70))
        self.screen.blit(mode_text, (10, 100))
        self.screen.blit(difficulty_text, (10, 130))
        
        # Draw controls info
        controls_text = self.font.render("Controls: Arrows=Move, A=Algorithm, R=Reset, 1/2/3=Difficulty", True, BLACK)
        self.screen.blit(controls_text, (self.width - controls_text.get_width() - 10, 10))
        
        # Draw game over message if completed
        if not self.game_active:
            font_large = pygame.font.SysFont("Arial", 36)
            complete_text = font_large.render("Maze Completed!", True, GREEN)
            press_r_text = self.font.render("Press R to restart", True, BLACK)
            
            self.screen.blit(complete_text, 
                            (self.width // 2 - complete_text.get_width() // 2, 
                            self.height // 2 - complete_text.get_height() // 2))
            self.screen.blit(press_r_text, 
                            (self.width // 2 - press_r_text.get_width() // 2, 
                            self.height // 2 + 40))
            
            # Display high scores
            scores = self.scoreboard.get_high_scores()
            y_pos = self.height // 2 + 80
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
        while True:
            self.handle_events()
            
            if self.algorithm_mode and self.game_active:
                self.run_algorithm_step()
            
            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = MazeGame()
    game.run() 