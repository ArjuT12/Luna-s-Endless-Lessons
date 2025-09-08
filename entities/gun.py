import pygame
from config import *

class Gun(pygame.sprite.Sprite):
    def __init__(self, frames,x_gun_offset, y_gun_offset):
        super().__init__()
        self.frames_right = frames
        self.frames_left = [pygame.transform.flip(f, True, False) for f in self.frames_right]
        
        self.current_frames = self.frames_right
        self.index = 0
        self.image = self.current_frames[0]
        self.rect = self.image.get_rect()
        self.attacking = False
        self.x_gun_offset = x_gun_offset
        self.y_gun_offset = y_gun_offset

    def start_attack(self, facing_right):
        self.attacking = True
        self.index = 0
        self.current_frames = self.frames_right if facing_right else self.frames_left
        
    def is_attacking(self):
        return self.attacking
        
    def update(self, player_rect, player_facing_right, player_attacking):
        self.current_frames = self.frames_right if player_facing_right else self.frames_left

        if player_attacking:
            self.index += 0.2
            if self.index >= len(self.current_frames):
                self.attacking = False
                self.index = 0  # Reset for next attack
        else:
            self.index = 0
            
        self.image = self.current_frames[int(self.index)]
        
        # Position the gun relative to the player
        # This offset aligns the gun with the player's hand

     
        offset_x = (25 * SCALE) - self.x_gun_offset if player_facing_right else (-25 * SCALE) + self.x_gun_offset
        offset_y = (10 * SCALE) + self.y_gun_offset
        self.rect.centerx = player_rect.centerx + offset_x
        self.rect.centery = player_rect.centery + offset_y