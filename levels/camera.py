import pygame
from config import *


class Camera:
    def __init__(self, width, height):
        # Camera shows 25 tiles at a time (25 * 32 = 800 pixels)
        self.viewport_width = 800  # 25 tiles * 32 pixels
        self.camera = pygame.Rect(0, 0, self.viewport_width, height)
        self.width = width  # Keep original width for reference
        self.height = height
        
        # Smooth camera movement
        self.target_x = 0
        self.target_y = 0
        self.camera_speed = 0.1  # Smoothing factor (0.1 = smooth, 1.0 = instant)

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def update(self, target):
        # Calculate target position
        target_x = -target.rect.centerx + int(self.viewport_width / 2)
        target_y = 0  # Keep camera at fixed vertical position
        
        # Map boundaries: 100 tiles wide = 3200 pixels
        map_width = 3200
        
        # Limit camera movement to prevent showing empty space
        # Don't scroll left past the start
        target_x = min(0, target_x)
        # Don't scroll right past the map boundary
        target_x = max(target_x, -(map_width - self.viewport_width))
        
        # Smooth camera movement using linear interpolation
        self.target_x = target_x
        self.target_y = target_y
        
        # Apply smooth movement with improved interpolation
        current_x = self.camera.x
        current_y = self.camera.y
        
        # Use a more responsive camera speed
        camera_speed = 0.15  # Slightly faster for better responsiveness
        
        # Linear interpolation for smooth movement
        new_x = current_x + (self.target_x - current_x) * camera_speed
        new_y = current_y + (self.target_y - current_y) * camera_speed
        
        self.camera = pygame.Rect(new_x, new_y, self.viewport_width, self.height)
