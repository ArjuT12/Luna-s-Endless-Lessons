import pygame
import json
import os
from config import *


class Heart(pygame.sprite.Sprite):
    def __init__(self, x, y, groups=None):
        super().__init__(groups)
        
        # Load the heart animation data
        self.animation_data = self.load_animation_data()
        
        # Load the heart image
        self.image = pygame.image.load('hearts_full.png').convert_alpha()
        
        # Set up animation
        self.setup_animation()
        
        # Set position and rect
        self.rect = pygame.Rect(x, y, 20, 20)  # Each heart slice is 20x20
        
        # Create a much smaller collision area for precise collection
        self.collision_rect = pygame.Rect(x + 8, y + 8, 4, 4)  # Very small collision area in center
        
        # Animation state
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 0.1  # Slower animation for hearts
        
        # Heart properties
        self.collected = False
        self.heal_amount = 50  # How much health this heart restores
        
    def load_animation_data(self):
        """Load animation data from hearts1.json"""
        try:
            with open('hearts1.json', 'r') as f:
                data = json.load(f)
            return data
        except FileNotFoundError:
            print("hearts1.json not found, using default animation")
            return None
        except json.JSONDecodeError:
            print("Invalid JSON in hearts1.json")
            return None
    
    def setup_animation(self):
        """Set up animation frames from the loaded data"""
        if not self.animation_data or 'slices' not in self.animation_data['meta']:
            # Fallback: create a simple animation with 4 frames
            self.frames = []
            for i in range(4):
                frame_rect = pygame.Rect(i * 20, 0, 20, 20)
                frame_surface = pygame.Surface((20, 20), pygame.SRCALPHA)
                frame_surface.blit(self.image, (0, 0), frame_rect)
                self.frames.append(frame_surface)
        else:
            # Use the slices from the JSON data
            self.frames = []
            slices = self.animation_data['meta']['slices']
            
            for slice_data in slices:
                bounds = slice_data['keys'][0]['bounds']
                frame_rect = pygame.Rect(bounds['x'], bounds['y'], bounds['w'], bounds['h'])
                frame_surface = pygame.Surface((bounds['w'], bounds['h']), pygame.SRCALPHA)
                frame_surface.blit(self.image, (0, 0), frame_rect)
                self.frames.append(frame_surface)
        
        # Set the initial frame
        if self.frames:
            self.image = self.frames[0]
    
    def update(self, player):
        """Update heart animation and check for collection"""
        if self.collected:
            return
        
        # Update animation
        self.animation_timer += self.animation_speed
        if self.animation_timer >= 1.0:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = self.frames[self.current_frame]
        
        # Update collision rect position to match heart position
        self.collision_rect.centerx = self.rect.centerx
        self.collision_rect.centery = self.rect.centery
        
        # Check if player collected the heart using precise collision detection
        # Player must be standing on top of the heart (more precise)
        if (hasattr(player, 'collision_rect') and 
            self.collision_rect.colliderect(player.collision_rect) and
            player.rect.bottom <= self.rect.bottom + 5):  # Player must be on top
            self.collect(player)
    
    def collect(self, player):
        """Collect the heart and add to inventory"""
        if not self.collected:
            # Check if player can use hearts (unlocked through story progression)
            if hasattr(player, 'can_use_hearts') and not player.can_use_hearts:
                print("Hearts not yet unlocked! Cannot collect heart.")
                return
                
            # Add heart to player's inventory instead of directly healing
            if hasattr(player, 'inventory'):
                if player.inventory.add_item('heart', 1):
                    self.collected = True
                    self.kill()  # Remove from all groups
                    print(f"Heart collected! Hearts in inventory: {player.inventory.get_item_quantity('heart')}")
                    # Save inventory after collecting heart
                    if hasattr(player, 'save_inventory'):
                        player.save_inventory()
                else:
                    print("Inventory is full! Cannot collect heart.")
            else:
                # Fallback to old behavior if no inventory system
                if player.health < player.max_health:
                    player.health = min(player.max_health, player.health + self.heal_amount)
                    self.collected = True
                    self.kill()  # Remove from all groups
                    print(f"Heart collected! Player health: {player.health}/{player.max_health}")
    
    def draw(self, surface, camera_offset):
        """Draw the heart with camera offset"""
        if not self.collected:
            surface.blit(self.image, camera_offset)
            
            # Debug: Draw collision area (uncomment for testing)
            # pygame.draw.rect(surface, (255, 0, 0), 
            #                 (self.collision_rect.x - camera_offset[0], 
            #                  self.collision_rect.y - camera_offset[1], 
            #                  self.collision_rect.width, 
            #                  self.collision_rect.height), 1)
