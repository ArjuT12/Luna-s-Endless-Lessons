import pygame
import random
import math
from config import *
from .animation import load_enemy_animations

class BaseEnemy(pygame.sprite.Sprite):
    """Base class for all enemies with common functionality"""
    
    def __init__(self, x, y, enemy_type, waypoints=None):
        super().__init__()
        
        # Basic enemy properties
        self.enemy_type = enemy_type
        self.size = 32
        self.rect = pygame.Rect(0, 0, self.size, self.size)
        self.rect.centerx = x
        self.rect.bottom = y
        
        # Health system
        self.max_health = 1
        self.health = self.max_health
        self.is_alive = True
        
        # Respawn system
        self.respawn_timer = 0
        self.respawn_delay = 180
        self.original_pos = (x, y)
        
        # Movement properties
        self.speed = 3
        self.waypoints = waypoints or [(x, y)]
        self.current_waypoint_index = 0
        self.target_waypoint = self.waypoints[0]
        self.moving = True
        
        # Player detection
        self.detection_range = 150
        self.player_in_range = False
        self.last_player_pos = None
        
        # Animation system
        self.animation_manager = load_enemy_animations(enemy_type, scale=1.0)
        self.current_state = 'idle'
        self.facing_right = True
        
        # Projectile system
        self.projectiles = pygame.sprite.Group()
        self.shoot_cooldown = 0
        self.shoot_delay = 90
        
        # Animation timer
        self.animation_timer = 0
        
        # State management
        self.state_timer = 0
        self.attack_cooldown = 0
        
    def update(self, player, collision_sprites):
        """Update enemy logic"""
        if not self.is_alive:
            self.handle_death_state()
            return
            
        # Update cooldowns
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
            
        # Check player detection
        self.check_player_detection(player)
        
        # Update state based on current situation
        self.update_state(player, collision_sprites)
        
        # Update animation
        self.animation_manager.update()
        
        # Update projectiles
        self.projectiles.update(collision_sprites)
        
        # Update state timer
        self.state_timer += 1
        
    def handle_death_state(self):
        """Handle death animation and respawn"""
        self.animation_manager.set_animation('death', loop=False)
        self.animation_manager.update()
        
        # Handle respawn timer
        self.respawn_timer += 1
        if self.respawn_timer >= self.respawn_delay:
            self.respawn()
    
    def check_player_detection(self, player):
        """Check if player is in detection range"""
        player_foot_level = player.rect.bottom
        enemy_foot_level = self.rect.bottom
        
        horizontal_distance = abs(self.rect.centerx - player.rect.centerx)
        
        self.player_in_range = (horizontal_distance <= self.detection_range and 
                               player_foot_level >= enemy_foot_level - 50)
        
        if self.player_in_range:
            self.last_player_pos = (player.rect.centerx, player.rect.centery)
            # Update facing direction
            self.facing_right = player.rect.centerx > self.rect.centerx
            self.animation_manager.set_facing(self.facing_right)
    
    def update_state(self, player, collision_sprites):
        """Update enemy state based on current situation"""
        if self.player_in_range:
            if self.attack_cooldown <= 0 and self.can_attack(player):
                self.set_state('attack')
            else:
                self.set_state('walk')
                self.move_toward_player(player, collision_sprites)
        else:
            self.set_state('walk')
            self.move_between_waypoints(collision_sprites)
    
    def set_state(self, new_state):
        """Set the current state and animation"""
        if new_state != self.current_state:
            self.current_state = new_state
            self.state_timer = 0
            
            # Set appropriate animation
            if new_state == 'attack':
                self.animation_manager.set_animation('attack', loop=False)
            elif new_state == 'walk':
                self.animation_manager.set_animation('walk', loop=True)
            else:
                self.animation_manager.set_animation('idle', loop=True)
    
    def can_attack(self, player):
        """Check if enemy can attack the player"""
        if not self.player_in_range:
            return False
        
        # Check if close enough to attack
        distance = abs(self.rect.centerx - player.rect.centerx)
        return distance <= 60  # Attack range
    
    def move_toward_player(self, player, collision_sprites):
        """Move toward the player when in range"""
        dx = player.rect.centerx - self.rect.centerx
        horizontal_distance = abs(dx)
        
        min_distance = 80
        
        if horizontal_distance > min_distance:
            chase_speed = self.speed * 2.5
            dx = (dx / horizontal_distance) * chase_speed
            
            old_x = self.rect.centerx
            old_y = self.rect.centery
            
            self.rect.centerx += dx
            
            # Check collision with walls
            for sprite in collision_sprites:
                if self.rect.colliderect(sprite.rect):
                    self.rect.centerx = old_x
                    self.rect.centery = old_y
                    break
    
    def move_between_waypoints(self, collision_sprites):
        """Move between waypoints when player is not in range"""
        if not self.waypoints or len(self.waypoints) <= 1:
            return
            
        # Check if reached current waypoint
        distance_to_target = math.sqrt(
            (self.rect.centerx - self.target_waypoint[0]) ** 2 + 
            (self.rect.centery - self.target_waypoint[1]) ** 2
        )
        
        if distance_to_target < 5:
            available_waypoints = [wp for wp in self.waypoints if wp != self.target_waypoint]
            if available_waypoints:
                self.target_waypoint = random.choice(available_waypoints)
        
        # Move towards target waypoint
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
            
            # Update facing direction based on movement
            if dx > 0:
                self.facing_right = True
            elif dx < 0:
                self.facing_right = False
            self.animation_manager.set_facing(self.facing_right)
            
            # Check collision with walls
            for sprite in collision_sprites:
                if self.rect.colliderect(sprite.rect):
                    self.rect.centerx = old_x
                    self.rect.centery = old_y
                    break
    
    def attack_player(self, player):
        """Attack the player - to be overridden by specific enemy types"""
        pass
    
    def take_damage(self, damage):
        """Take damage and check if enemy dies"""
        self.health -= damage
        if self.health <= 0:
            self.is_alive = False
            self.respawn_timer = 0
            return True
        return False
    
    def respawn(self, player=None):
        """Respawn the enemy"""
        self.is_alive = True
        self.health = self.max_health
        self.respawn_timer = 0
        self.current_state = 'idle'
        self.animation_manager.set_animation('idle', loop=True)
        
        if player:
            offset_x = random.randint(-200, 200)
            self.rect.centerx = player.rect.centerx + offset_x
            self.rect.bottom = player.rect.bottom - 30
        else:
            self.rect.centerx = self.original_pos[0]
            self.rect.bottom = self.original_pos[1]
        
        self.target_waypoint = (self.rect.centerx, self.rect.bottom)
    
    def draw_health_bar(self, screen, screen_pos):
        """Draw health bar above enemy"""
        screen_x = screen_pos[0]
        screen_y = screen_pos[1] - 15
        
        bar_width = self.size + 10
        bar_height = 6
        pygame.draw.rect(screen, (255, 0, 0), (screen_x - 5, screen_y, bar_width, bar_height))
        
        health_width = (self.health / self.max_health) * bar_width
        pygame.draw.rect(screen, (0, 255, 0), (screen_x - 5, screen_y, health_width, bar_height))
        
        pygame.draw.rect(screen, (255, 255, 255), (screen_x - 5, screen_y, bar_width, bar_height), 1)
    
    def draw(self, screen, screen_pos):
        """Draw enemy with current animation frame"""
        if self.is_alive or self.current_state == 'death':
            # Get current animation frame
            frame = self.animation_manager.get_current_frame()
            if frame:
                # Center the frame on the enemy position
                frame_rect = frame.get_rect()
                frame_rect.centerx = screen_pos[0] + self.size // 2
                frame_rect.bottom = screen_pos[1] + self.size
                
                screen.blit(frame, frame_rect)
            
            # Draw health bar if alive
            if self.is_alive:
                self.draw_health_bar(screen, screen_pos)
