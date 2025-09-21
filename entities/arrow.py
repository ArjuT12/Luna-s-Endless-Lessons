import pygame
import math
from config import *

class Arrow(pygame.sprite.Sprite):
    """Arrow projectile class for bow weapon"""
    
    def __init__(self, x, y, direction, speed=12, damage_multiplier=1.0):
        super().__init__()
        
        # Arrow properties
        base_damage = 25  # Higher damage than sword
        self.damage = int(base_damage * damage_multiplier)  # Apply multiplier
        self.speed = speed
        self.direction = direction  # 1 for right, -1 for left
        
        
        # Load arrow sprite
        self.image = pygame.image.load("Arrow01(32x32).png").convert_alpha()
        
        # Scale the arrow to appropriate size (3x larger)
        self.image = pygame.transform.scale(self.image, (96, 96))
        
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
        
        
    def update(self, collision_sprites, enemy_sprites, animated_objects=None):
        """Update arrow position and check collisions"""
        self.age += 1
        
        # Move arrow horizontally only (no gravity)
        self.rect.centerx += self.vel_x
        
        # Check collision with walls/terrain (with more leeway)
        # for sprite in collision_sprites:
        #     if self.rect.colliderect(sprite.rect):
        #         # Give more leeway - only kill if arrow is significantly overlapping
        #         overlap = self.rect.clip(sprite.rect)
        #         if overlap.width > 30 or overlap.height > 30:  # Only kill if overlap is substantial (increased leeway)
        #             self.kill()
        #             return
        
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
                    print(f"Arrow hit enemy for {self.damage} damage!")
                    self.has_hit = True
                    self.kill()
                    return
        
        # Check collision with animated objects
        if not self.has_hit and animated_objects:
            for animated_obj in animated_objects:
                if hasattr(animated_obj, 'is_alive') and animated_obj.is_alive and self.rect.colliderect(animated_obj.rect):
                    # Deal damage to animated object
                    if animated_obj.take_damage(self.damage):
                        print(f"Arrow killed animated object for {self.damage} damage!")
                    else:
                        print(f"Arrow hit animated object for {self.damage} damage! Health: {animated_obj.health}/{animated_obj.max_health}")
                    self.has_hit = True
                    self.kill()
                    return
        
        # Check if arrow is out of bounds (use much larger world bounds)
        if (self.rect.right < -1000 or self.rect.left > 10000 or 
            self.rect.bottom < -1000 or self.rect.top > 10000):
            self.kill()
    
    def draw(self, screen, camera):
        """Draw arrow on screen"""
        screen_pos = self.rect.copy()
        screen_pos.x -= camera.camera.x
        screen_pos.y -= camera.camera.y
        
        # Draw the arrow image
        screen.blit(self.image, screen_pos)