# main.py

import pygame, sys
from config import *
from entities.player import Player
from levels.level import Level
from levels.background import LayeredBackground
from start_screen import StartScreen
from api_client import LunaAPIClient

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Luna Endless Lesson")
clock = pygame.time.Clock()

# Set up font for the inventory display
pygame.font.init()
font = pygame.font.Font(None, 36)


def create_background_for_map(map_name):
    """Create appropriate background for the given map"""
    if map_name == "forest2":
        # Use Futuristic City Parallax for forest2
        return LayeredBackground(background_folder="Futuristic City Parallax")
    else:
        # Use parallax background for other maps
        return LayeredBackground()

def run_start_screen():
    """Run the start screen and return whether to start the game"""
    start_screen = StartScreen(WIDTH, HEIGHT)
    action = start_screen.run(screen)
    
    if action == "quit_game":
        pygame.quit()
        sys.exit()
    elif action in ["start_game", "setup_complete"]:
        return True
    return False

def run_game():
    """Run the main game"""
    # Create level and get collision sprites
    level = Level()
    collision_sprites = level.get_collision_sprites()
    
    # Create background based on current map
    background = create_background_for_map(level.current_map)

    # Main game loop
    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            # Handle game over screen
            if level.game_over:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        # Restart game
                        level = Level()
                        collision_sprites = level.get_collision_sprites()
                        background = create_background_for_map(level.current_map)
                        continue
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                continue
            
            # Handle win screen
            if level.game_won:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        # Restart game
                        level = Level()
                        collision_sprites = level.get_collision_sprites()
                        background = create_background_for_map(level.current_map)
                        continue
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                continue
            
            # Weapon switching is now handled in player.py with proper unlock checks
                

        keys = pygame.key.get_pressed()

        # Check if map has changed and update background accordingly
        if hasattr(level, 'current_map') and hasattr(level, '_last_map'):
            if level.current_map != level._last_map:
                background = create_background_for_map(level.current_map)
                level._last_map = level.current_map
        elif hasattr(level, 'current_map'):
            level._last_map = level.current_map

        # Get camera offset for parallax scrolling
        camera_offset = level.camera.camera.topleft
        
        # Log player position information to console
        print(f"Camera X Offset: {camera_offset[0]:.1f} | Camera Y Offset: {camera_offset[1]:.1f} | Player X: {level.player.rect.centerx} | Player Y: {level.player.rect.bottom} | Ground Level: {HEIGHT - GROUND_HEIGHT}")
        
        # Clear screen with background color to remove previous frames
        fill_color = background.get_background_fill_color()
        screen.fill(fill_color)
        
        # Draw layered background with parallax scrolling
        background.draw(screen, camera_offset)
        
        level.run(keys, collision_sprites)

        # INVENTORY DISPLAY (UI elements stay in fixed screen position)

        pygame.display.flip()

# Main execution
if __name__ == "__main__":
    # Initialize API client - all API calls happen at start and end only
    api_client = LunaAPIClient()
    
    # Single API sync at game startup only
    print("🔄 Initializing game data...")
    sync_result = api_client.auto_sync_player_data()
    if sync_result["success"]:
        print(f"✅ {sync_result['message']}")
    else:
        print(f"❌ {sync_result['message']}: {sync_result.get('error', 'Unknown error')}")
    
    # Run start screen first
    if run_start_screen():
        # No API calls here - only at start and end
        # If user chose to start game, run the main game
        run_game()
