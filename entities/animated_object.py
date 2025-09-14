import pygame
from entities.animation import Animation, AnimationManager

class AnimatedObject(pygame.sprite.Sprite):
    """Animated object that moves back and forth with walk animation and attacks player"""
    
    def __init__(self, x, y, groups, spritesheet_path, json_path, movement_range=80, scale=2.0):
        super().__init__(groups)
        
        # Position and movement
        self.start_x = x
        self.current_x = x
        self.ground_y = y  # Store the ground level
        self.movement_range = movement_range
        self.movement_speed = 1.0  # pixels per frame
        self.direction = 1  # 1 for right, -1 for left
        self.target_x = x + movement_range
        
        # Visibility control
        self.visible = True  # Default to visible, can be set externally
        
        # Enemy properties
        self.max_health = 3  # Health points
        self.health = self.max_health
        self.is_alive = True
        self.take_damage_cooldown = 0
        self.take_damage_cooldown_max = 30  # 0.5 seconds invulnerability after taking damage
        
        # Attack system
        self.attack_range = 100  # Distance to detect player
        self.attack_damage = 10
        self.attack_cooldown = 0
        self.attack_cooldown_max = 60  # 1 second at 60 FPS
        self.last_attack_time = 0
        self.is_attacking = False  # Whether currently following/attacking player
        self.follow_speed = 1.5  # Speed when following player (faster than normal)
        
        # Animation system
        self.animation_manager = AnimationManager()
        
        # Load animations
        idle_animation = Animation(spritesheet_path, json_path, scale)
        walk_animation = Animation(spritesheet_path, json_path, scale)
        
        # Set up animations based on frame tags from JSON
        # The JSON has "Idle" (frames 0-3) and "Follow" (frames 4-9) animations
        # Create idle animation (frames 0-3)
        idle_animation.frames = idle_animation.frames[0:4]  # First 4 frames for idle
        idle_animation.frame_durations = idle_animation.frame_durations[0:4]
        idle_animation.current_frame = 0
        idle_animation.frame_timer = 0
        
        # Create walk animation (frames 4-9)
        walk_animation.frames = walk_animation.frames[4:10]  # Frames 4-9 for walk
        walk_animation.frame_durations = walk_animation.frame_durations[4:10]
        walk_animation.current_frame = 0
        walk_animation.frame_timer = 0
        
        # Add animations to manager
        self.animation_manager.add_animation('idle', idle_animation)
        self.animation_manager.add_animation('walk', walk_animation)
        
        # Set initial animation
        self.animation_manager.set_animation('walk', loop=True)
        
        # Set up sprite - position on ground
        self.image = self.animation_manager.get_current_frame()
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y  # Position bottom of sprite on ground
        
        # Movement state
        self.moving = True
        
        # Platform detection
        self.platform_start_x = None
        self.platform_end_x = None
        self.on_platform = False
        self.platform_check_cooldown = 0
        self.platform_check_interval = 10  # Check every 10 frames instead of every frame
        
    def update(self, player=None, level=None):
        """Update animation, movement, and attack"""
        # Check if dead or not visible
        if not self.is_alive or not self.visible:
            return
        
        # Update animation
        self.animation_manager.update()
        
        # Update cooldowns
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.take_damage_cooldown > 0:
            self.take_damage_cooldown -= 1
        
        # Check for platform tiles and adjust movement (with cooldown to prevent glitching)
        if level and self.platform_check_cooldown <= 0:
            self.check_platform_collision(level)
            self.platform_check_cooldown = self.platform_check_interval
        elif level:
            self.platform_check_cooldown -= 1
        
        # Check for player and determine behavior
        if player:
            player_distance = self.get_distance_to_player(player)
            
            # If player is within attack range, start following/attacking
            if player_distance <= self.attack_range:
                if not self.is_attacking:
                    self.is_attacking = True
                    print("Animated object started following player!")
                
                # Follow the player
                self.follow_player(player)
                
                # Attack if cooldown is ready
                if self.attack_cooldown <= 0:
                    self.attack_player(player)
            else:
                # Player is too far, stop attacking and resume normal movement
                if self.is_attacking:
                    self.is_attacking = False
                    print("Animated object stopped following player, resuming patrol.")
        
        # Update movement (only if not attacking)
        if self.moving and not self.is_attacking:
            # Move towards target
            self.current_x += self.direction * self.movement_speed
            
            # Use platform boundaries if on platform, otherwise use original movement
            if self.on_platform and self.platform_start_x is not None and self.platform_end_x is not None:
                # Constrain movement to platform boundaries
                self.current_x = max(self.platform_start_x, min(self.current_x, self.platform_end_x))
                
                # Check if reached platform edge
                if self.direction > 0 and self.current_x >= self.platform_end_x:
                    # Reached right edge of platform, turn around
                    self.current_x = self.platform_end_x
                    self.direction = -1
                    self.animation_manager.set_facing(False)  # Face left
                elif self.direction < 0 and self.current_x <= self.platform_start_x:
                    # Reached left edge of platform, turn around
                    self.current_x = self.platform_start_x
                    self.direction = 1
                    self.animation_manager.set_facing(True)  # Face right
            else:
                # Original movement logic
                if self.direction > 0 and self.current_x >= self.target_x:
                    # Reached right target, turn around
                    self.current_x = self.target_x
                    self.direction = -1
                    self.target_x = self.start_x
                    self.animation_manager.set_facing(False)  # Face left
                elif self.direction < 0 and self.current_x <= self.start_x:
                    # Reached left target, turn around
                    self.current_x = self.start_x
                    self.direction = 1
                    self.target_x = self.start_x + self.movement_range
                    self.animation_manager.set_facing(True)  # Face right
        
        # Update sprite image and position
        self.image = self.animation_manager.get_current_frame()
        self.rect.centerx = int(self.current_x)
        self.rect.bottom = self.ground_y  # Keep bottom on ground
        
    def stop_moving(self):
        """Stop the object from moving"""
        self.moving = False
        self.animation_manager.set_animation('idle', loop=True)
        
    def start_moving(self):
        """Start the object moving again"""
        self.moving = True
        self.animation_manager.set_animation('walk', loop=True)
    
    def get_distance_to_player(self, player):
        """Calculate distance to player"""
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        return (dx * dx + dy * dy) ** 0.5
    
    def follow_player(self, player):
        """Follow the player while staying within movement region"""
        # Calculate direction to player
        dx = player.rect.centerx - self.rect.centerx
        
        # Determine movement direction
        if dx > 0:
            # Player is to the right
            self.direction = 1
            self.animation_manager.set_facing(True)  # Face right
        else:
            # Player is to the left
            self.direction = -1
            self.animation_manager.set_facing(False)  # Face left
        
        # Move towards player, but stay within region bounds
        new_x = self.current_x + (self.direction * self.follow_speed)
        
        # Clamp position to stay within movement region
        min_x = self.start_x
        max_x = self.start_x + self.movement_range
        self.current_x = max(min_x, min(max_x, new_x))
    
    def attack_player(self, player):
        """Attack the player"""
        # Attack the player
        if hasattr(player, 'take_damage'):
            player.take_damage(self.attack_damage)
            print(f"Animated object attacked player for {self.attack_damage} damage!")
        else:
            # Fallback if player doesn't have take_damage method
            if hasattr(player, 'health'):
                player.health -= self.attack_damage
                print(f"Animated object attacked player for {self.attack_damage} damage! Health: {player.health}")
        
        # Set attack cooldown
        self.attack_cooldown = self.attack_cooldown_max
    
    def take_damage(self, damage):
        """Take damage from player attacks"""
        # Check if we can take damage (not in cooldown)
        if self.take_damage_cooldown > 0 or not self.is_alive:
            return False
        
        # Take damage
        self.health -= damage
        self.take_damage_cooldown = self.take_damage_cooldown_max
        
        print(f"Animated object took {damage} damage! Health: {self.health}/{self.max_health}")
        
        # Check if dead
        if self.health <= 0:
            self.die()
            return True
        
        return True
    
    def check_platform_collision(self, level):
        """Check if standing on a platform tile and adjust movement bounds"""
        if not hasattr(level, 'is_position_on_tile_id'):
            return
        
        # Check multiple points to make platform detection more stable
        # Check center and slightly left/right to account for animation frame changes
        check_points = [
            (self.rect.centerx, self.rect.bottom + 1),  # Center
            (self.rect.centerx - 8, self.rect.bottom + 1),  # Slightly left
            (self.rect.centerx + 8, self.rect.bottom + 1),  # Slightly right
        ]
        
        on_platform = False
        for check_x, check_y in check_points:
            if (level.is_position_on_tile_id(check_x, check_y, 34) or 
                level.is_position_on_tile_id(check_x, check_y, 35) or
                level.is_position_on_tile_id(check_x, check_y, 2) or  # Also check for ground tiles (tile 2)
                level.is_position_on_tile_id(check_x, check_y, 12)):  # Also check for platform tiles (tile 12)
                on_platform = True
                break
        
        if on_platform:
            if not self.on_platform:
                # Just stepped onto platform, find platform boundaries
                current_tile_x = int(self.rect.centerx // 32)
                current_tile_y = int(self.rect.bottom // 32)
                self.find_platform_boundaries(level, current_tile_x, current_tile_y)
                self.on_platform = True
                print(f"Animated object stepped onto platform at tile ({current_tile_x}, {current_tile_y})")
        else:
            if self.on_platform:
                # Only step off platform if we're clearly not on it (add some tolerance)
                # Check if we're still within platform bounds
                if (self.platform_start_x is not None and self.platform_end_x is not None and
                    self.current_x < self.platform_start_x - 16 or 
                    self.current_x > self.platform_end_x + 16):
                    # Stepped off platform, reset to original movement
                    self.on_platform = False
                    self.platform_start_x = None
                    self.platform_end_x = None
                    print("Animated object stepped off platform, resuming original movement")
    
    def find_platform_boundaries(self, level, start_tile_x, tile_y):
        """Find the start and end of the platform tile row"""
        # Find leftmost platform tile (check tiles 34, 35, 2, and 12)
        left_x = start_tile_x
        while left_x >= 0:
            check_x = left_x * 32 + 16
            check_y = tile_y * 32 + 16
            if (level.is_position_on_tile_id(check_x, check_y, 34) or 
                level.is_position_on_tile_id(check_x, check_y, 35) or
                level.is_position_on_tile_id(check_x, check_y, 2) or  # Also check for ground tiles (tile 2)
                level.is_position_on_tile_id(check_x, check_y, 12)):  # Also check for platform tiles (tile 12)
                left_x -= 1
            else:
                break
        left_x += 1  # Adjust back to last valid tile
        
        # Find rightmost platform tile (check tiles 34, 35, 2, and 12)
        right_x = start_tile_x
        while right_x < 100:
            check_x = right_x * 32 + 16
            check_y = tile_y * 32 + 16
            if (level.is_position_on_tile_id(check_x, check_y, 34) or 
                level.is_position_on_tile_id(check_x, check_y, 35) or
                level.is_position_on_tile_id(check_x, check_y, 2) or  # Also check for ground tiles (tile 2)
                level.is_position_on_tile_id(check_x, check_y, 12)):  # Also check for platform tiles (tile 12)
                right_x += 1
            else:
                break
        right_x -= 1  # Adjust back to last valid tile
        
        # Convert to world coordinates with some padding for smoother movement
        self.platform_start_x = left_x * 32 + 8   # Slightly left of center
        self.platform_end_x = right_x * 32 + 24   # Slightly right of center
        
        print(f"Platform boundaries: {self.platform_start_x} to {self.platform_end_x}")
    
    def die(self):
        """Handle death"""
        self.is_alive = False
        self.moving = False
        self.is_attacking = False
        print("Animated object died!")
        
        # Remove from all groups
        self.kill()
    
    def get_health_percentage(self):
        """Get health as percentage (0.0 to 1.0)"""
        if self.max_health <= 0:
            return 0.0
        return max(0.0, min(1.0, self.health / self.max_health))