import pygame
import random
import math
from config import *
from .animation import load_enemy_animations

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, waypoints=None):
        super().__init__()
        
        self.size = 32
        self.image = pygame.Surface((self.size, self.size))
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        
        # Health system
        self.max_health = 1
        self.health = self.max_health
        self.is_alive = True
        
        # Respawn system
        self.respawn_timer = 0
        self.respawn_delay = 180  # 3 seconds at 60 FPS - faster respawn
        self.original_pos = (x, y)
        
        # Movement properties - faster for horde behavior
        self.speed = 3  # Faster movement
        self.waypoints = waypoints or [(x, y)]  # Default to current position if no waypoints
        self.current_waypoint_index = 0
        self.target_waypoint = self.waypoints[0]
        self.moving = True
        
        # Player detection - moderate range for following behavior
        self.detection_range = 150  # Moderate range - only follow when near
        self.player_in_range = False
        self.last_player_pos = None
        
        # Enemy color (different for each enemy)
        self.color = self.get_random_color()
        self.image.fill(self.color)  # Apply color to image
        
        # Projectile system
        self.projectiles = pygame.sprite.Group()
        self.shoot_cooldown = 0
        self.shoot_delay = 90  # frames between shots (slower shooting)
        
        # Animation
        self.animation_timer = 0
        self.animation_manager = load_enemy_animations('slime', scale=1.0)
        self.current_state = 'idle'
        self.facing_right = True
        
    def update(self, player, collision_sprites):
        if not self.is_alive:
            # Handle respawn timer
            self.respawn_timer += 1
            if self.respawn_timer >= self.respawn_delay:
                self.respawn(player)  # Pass player for horde respawn
            return
            
        # Update shoot cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
            
        # Check if player is in range - only follow when player is 50px below enemy foot level
        player_foot_level = player.rect.bottom  # Player's foot level
        enemy_foot_level = self.rect.bottom     # Enemy's foot level
        
        # Calculate horizontal distance
        horizontal_distance = abs(self.rect.centerx - player.rect.centerx)
        
        # Check if player is within detection range horizontally AND 50px below enemy
        self.player_in_range = (horizontal_distance <= self.detection_range and 
                               player_foot_level >= enemy_foot_level - 50)
        
        if self.player_in_range:
            # Face player, move toward player, and shoot
            self.last_player_pos = (player.rect.centerx, player.rect.centery)
            self.face_player(player)
            self.move_toward_player(player, collision_sprites)
            self.shoot_at_player(player)
            self.moving = True
        else:
            # Move between waypoints when player is not in range
            self.moving = True
            self.move_between_waypoints(collision_sprites)
        
        # Update projectiles
        self.projectiles.update(collision_sprites)
        
        # Update animation
        self.animation_timer += 1
        self.update_animation_state()
        self.animation_manager.update()
        
    def update_animation_state(self):
        """Update animation based on current state"""
        if not self.is_alive:
            self.animation_manager.set_animation('death', loop=False)
        elif self.player_in_range:
            if self.shoot_cooldown <= 0:
                self.animation_manager.set_animation('attack', loop=False)
            else:
                self.animation_manager.set_animation('walk', loop=True)
        else:
            self.animation_manager.set_animation('walk', loop=True)
    
    def face_player(self, player):
        """Make enemy face the player"""
        if player.rect.centerx < self.rect.centerx:
            # Player is to the left
            self.facing_right = False
        else:
            # Player is to the right
            self.facing_right = True
        
        self.animation_manager.set_facing(self.facing_right)
    
    def move_toward_player(self, player, collision_sprites):
        """Move toward the player when in range - only horizontally, keep at ground level"""
        # Calculate horizontal direction to player only
        dx = player.rect.centerx - self.rect.centerx
        horizontal_distance = abs(dx)
        
        # Maintain a small distance from player for visibility
        min_distance = 80  # Keep at least 80 pixels away for better visibility
        
        if horizontal_distance > min_distance:
            # Only move horizontally, keep enemy at ground level
            chase_speed = self.speed * 2.5  # Much faster chasing
            dx = (dx / horizontal_distance) * chase_speed
            
            # Check for collisions before moving
            old_x = self.rect.centerx
            old_y = self.rect.centery
            
            # Only move horizontally
            self.rect.centerx += dx
            # Keep enemy at ground level (don't change Y position)
            
            # Check collision with walls
            for sprite in collision_sprites:
                if self.rect.colliderect(sprite.rect):
                    # Revert movement if collision detected
                    self.rect.centerx = old_x
                    self.rect.centery = old_y
                    break
    
    def move_between_waypoints(self, collision_sprites):
        """Move between waypoints in a random order"""
        if not self.waypoints or len(self.waypoints) <= 1:
            return
            
        # Check if reached current waypoint
        distance_to_target = math.sqrt(
            (self.rect.centerx - self.target_waypoint[0]) ** 2 + 
            (self.rect.centery - self.target_waypoint[1]) ** 2
        )
        
        if distance_to_target < 5:  # Close enough to waypoint
            # Choose next waypoint randomly
            available_waypoints = [wp for wp in self.waypoints if wp != self.target_waypoint]
            if available_waypoints:
                self.target_waypoint = random.choice(available_waypoints)
        
        # Move towards target waypoint
        dx = self.target_waypoint[0] - self.rect.centerx
        dy = self.target_waypoint[1] - self.rect.centery
        distance = math.sqrt(dx ** 2 + dy ** 2)
        
        if distance > 0:
            # Normalize direction and apply speed
            dx = (dx / distance) * self.speed
            dy = (dy / distance) * self.speed
            
            # Check for collisions before moving
            old_x = self.rect.centerx
            old_y = self.rect.centery
            
            self.rect.centerx += dx
            self.rect.centery += dy
            
            # Check collision with walls
            for sprite in collision_sprites:
                if self.rect.colliderect(sprite.rect):
                    # Revert movement if collision detected
                    self.rect.centerx = old_x
                    self.rect.centery = old_y
                    break
    
    def shoot_at_player(self, player):
        """Shoot projectile at player"""
        if self.shoot_cooldown <= 0 and self.last_player_pos:
            # Calculate direction to player
            dx = self.last_player_pos[0] - self.rect.centerx
            dy = self.last_player_pos[1] - self.rect.centery
            distance = math.sqrt(dx ** 2 + dy ** 2)
            
            if distance > 0:
                # Normalize direction
                dx = dx / distance
                dy = dy / distance
                
                # Create projectile
                projectile = Projectile(
                    self.rect.centerx, 
                    self.rect.centery, 
                    dx, 
                    dy
                )
                self.projectiles.add(projectile)
                self.shoot_cooldown = self.shoot_delay
    
    def take_damage(self, damage):
        """Take damage and check if enemy dies"""
        self.health -= damage
        if self.health <= 0:
            self.is_alive = False
            self.respawn_timer = 0  # Start respawn timer
            # Don't kill the enemy permanently, just make it inactive
            # self.kill()  # Commented out to prevent permanent removal
            return True  # Enemy died
        return False  # Enemy still alive
    
    def respawn(self, player=None):
        """Respawn the enemy close to the player for horde behavior"""
        self.is_alive = True
        self.health = self.max_health
        self.respawn_timer = 0
        
        if player:
            # Respawn close to player for horde behavior
            # Spawn at a random position near the player at ground level
            import random
            offset_x = random.randint(-200, 200)
            self.rect.centerx = player.rect.centerx + offset_x
            self.rect.bottom = player.rect.bottom - 30  # Keep at same ground level as player minus 30px
        else:
            # Fallback to original position
            self.rect.centerx = self.original_pos[0]
            self.rect.bottom = self.original_pos[1]  # Use bottom for ground level
        
        # Reset waypoint to current position
        self.target_waypoint = (self.rect.centerx, self.rect.bottom)
        
        # Reset animation
        self.animation_manager.set_animation('idle', loop=True)
        self.facing_right = True
    
    def get_random_color(self):
        """Get a random color for the enemy"""
        colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Cyan
            (255, 128, 0),  # Orange
            (128, 0, 255),  # Purple
        ]
        return random.choice(colors)
    
    def draw_health_bar(self, screen, screen_pos):
        """Draw health bar above enemy"""
        # Always show health bar for enemies
        # Calculate screen position
        screen_x = screen_pos[0]
        screen_y = screen_pos[1] - 15
        
        # Draw health bar background (red)
        bar_width = self.size + 10
        bar_height = 6
        pygame.draw.rect(screen, (255, 0, 0), (screen_x - 5, screen_y, bar_width, bar_height))
        
        # Draw health bar (green)
        health_width = (self.health / self.max_health) * bar_width
        pygame.draw.rect(screen, (0, 255, 0), (screen_x - 5, screen_y, health_width, bar_height))
        
        # Draw border
        pygame.draw.rect(screen, (255, 255, 255), (screen_x - 5, screen_y, bar_width, bar_height), 1)
    
    def draw(self, screen, screen_pos):
        """Draw enemy with animation"""
        if self.is_alive or not self.is_alive:  # Draw even when dead for death animation
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


class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, dx, dy):
        super().__init__()
        
        self.size = 12  # Larger projectile
        self.damage = 20  # Damage to player
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)  # Transparent background
        # Draw bright yellow circle with border
        pygame.draw.circle(self.image, (255, 255, 0), (self.size//2, self.size//2), self.size//2)
        pygame.draw.circle(self.image, (255, 255, 255), (self.size//2, self.size//2), self.size//2, 2)  # White border
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        
        # Movement
        self.speed = 3
        self.dx = dx * self.speed
        self.dy = dy * self.speed
        
        # Life
        self.lifetime = 180  # frames before projectile disappears
        self.age = 0
        
        # Particles
        self.particles = []
        
    def update(self, collision_sprites):
        self.age += 1
        
        # Move projectile
        self.rect.centerx += self.dx
        self.rect.centery += self.dy
        
        # Check collision with walls
        for sprite in collision_sprites:
            if self.rect.colliderect(sprite.rect):
                self.create_particles()
                self.kill()
                return
        
        # Check if projectile is too old
        if self.age >= self.lifetime:
            self.kill()
        
        # Update particles
        for particle in self.particles[:]:
            particle.update()
            if particle.lifetime <= 0:
                self.particles.remove(particle)
    
    def create_particles(self):
        """Create particle effect when projectile hits something"""
        for _ in range(5):
            particle = Particle(self.rect.centerx, self.rect.centery)
            self.particles.append(particle)
    
    def draw(self, screen, screen_pos):
        # Draw projectile at screen position
        screen.blit(self.image, screen_pos)
        
        # Draw particles
        for particle in self.particles:
            particle.draw(screen, screen_pos)


class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.dx = random.uniform(-4, 4)
        self.dy = random.uniform(-4, 4)
        self.lifetime = 60
        self.max_lifetime = 60
        self.size = random.randint(4, 8)  # Much bigger and more visible particles
        self.color = (255, 255, 0)  # Bright yellow
    
    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.lifetime -= 1
        
        # Fade out
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        self.color = (255, 255, 0, alpha)
    
    def draw(self, screen, screen_pos):
        # Draw particle at screen position
        screen_x = int(screen_pos[0])
        screen_y = int(screen_pos[1])
        
        # Draw particle as a small circle
        pygame.draw.circle(screen, self.color[:3], (screen_x, screen_y), self.size)
