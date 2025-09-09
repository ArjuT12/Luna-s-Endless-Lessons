import pygame
import random
import math
from .enemy_base import BaseEnemy
from .animation import load_enemy_animations

class SlimeEnemy(BaseEnemy):
    """Slime enemy with specific behaviors and animations"""
    
    def __init__(self, x, y, waypoints=None):
        super().__init__(x, y, 'slime', waypoints)
        
        # Slime-specific properties
        self.max_health = 2  # Slimes are a bit tougher
        self.health = self.max_health
        self.speed = 2  # Slimes move slower
        self.detection_range = 120  # Shorter detection range
        
        # Make slime bigger
        self.size = 48  # Increased from 32 to 48
        self.rect = pygame.Rect(0, 0, self.size, self.size)
        self.rect.centerx = x
        self.rect.bottom = y
        
        # Attack properties
        self.attack_range = 60  # Increased range for melee attack
        self.attack_damage = 20  # Increased damage for melee
        self.attack_cooldown_time = 90  # Faster attack cooldown
        self.is_attacking = False
        self.attack_duration = 30  # Duration of attack animation
        self.attack_timer = 0  # Timer for attack duration
        
        # Animation timing
        self.attack_animation_duration = 6  # frames for attack animation
        
        # Update animation manager with bigger scale
        self.animation_manager = load_enemy_animations('slime', scale=1.5)  # 1.5x bigger
        
    def update_state(self, player, collision_sprites):
        """Override to add slime-specific state logic"""
        if not self.is_alive:
            return
            
        if self.player_in_range:
            distance = abs(self.rect.centerx - player.rect.centerx)
            
            if distance <= self.attack_range and self.attack_cooldown <= 0 and not self.is_attacking:
                self.set_state('attack')
                self.attack_player(player)
            elif not self.is_attacking:
                self.set_state('walk')
                self.move_toward_player(player, collision_sprites)
        else:
            if not self.is_attacking:
                self.set_state('walk')
                self.move_between_waypoints(collision_sprites)
    
    def set_state(self, state):
        """Set the current state and update animation"""
        self.current_state = state
        
        if state == 'attack':
            self.is_attacking = True
            self.animation_manager.set_animation('attack', loop=False)
        elif state == 'walk':
            self.animation_manager.set_animation('walk', loop=True)
        elif state == 'idle':
            self.animation_manager.set_animation('idle', loop=True)
        elif state == 'death':
            self.animation_manager.set_animation('death', loop=False)
    
    def attack_player(self, player):
        """Slime melee attack - jump towards player"""
        if self.attack_cooldown <= 0 and not self.is_attacking:
            # Set attack cooldown
            self.attack_cooldown = self.attack_cooldown_time
            self.attack_timer = 0
            
            # Face the player
            if player.rect.centerx < self.rect.centerx:
                self.facing_right = False
            else:
                self.facing_right = True
    
    def can_attack(self, player):
        """Check if slime can attack"""
        # Simple check - can attack if not on cooldown
        return self.attack_cooldown <= 0
    
    def check_height_and_climb(self, level):
        """Check for height differences and climb if needed"""
        if not self.is_alive or not level.map_loader.map_data:
            return
            
        # Get map data
        tile_width = level.map_loader.map_data.get('tilewidth', 32)
        tile_height = level.map_loader.map_data.get('tileheight', 32)
        map_width = level.map_loader.map_data.get('width', 0)
        map_height = level.map_loader.map_data.get('height', 0)
        
        if map_width == 0 or map_height == 0:
            return
            
        # Convert slime position to tile coordinates
        slime_tile_x = int(self.rect.centerx // tile_width)
        slime_tile_y = int(self.rect.bottom // tile_height)
        
        # Check if there's a solid tile in front of the slime
        direction = 1 if self.facing_right else -1
        check_tile_x = slime_tile_x + direction
        
        # Check bounds
        if check_tile_x < 0 or check_tile_x >= map_width or slime_tile_y < 0 or slime_tile_y >= map_height:
            return
            
        # Get tile data from the first layer
        if 'layers' in level.map_loader.map_data and len(level.map_loader.map_data['layers']) > 0:
            layer_data = level.map_loader.map_data['layers'][0].get('data', [])
            
            # Check for solid tiles in front of slime
            front_tile_index = slime_tile_y * map_width + check_tile_x
            if 0 <= front_tile_index < len(layer_data):
                front_tile_id = layer_data[front_tile_index]
                
                # Define solid tiles (same as in map_loader.py)
                solid_tiles = {1, 2, 3, 11, 12, 13, 21, 22, 23, 31, 61, 62, 63, 64}
                
                if front_tile_id in solid_tiles:
                    # There's a solid tile in front, try to climb up
                    if self.moving and self.current_state == 'walk':
                        # Check if there's space above the slime to climb
                        current_tile_index = slime_tile_y * map_width + slime_tile_x
                        if 0 <= current_tile_index < len(layer_data):
                            current_tile_id = layer_data[current_tile_index]
                            
                            # If current tile is solid, try to move up
                            if current_tile_id in solid_tiles:
                                # Small upward movement to climb
                                self.rect.y -= 2
                                
                                # Also try to move forward slightly to get over the obstacle
                                self.rect.x += direction * 2
    
    def move_toward_player(self, player, collision_sprites):
        """Move toward the player when in range - with Y boundary check"""
        dx = player.rect.centerx - self.rect.centerx
        horizontal_distance = abs(dx)
        
        min_distance = 80
        
        if horizontal_distance > min_distance:
            chase_speed = self.speed * 2.5
            dx = (dx / horizontal_distance) * chase_speed
            
            old_x = self.rect.centerx
            old_y = self.rect.centery
            
            self.rect.centerx += dx
            
            # Y boundary check - don't go below 545
            if self.rect.bottom > 545:
                self.rect.bottom = 545
            
            # Check collision with walls
            for sprite in collision_sprites:
                if self.rect.colliderect(sprite.rect):
                    self.rect.centerx = old_x
                    self.rect.centery = old_y
                    break
    
    def move_between_waypoints(self, collision_sprites):
        """Move between waypoints when player is not in range - with Y boundary check"""
        if not self.waypoints or len(self.waypoints) <= 1:
            return
            
        # Check if reached current waypoint
        distance_to_target = math.sqrt(
            (self.rect.centerx - self.target_waypoint[0]) ** 2 + 
            (self.rect.centery - self.target_waypoint[1]) ** 2
        )
        
        if distance_to_target < 10:  # Close enough to waypoint
            self.current_waypoint_index = (self.current_waypoint_index + 1) % len(self.waypoints)
            self.target_waypoint = self.waypoints[self.current_waypoint_index]
        
        # Move toward target waypoint
        dx = self.target_waypoint[0] - self.rect.centerx
        dy = self.target_waypoint[1] - self.rect.centery
        distance = math.sqrt(dx ** 2 + dy ** 2)
        
        if distance > 0:
            dx = (dx / distance) * self.speed
            dy = (dy / distance) * self.speed
            
            old_x = self.rect.centerx
            old_y = self.rect.centery
            
            self.rect.centerx += dx
            self.rect.centery += dy
            
            # Y boundary check - don't go below 545
            if self.rect.bottom > 545:
                self.rect.bottom = 545
            
            # Check collision with walls
            for sprite in collision_sprites:
                if self.rect.colliderect(sprite.rect):
                    self.rect.centerx = old_x
                    self.rect.centery = old_y
                    break

    def update(self, player, collision_sprites, level=None):
        """Update slime with custom logic"""
        if not self.is_alive:
            self.handle_death_state()
            return
            
        # Update cooldowns
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
            
        # Handle attack state
        if self.is_attacking:
            self.attack_timer += 1
            if self.attack_timer >= self.attack_duration:
                self.is_attacking = False
                self.set_state('idle')
                self.animation_manager.set_animation('idle', loop=True)
            
            # During attack, move towards player
            if self.player_in_range:
                dx = player.rect.centerx - self.rect.centerx
                if abs(dx) > 5:  # Only move if not too close
                    move_speed = self.speed * 1.5  # Faster during attack
                    if dx > 0:
                        self.rect.x += move_speed
                        self.facing_right = True
                    else:
                        self.rect.x -= move_speed
                        self.facing_right = False
                
                # Y boundary check - don't go below 545
                if self.rect.bottom > 545:
                    self.rect.bottom = 545
        else:
            # Check player detection
            self.check_player_detection(player)
            
            # Update state based on current situation
            self.update_state(player, collision_sprites)
            
            # Check for height differences and climb (if level is provided)
            if level:
                self.check_height_and_climb(level)
            
            # Update animation based on state
            if self.current_state == 'walk' and not self.is_attacking:
                self.animation_manager.set_animation('walk', loop=True)
            elif self.current_state == 'idle' and not self.is_attacking:
                self.animation_manager.set_animation('idle', loop=True)
        
        # Update animation
        self.animation_manager.update()
        
        # Update state timer
        self.state_timer += 1

