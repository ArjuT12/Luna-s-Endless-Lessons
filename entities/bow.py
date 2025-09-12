import pygame
from config import *
from .arrow import Arrow

class Bow(pygame.sprite.Sprite):
    """Bow weapon class for ranged attacks"""
    
    def __init__(self, frames, x_bow_offset, y_bow_offset):
        super().__init__()
        self.frames_right = frames if frames else self.create_default_frames()
        self.frames_left = [pygame.transform.flip(f, True, False) for f in self.frames_right]
        
        self.current_frames = self.frames_right
        self.index = 0
        self.image = self.current_frames[0]
        self.rect = self.image.get_rect()
        self.attacking = False
        self.x_bow_offset = x_bow_offset
        self.y_bow_offset = y_bow_offset
        
        # Bow properties
        self.shoot_cooldown = 0
        self.shoot_delay = 30  # Faster than gun, slower than sword
        self.arrows = pygame.sprite.Group()
    
    def create_default_frames(self):
        """Create default bow frames when no sprites are provided"""
        frames = []
        for i in range(3):  # Create 3 simple frames
            # Create a simple bow image
            frame = pygame.Surface((32, 16), pygame.SRCALPHA)
            # Draw a simple bow shape
            pygame.draw.arc(frame, (139, 69, 19), (0, 0, 32, 16), 0, 3.14, 3)  # Brown bow curve
            pygame.draw.line(frame, (139, 69, 19), (16, 8), (16, 12), 2)  # Bow handle
            frames.append(frame)
        return frames
        
    def start_attack(self, facing_right):
        """Start bow attack animation and shooting"""
        if self.shoot_cooldown <= 0:
            self.attacking = True
            self.index = 0
            self.current_frames = self.frames_right if facing_right else self.frames_left
            self.shoot_cooldown = self.shoot_delay
    
    def shoot_arrow(self, player_rect, player_facing_right):
        """Create and shoot an arrow"""
        if self.shoot_cooldown <= 0:
            # Calculate arrow spawn position (at player center)
            direction = 1 if player_facing_right else -1
            arrow_x = player_rect.centerx  # Start from player center
            arrow_y = player_rect.centery  # Start from player center
            
            # Create arrow
            arrow = Arrow(arrow_x, arrow_y, direction)
            self.arrows.add(arrow)
            self.shoot_cooldown = self.shoot_delay
            return arrow
        return None
    
    def is_attacking(self):
        return self.attacking
        
    def update(self, player_rect, player_facing_right, player_attacking):
        """Update bow animation and cooldown"""
        self.current_frames = self.frames_right if player_facing_right else self.frames_left
        
        # Update shoot cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        
        if player_attacking and self.shoot_cooldown <= 0:
            self.index += 0.3  # Faster animation than gun
            if self.index >= len(self.current_frames):
                self.attacking = False
                self.index = 0
        else:
            self.index = 0
            
        self.image = self.current_frames[int(self.index)]
        
        # Position the bow relative to the player
        offset_x = (25 * SCALE) - self.x_bow_offset if player_facing_right else (-25 * SCALE) + self.x_bow_offset
        offset_y = (10 * SCALE) + self.y_bow_offset
        self.rect.centerx = player_rect.centerx + offset_x
        self.rect.centery = player_rect.centery + offset_y
        
        # Update arrows
        self.arrows.update([], [])  # Will be updated properly in level
    
    def update_arrows(self, collision_sprites, enemy_sprites):
        """Update all arrows and check collisions"""
        self.arrows.update(collision_sprites, enemy_sprites)
        
        # Remove dead arrows
        for arrow in self.arrows.copy():
            if not arrow.alive():
                self.arrows.remove(arrow)
    
    def draw_arrows(self, screen, camera):
        """Draw all arrows"""
        for arrow in self.arrows:
            arrow.draw(screen, camera)
    
    def get_arrows(self):
        """Get all active arrows for collision detection"""
        return self.arrows
