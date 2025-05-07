class PowerUp:
    def __init__(self, x, y, powerup_type, cell_size):
        """
        Initialize a powerup
        
        Args:
            x, y: Position in the maze grid
            powerup_type: Type of powerup ("speed", "reveal", "teleport", etc.)
            cell_size: Size of each cell for rendering
        """
        self.x = x
        self.y = y
        self.type = powerup_type
        self.cell_size = cell_size
        
        # Initialize timing for animations
        self.animation_time = 0
        self.active = True
    
    def update(self, dt):
        """Update powerup animation"""
        self.animation_time += dt
        
    def get_color(self):
        """Get powerup color based on type"""
        if self.type == "speed":
            return (255, 0, 0)  # Red
        elif self.type == "reveal":
            return (0, 0, 255)  # Blue
        elif self.type == "teleport":
            return (255, 165, 0)  # Orange
        else:
            return (128, 0, 128)  # Purple (default) 