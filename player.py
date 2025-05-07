class Player:
    def __init__(self, x, y, cell_size):
        self.x = x
        self.y = y
        self.cell_size = cell_size
        self.has_speed_boost = False
        self.speed_boost_duration = 0
    
    def move(self, x, y):
        """Move player to a new position"""
        self.x = x
        self.y = y
    
    def apply_speed_boost(self, duration=10):
        """Apply a speed boost for a certain duration (in seconds)"""
        self.has_speed_boost = True
        self.speed_boost_duration = duration
    
    def update(self, dt):
        """Update player state based on elapsed time"""
        if self.has_speed_boost:
            self.speed_boost_duration -= dt
            if self.speed_boost_duration <= 0:
                self.has_speed_boost = False
                self.speed_boost_duration = 0 