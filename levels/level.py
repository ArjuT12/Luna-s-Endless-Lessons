import pygame
from config import *
from entities.player import Player
from levels.tile import Tile
from levels.camera import Camera
from levels.map_loader import MapLoader



class Level:
    def __init__(self):
        
        #Level setup
        self.display_surface = pygame.display.get_surface()

        #sprite Group 
        self.visible_sprite = pygame.sprite.Group()
        self.active_sprite = pygame.sprite.Group()
        self.collision_sprite = pygame.sprite.Group()
        self.enemy_sprite = pygame.sprite.Group()  # Group for enemy tiles
        
        # Camera system
        self.camera = Camera(WIDTH, HEIGHT)
        
        # Map loader
        self.map_loader = MapLoader()
        self.map_tiles = []
        
        # Interaction system
        self.interactive_tiles = []
        self.nearby_interactive = None
        self.show_interaction_prompt = False
        self.dialogue_active = False
        self.current_dialogue = None
        self.dialogue_index = 0
        
        # Key state tracking for dialogue
        self.z_pressed = False
        self.enter_pressed = False
        self.q_pressed = False
        
        # Test dialogues
        self.dialogues = {
            102: [
                "Hello there, traveler!",
                "Welcome to our village.",
                "I hope you're enjoying your journey.",
                "Be careful out there - the forest can be dangerous!",
                "Safe travels, friend!"
            ]
        }

        self.setup_level()

    def setup_level(self):
        # Load map data
        self.load_map()
        
        # Create player at the specified starting position
        # Map is 100x20 tiles, bottom 3 rows are floor (96 pixels from bottom)
        # Player feet should start at 97 pixels from bottom, so bottom = 640 - 97 = 543
        # Position player at X: 32, Y: 543
        self.player = Player()
        self.player.rect.centerx = 32  # Starting position X: 32
        self.player.rect.bottom = 543  # Player feet at 97 pixels from bottom (640 - 97 = 543)
        self.player.on_ground = True  # Ensure player starts on ground
        self.player.vel_y = 0  # Ensure player starts with zero velocity
    
    def load_map(self):
        """Load the forest map using the map loader"""
        # Load map data (this will also load all referenced tilesets)
        if self.map_loader.load_map('forest2.json'):
            print("Map loaded successfully")
            
            # Create tiles from map data
            self.map_tiles = self.map_loader.create_tiles_from_map([self.collision_sprite, self.enemy_sprite])
            
            # Collect interactive tiles
            self.interactive_tiles = [tile for tile in self.map_tiles if hasattr(tile, 'is_interactive') and tile.is_interactive]
            print(f"Created {len(self.map_tiles)} map tiles")
            print(f"Found {len(self.interactive_tiles)} interactive tiles")
        else:
            print("Failed to load map data")

    def check_interactions(self, keys):
        """Check if player is near interactive tiles and handle interactions"""
        # Check if player is near any interactive tile
        self.nearby_interactive = None
        interaction_distance = 50  # Distance in pixels to trigger interaction
        
        for tile in self.interactive_tiles:
            distance = ((self.player.rect.centerx - tile.rect.centerx) ** 2 + 
                       (self.player.rect.centery - tile.rect.centery) ** 2) ** 0.5
            if distance <= interaction_distance:
                self.nearby_interactive = tile
                break
        
        # Show interaction prompt if near interactive tile
        self.show_interaction_prompt = self.nearby_interactive is not None and not self.dialogue_active
        
        # Handle interaction input (Q key)
        if keys[pygame.K_q] and not self.q_pressed and self.nearby_interactive and not self.dialogue_active:
            self.start_dialogue(self.nearby_interactive.tile_id)
            self.q_pressed = True
        elif not keys[pygame.K_q]:
            self.q_pressed = False
        
        # Handle dialogue navigation
        if self.dialogue_active:
            # Z key for continuing dialogue
            if keys[pygame.K_z] and not self.z_pressed:
                self.next_dialogue()
                self.z_pressed = True
            elif not keys[pygame.K_z]:
                self.z_pressed = False
            
            # ENTER key for continuing dialogue
            if keys[pygame.K_RETURN] and not self.enter_pressed:
                self.next_dialogue()
                self.enter_pressed = True
            elif not keys[pygame.K_RETURN]:
                self.enter_pressed = False
            
            # ESC key for exiting dialogue
            if keys[pygame.K_ESCAPE]:
                self.end_dialogue()
    
    def start_dialogue(self, tile_id):
        """Start dialogue for the given tile ID"""
        if tile_id in self.dialogues:
            self.current_dialogue = self.dialogues[tile_id]
            self.dialogue_index = 0
            self.dialogue_active = True
            self.show_interaction_prompt = False
    
    def next_dialogue(self):
        """Move to next dialogue line"""
        if self.dialogue_active and self.current_dialogue:
            self.dialogue_index += 1
            if self.dialogue_index >= len(self.current_dialogue):
                self.end_dialogue()
    
    def end_dialogue(self):
        """End current dialogue"""
        self.dialogue_active = False
        self.current_dialogue = None
        self.dialogue_index = 0
    
    def draw_ui(self):
        """Draw interaction prompts and dialogue"""
        font = pygame.font.Font(None, 36)
        
        # Draw interaction prompt
        if self.show_interaction_prompt:
            prompt_text = font.render("Press Q to interact", True, (255, 255, 255))
            prompt_rect = prompt_text.get_rect(center=(WIDTH // 2, HEIGHT - 100))
            
            # Draw background for prompt
            bg_rect = prompt_rect.inflate(20, 10)
            pygame.draw.rect(self.display_surface, (0, 0, 0, 150), bg_rect)
            pygame.draw.rect(self.display_surface, (255, 255, 255), bg_rect, 2)
            
            self.display_surface.blit(prompt_text, prompt_rect)
        
        # Draw dialogue
        if self.dialogue_active and self.current_dialogue:
            dialogue_text = self.current_dialogue[self.dialogue_index]
            
            # Create dialogue box
            dialogue_rect = pygame.Rect(50, HEIGHT - 200, WIDTH - 100, 150)
            pygame.draw.rect(self.display_surface, (0, 0, 0, 200), dialogue_rect)
            pygame.draw.rect(self.display_surface, (255, 255, 255), dialogue_rect, 3)
            
            # Draw dialogue text (wrapped)
            words = dialogue_text.split()
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                if font.size(test_line)[0] < dialogue_rect.width - 20:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
            
            # Draw each line
            y_offset = dialogue_rect.y + 20
            for line in lines[:3]:  # Max 3 lines
                text_surface = font.render(line, True, (255, 255, 255))
                text_rect = text_surface.get_rect(centerx=dialogue_rect.centerx, y=y_offset)
                self.display_surface.blit(text_surface, text_rect)
                y_offset += 30
            
            # Draw continue prompt
            continue_text = font.render("Press Z or ENTER to continue or ESC to exit", True, (200, 200, 200))
            continue_rect = continue_text.get_rect(centerx=dialogue_rect.centerx, y=dialogue_rect.bottom - 30)
            self.display_surface.blit(continue_text, continue_rect)

    def run(self, keys, collision_sprites):
        #run whole game(level)
        # Update player with proper arguments
        self.player.update(keys, collision_sprites, self.enemy_sprite)
        
        # Check interactions
        self.check_interactions(keys)
        
        # Update camera to follow player
        self.camera.update(self.player)
        
        # Clear the screen - let background layers provide the sky color
        # self.display_surface.fill((135, 206, 235))  # Sky blue background
        
        # Draw map tiles first (only those visible in camera viewport)
        for tile in self.map_tiles:
            screen_pos = self.camera.apply(tile)
            # Only draw tiles that are within the camera viewport
            if (screen_pos.x > -32 and screen_pos.x < self.camera.viewport_width and 
                screen_pos.y > -32 and screen_pos.y < HEIGHT):
                self.display_surface.blit(tile.image, screen_pos)
        
        # Draw player on top
        screen_pos = self.camera.apply(self.player)
        self.display_surface.blit(self.player.image, screen_pos)
        
        # Draw UI elements
        self.draw_ui()
        
    def get_collision_sprites(self):
        return self.collision_sprite




