import pygame
from config import *
from entities.player import Player
from entities.enemy import Enemy
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
        self.enemies = pygame.sprite.Group()  # Group for actual enemy sprites
        self.enemy_projectiles = pygame.sprite.Group()  # Group for enemy projectiles
        
        # Game stats
        self.enemies_hit = 0
        self.game_over = False
        self.max_enemies = 5
        self.enemy_spawn_timer = 0
        self.enemy_spawn_delay = 300  # Spawn new enemy every 5 seconds (300 frames at 60fps)
        
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
        
        # Create enemies
        self.create_enemies()
    
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
    
    def create_enemies(self):
        """Create enemies at various positions with waypoints"""
        # Get ground level from player's position and move enemies 30px up
        ground_level = self.player.rect.bottom - 30  # Use player's bottom minus 30px
        
        # Define enemy positions and their waypoints - 5 enemies in different areas
        enemy_data = [
            {
                'pos': (200, ground_level),  # Area 1: Left side
                'waypoints': [(200, ground_level), (300, ground_level), (400, ground_level), (300, ground_level)]
            },
            {
                'pos': (800, ground_level),  # Area 2: Center-right
                'waypoints': [(800, ground_level), (900, ground_level), (1000, ground_level), (900, ground_level)]
            },
            {
                'pos': (1400, ground_level),  # Area 3: Far right
                'waypoints': [(1400, ground_level), (1500, ground_level), (1600, ground_level), (1500, ground_level)]
            },
            {
                'pos': (600, ground_level),  # Area 4: Upper area
                'waypoints': [(600, ground_level), (700, ground_level), (800, ground_level), (700, ground_level)]
            },
            {
                'pos': (1200, ground_level),  # Area 5: Middle area
                'waypoints': [(1200, ground_level), (1300, ground_level), (1400, ground_level), (1300, ground_level)]
            }
        ]
        
        for data in enemy_data:
            enemy = Enemy(data['pos'][0], data['pos'][1], data['waypoints'])
            self.enemies.add(enemy)
    
    def check_projectile_collisions(self):
        """Check collisions between player and enemy projectiles"""
        for enemy in self.enemies:
            for projectile in enemy.projectiles:
                if projectile.rect.colliderect(self.player.rect):
                    # Player hit by projectile (disabled for testing)
                    # self.player.take_damage(projectile.damage)
                    projectile.kill()
    
    def check_attack_collisions(self):
        """Check collisions between player attacks and enemies"""
        if not self.player.attacking:
            # Reset hit tracking when not attacking
            for enemy in self.enemies:
                if hasattr(enemy, 'hit_this_attack'):
                    delattr(enemy, 'hit_this_attack')
            return
            
        # Create attack hitbox
        attack_frame = int(self.player.attack_index)
        if attack_frame >= len(self.player.current_attack_frames_right):
            return
        
        # Sword hitbox - wider but shorter, closer to player
        hitbox_width = 80  # Wider for sword length
        hitbox_height = 30  # Shorter height for sword width
        
        # Position hitbox closer to player and lower
        player_y = self.player.rect.centery + 50  # 50 pixels below center
        
        if self.player.facing_right:
            # Hitbox extends to the right of the player, closer and lower
            hitbox_x = self.player.rect.centerx + 10  # Closer to player
            hitbox_y = player_y - hitbox_height // 2  # Center on lower position
        else:
            # Hitbox extends to the left of the player, closer and lower
            hitbox_x = self.player.rect.centerx - hitbox_width - 10  # Closer to player
            hitbox_y = player_y - hitbox_height // 2  # Center on lower position
        
        attack_hitbox = pygame.Rect(hitbox_x, hitbox_y, hitbox_width, hitbox_height)
        
        # Debug: Draw attack hitbox in screen coordinates (remove this later)
        attack_screen_rect = pygame.Rect(
            attack_hitbox.x - self.camera.camera.x,
            attack_hitbox.y - self.camera.camera.y,
            attack_hitbox.width,
            attack_hitbox.height
        )
        pygame.draw.rect(self.display_surface, (255, 0, 0), attack_screen_rect, 2)
        
        # Check collision with enemies - only one enemy can be hit per attack
        hit_an_enemy = False
        for enemy in self.enemies:
            # Only draw debug hitbox for alive enemies
            if enemy.is_alive:
                # Debug: Draw enemy hitbox
                enemy_screen_pos = self.camera.apply(enemy)
                enemy_debug_rect = pygame.Rect(enemy_screen_pos[0], enemy_screen_pos[1], enemy.rect.width, enemy.rect.height)
                pygame.draw.rect(self.display_surface, (0, 255, 0), enemy_debug_rect, 2)
            
            # Only hit one enemy per attack
            if not hit_an_enemy and attack_hitbox.colliderect(enemy.rect) and enemy.is_alive and not hasattr(enemy, 'hit_this_attack'):
                # Only count hit if enemy actually dies
                if enemy.take_damage(1):
                    self.enemies_hit += 1
                # Mark enemy as hit this attack to prevent multiple hits
                enemy.hit_this_attack = True
                hit_an_enemy = True  # Only one enemy can be hit per attack

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
        
        # Check if game is over
        if self.player.health <= 0:
            self.game_over = True
            return
        
        # Update player with proper argumentalsono 
        self.player.update(keys, collision_sprites, self.enemy_sprite)
        
        # Update enemies
        for enemy in self.enemies:
            enemy.update(self.player, collision_sprites)
        
        # Spawn enemies if less than max
        self.spawn_enemies_if_needed()
        
        # Check collisions
        self.check_projectile_collisions()
        self.check_attack_collisions()
        
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
        
        # Draw enemies (only alive ones)
        for enemy in self.enemies:
            if enemy.is_alive:
                # Use camera.apply() to ensure enemy is always visible
                screen_pos = self.camera.apply(enemy)
                enemy.draw(self.display_surface, screen_pos)
            
            # Draw enemy projectiles
            for projectile in enemy.projectiles:
                projectile_screen_pos = self.camera.apply(projectile)
                projectile.draw(self.display_surface, projectile_screen_pos)
        
        # Draw player on top
        screen_pos = self.camera.apply(self.player)
        self.display_surface.blit(self.player.image, screen_pos)
        
        # Draw player health bar
        self.player.draw_health_bar(self.display_surface)
        
        # Draw UI elements
        self.draw_ui()
        
        # Draw game stats
        self.draw_game_stats()
        
        # Draw game over screen on top of everything
        if self.game_over:
            self.draw_game_over_screen()
        
    def draw_game_stats(self):
        """Draw game statistics on screen"""
        font = pygame.font.Font(None, 36)
        
        # Count alive enemies
        alive_enemies = sum(1 for enemy in self.enemies if enemy.is_alive)
        
        # Draw enemy hit count
        hit_text = font.render(f"Enemies Hit: {self.enemies_hit}", True, (255, 255, 255))
        self.display_surface.blit(hit_text, (10, 10))
        
        # Draw player health
        health_text = font.render(f"Health: {self.player.health}/{self.player.max_health}", True, (255, 255, 255))
        self.display_surface.blit(health_text, (10, 50))
        
        # Draw alive enemies count (moved to right side to avoid overlap with weapon info)
        alive_text = font.render(f"Alive Enemies: {alive_enemies}", True, (255, 255, 255))
        self.display_surface.blit(alive_text, (400, 10))
    
    def draw_game_over_screen(self):
        """Draw game over screen"""
        # Create darker overlay for better visibility
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(200)  # Increased opacity
        overlay.fill((0, 0, 0))
        self.display_surface.blit(overlay, (0, 0))
        
        # Draw game over text with larger fonts
        font_large = pygame.font.Font(None, 96)  # Increased from 72
        font_medium = pygame.font.Font(None, 64)  # Increased from 48
        font_small = pygame.font.Font(None, 48)   # For instructions
        
        game_over_text = font_large.render("GAME OVER", True, (255, 0, 0))
        game_over_rect = game_over_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 80))
        self.display_surface.blit(game_over_text, game_over_rect)
        
        you_died_text = font_medium.render("You Died!", True, (255, 255, 255))
        you_died_rect = you_died_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 20))
        self.display_surface.blit(you_died_text, you_died_rect)
        
        stats_text = font_medium.render(f"Enemies Defeated: {self.enemies_hit}", True, (255, 255, 255))
        stats_rect = stats_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 40))
        self.display_surface.blit(stats_text, stats_rect)
        
        restart_text = font_small.render("Press R to restart or ESC to exit", True, (200, 200, 200))
        restart_rect = restart_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 100))
        self.display_surface.blit(restart_text, restart_rect)

    def spawn_enemies_if_needed(self):
        """Spawn enemies based on time and maintain minimum count"""
        # Increment spawn timer
        self.enemy_spawn_timer += 1
        
        # Count alive enemies
        alive_enemies = sum(1 for enemy in self.enemies if enemy.is_alive)
        
        # Log alive enemy count every 60 frames (1 second) to see when count exceeds 5
        if self.enemy_spawn_timer % 60 == 0:
            print(f"Alive Enemies: {alive_enemies} (Total Enemies: {len(self.enemies)})")
        
        # Spawn new enemy if timer is up OR if we have fewer than minimum enemies
        # But never exceed 5 alive enemies at any time
        should_spawn = ((self.enemy_spawn_timer >= self.enemy_spawn_delay) or (alive_enemies < 3)) and (alive_enemies < 5)
        
        # Additional safety check: if we somehow have more than 5 alive enemies, don't spawn more
        if alive_enemies >= 5:
            should_spawn = False
            
        # Emergency cleanup: if we have more than 5 alive enemies, kill the excess ones
        if alive_enemies > 5:
            print(f"WARNING: Too many alive enemies ({alive_enemies}), killing excess...")
            alive_list = [enemy for enemy in self.enemies if enemy.is_alive]
            # Kill the excess enemies (keep only the first 5)
            for i in range(5, len(alive_list)):
                alive_list[i].is_alive = False
                alive_list[i].respawn_timer = 0
        
        if should_spawn:
            # Spawn a new enemy at a random position near the player
            import random
            offset_x = random.randint(-400, 400)
            offset_y = random.randint(-300, 300)
            spawn_x = self.player.rect.centerx + offset_x
            spawn_y = self.player.rect.centery + offset_y
            
            # Make sure spawn position is within reasonable bounds
            spawn_x = max(100, min(spawn_x, 2000))
            spawn_y = max(100, min(spawn_y, 600))
            
            # Create waypoints around spawn position
            waypoints = [
                (spawn_x, spawn_y),
                (spawn_x + 100, spawn_y),
                (spawn_x, spawn_y + 100),
                (spawn_x - 100, spawn_y)
            ]
            
            enemy = Enemy(spawn_x, spawn_y, waypoints)
            self.enemies.add(enemy)
            self.visible_sprite.add(enemy)
            
            # Reset timer
            self.enemy_spawn_timer = 0

    def get_collision_sprites(self):
        return self.collision_sprite




