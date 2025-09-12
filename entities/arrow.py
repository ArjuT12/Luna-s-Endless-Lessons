import pygame
import math
from config import *

class Arrow(pygame.sprite.Sprite):
    """Arrow projectile class for bow weapon"""
    
    def __init__(self, x, y, direction, speed=6):
        super().__init__()
        
        # Arrow properties
        self.damage = 25  # Higher damage than sword
        self.speed = speed
        self.direction = direction  # 1 for right, -1 for left
        
        
        # Load arrow sprite
        self.image = pygame.image.load("Arrow01(32x32).png").convert_alpha()
        
        # Scale the arrow to appropriate size (4 times the original size)
        self.image = pygame.transform.scale(self.image, (128, 128))
        
        # Flip arrow based on direction
        if direction < 0:
            self.image = pygame.transform.flip(self.image, True, False)
        
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        
        # Physics
        self.vel_x = direction * speed
        self.vel_y = 0  # No vertical movement - arrow travels straight
        self.gravity = 0  # No gravity - arrow travels horizontally
        self.max_fall_speed = 0
        
        # Life
        self.lifetime = 600  # 10 seconds at 60fps - longer travel distance
        self.age = 0
        
        # Collision
        self.has_hit = False
        
        
    def update(self, collision_sprites, enemy_sprites):
        """Update arrow position and check collisions"""
        self.age += 1
        
        # Move arrow horizontally only (no gravity)
        self.rect.centerx += self.vel_x
        
        # Check collision with walls/terrain
        for sprite in collision_sprites:
            if self.rect.colliderect(sprite.rect):
                self.kill()
                return
        
        # Check if arrow is too old
        if self.age >= self.lifetime:
            self.kill()
            return
        
        # Check collision with enemies
        if not self.has_hit:
            for enemy in enemy_sprites:
                if hasattr(enemy, 'is_alive') and enemy.is_alive and self.rect.colliderect(enemy.rect):
                    # Deal damage to enemy
                    enemy.take_damage(self.damage)
                    self.has_hit = True
                    self.kill()
                    return
        
        # Check if arrow is out of bounds (use much larger bounds for scrolling world)
        if (self.rect.right < -1000 or self.rect.left > 5000 or 
            self.rect.bottom < -1000 or self.rect.top > 2000):
            self.kill()
    
    def draw(self, screen, camera):
        """Draw arrow on screen"""
        # Use the same camera.apply method as other entities
        screen_pos = camera.apply(self)
        
        # Draw the arrow image
        screen.blit(self.image, screen_pos)
