import pygame
from config import *


class Camera:
    def __init__(self, width, height):
        self.viewport_width = 800
        self.camera = pygame.Rect(0, 0, self.viewport_width, height)
        self.width = width
        self.height = height
        
        self.target_x = 0
        self.target_y = 0
        self.camera_speed = 0.1

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)
    
    def apply_pos(self, pos):
        return (pos[0] + self.camera.x, pos[1] + self.camera.y)

    def update(self, target):
        target_x = -target.rect.centerx + int(self.viewport_width / 2)
        target_y = 0
        
        map_width = 3200
        
        target_x = min(0, target_x)
        target_x = max(target_x, -(map_width - self.viewport_width))
        
        self.target_x = target_x
        self.target_y = target_y
        
        current_x = self.camera.x
        current_y = self.camera.y
        
        camera_speed = 0.15
        new_x = current_x + (self.target_x - current_x) * camera_speed
        new_y = current_y + (self.target_y - current_y) * camera_speed
        
        self.camera = pygame.Rect(new_x, new_y, self.viewport_width, self.height)
