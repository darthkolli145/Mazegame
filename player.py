class Player:
    def __init__(self, x, y, cell_size):
        self.x = x
        self.y = y
        self.cell_size = cell_size
        
        # Player state and active powerups
        self.has_speed_boost = False
        self.speed_boost_duration = 0
        self.speed_multiplier = 1
        
        self.wall_break_active = False
        self.wall_break_duration = 0
        self.wall_break_strength = 0
        
        self.score_multiplier_active = False
        self.score_multiplier_duration = 0
        self.score_multiplier_value = 1.0
        
        self.time_freeze_active = False
        self.time_freeze_duration = 0
        
        self.ghost_mode_active = False
        self.ghost_mode_duration = 0
        
        # Decay freeze powerup
        self.decay_freeze_active = False
        self.decay_freeze_duration = 0
        
        # Powerup collection statistics
        self.powerups_collected = 0
        self.walls_broken = 0
    
    def move(self, x, y):
        """Move player to a new position"""
        self.x = x
        self.y = y
    
    def apply_powerup(self, powerup_type, duration=0, strength=1):
        """Apply a powerup effect to the player"""
        self.powerups_collected += 1
        
        if powerup_type == "speed":
            self.has_speed_boost = True
            self.speed_boost_duration = duration
            self.speed_multiplier = strength
        
        elif powerup_type == "wall_break":
            self.wall_break_active = True
            self.wall_break_duration = duration
            self.wall_break_strength = strength
        
        elif powerup_type == "score_multiplier":
            self.score_multiplier_active = True
            self.score_multiplier_duration = duration
            self.score_multiplier_value = strength
        
        elif powerup_type == "time_freeze":
            self.time_freeze_active = True
            self.time_freeze_duration = duration
        
        elif powerup_type == "ghost":
            self.ghost_mode_active = True
            self.ghost_mode_duration = duration
        
        elif powerup_type == "decay_freeze":
            self.decay_freeze_active = True
            self.decay_freeze_duration = duration
    
    def can_break_wall(self):
        """Check if player can break a wall"""
        return self.wall_break_active and self.wall_break_strength > 0
    
    def break_wall(self):
        """Use wall breaking ability"""
        if self.wall_break_active and self.wall_break_strength > 0:
            self.wall_break_strength -= 1
            self.walls_broken += 1
            return True
        return False
    
    def get_score_multiplier(self):
        """Get current score multiplier"""
        return self.score_multiplier_value if self.score_multiplier_active else 1.0
    
    def is_time_frozen(self):
        """Check if time is frozen"""
        return self.time_freeze_active
    
    def can_pass_through_walls(self):
        """Check if player can pass through walls (ghost mode)"""
        return self.ghost_mode_active
    
    def get_vision_range(self):
        """Get the current vision range of the player"""
        # Return a very large value to ensure the entire maze is visible
        return 1000  # Effectively unlimited vision range
    
    def get_speed_multiplier(self):
        """Get current speed multiplier (affects cooldown time)"""
        return self.speed_multiplier if self.has_speed_boost else 1.0
    
    def update(self, dt):
        """Update player state based on elapsed time"""
        if self.has_speed_boost:
            self.speed_boost_duration -= dt
            if self.speed_boost_duration <= 0:
                self.has_speed_boost = False
                self.speed_boost_duration = 0
                self.speed_multiplier = 1
        
        if self.wall_break_active:
            self.wall_break_duration -= dt
            if self.wall_break_duration <= 0:
                self.wall_break_active = False
                self.wall_break_duration = 0
                self.wall_break_strength = 0
        
        if self.score_multiplier_active:
            self.score_multiplier_duration -= dt
            if self.score_multiplier_duration <= 0:
                self.score_multiplier_active = False
                self.score_multiplier_duration = 0
                self.score_multiplier_value = 1.0
        
        if self.time_freeze_active:
            self.time_freeze_duration -= dt
            if self.time_freeze_duration <= 0:
                self.time_freeze_active = False
                self.time_freeze_duration = 0
        
        if self.ghost_mode_active:
            self.ghost_mode_duration -= dt
            if self.ghost_mode_duration <= 0:
                self.ghost_mode_active = False
                self.ghost_mode_duration = 0
        
        if self.decay_freeze_active:
            self.decay_freeze_duration -= dt
            if self.decay_freeze_duration <= 0:
                self.decay_freeze_active = False
                self.decay_freeze_duration = 0
    
    def get_active_powerups_text(self):
        """Get text describing active powerups"""
        active_powerups = []
        
        if self.has_speed_boost:
            active_powerups.append(f"Speed ({self.speed_boost_duration:.1f}s)")
        
        if self.wall_break_active:
            active_powerups.append(f"Wall Break ({self.wall_break_duration:.1f}s, {self.wall_break_strength} left)")
        
        if self.score_multiplier_active:
            active_powerups.append(f"Score x{self.score_multiplier_value} ({self.score_multiplier_duration:.1f}s)")
        
        if self.time_freeze_active:
            active_powerups.append(f"Time Freeze ({self.time_freeze_duration:.1f}s)")
        
        if self.ghost_mode_active:
            active_powerups.append(f"Ghost ({self.ghost_mode_duration:.1f}s)")
        
        if self.decay_freeze_active:
            active_powerups.append(f"Decay Shield ({self.decay_freeze_duration:.1f}s)")
        
        return ", ".join(active_powerups) if active_powerups else "None" 