# main.py

import pygame, sys
from config import *
from entities.player import Player
from levels.level import Level
from levels.background import LayeredBackground
from start_screen import StartScreen

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Luna Endless Lesson")
clock = pygame.time.Clock()

# Set up font for the inventory display
pygame.font.init()
font = pygame.font.Font(None, 36)


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
    
    # Create layered background (dark theme)
    background = LayeredBackground()

    # Main game loop
    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            # Handle weapon switching with keydown events
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    if level.player.weapon_switched:
                        level.player.current_attack_frames_right = level.player.attack1_frames_right
                        level.player.current_attack_frames_left = level.player.attack1_frames_left
                        level.player.weapon_switched = False
                    else:
                        level.player.current_attack_frames_right = level.player.attack2_frames_right
                        level.player.current_attack_frames_left = level.player.attack2_frames_left
                        level.player.weapon_switched = True
                

        keys = pygame.key.get_pressed()

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
        weapon_text = "Weapon: Sword" if not level.player.weapon_switched else "Weapon: Bow and Arrow"
        text_surface = font.render(weapon_text, True, (255, 255, 255))
        screen.blit(text_surface, (10, 10))
        
        
        # DEBUG: Show player position
        pos_text = f"Player Y: {level.player.rect.bottom} | Ground: {HEIGHT - GROUND_HEIGHT}"
        pos_surface = font.render(pos_text, True, (255, 255, 0))
        screen.blit(pos_surface, (10, 70))

        pygame.display.flip()

# Main execution
if __name__ == "__main__":
    # Run start screen first
    if run_start_screen():
        # If user chose to start game, run the main game
        run_game()
