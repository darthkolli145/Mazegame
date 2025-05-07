class Portal:
    def __init__(self, x, y, target_pos, portal_id, cell_size):
        """
        Initialize a portal
        
        Args:
            x, y: Position in the maze grid
            target_pos: Tuple (x, y) for the linked portal's position
            portal_id: ID to identify portal pairs
            cell_size: Size of each cell for rendering
        """
        self.x = x
        self.y = y
        self.target = target_pos
        self.id = portal_id
        self.cell_size = cell_size
        
        # Portal animation
        self.animation_time = 0
        self.cooldown = 0  # Cooldown to prevent infinite portal loops
    
    def update(self, dt):
        """Update portal animation and cooldown"""
        self.animation_time += dt
        
        if self.cooldown > 0:
            self.cooldown -= dt
    
    def teleport_ready(self):
        """Check if portal can be used (not on cooldown)"""
        return self.cooldown <= 0
    
    def reset_cooldown(self, time=0.5):
        """Set cooldown after teleportation"""
        self.cooldown = time 