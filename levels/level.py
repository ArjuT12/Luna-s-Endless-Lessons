import pygame
from config import *
from entities.player import Player
from entities.enemy import Enemy
from entities.enemy_factory import EnemyFactory
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
        
        # Score system
        self.score = 0
        self.survival_time = 0
        self.score_multiplier = 1.0
        self.combo_count = 0
        self.last_kill_time = 0
        self.max_combo = 0
        self.start_time = 0
        
        # UI animations
        self.score_popups = []  # List of score popup animations
        self.ui_animations = {
            'health_flash': 0,
            'combo_flash': 0,
            'score_flash': 0
        }
        
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
        
        # Initialize the level
        self.setup_level()
        
        # Start timing
        self.start_time = pygame.time.get_ticks()
    
    def is_position_on_tile_id(self, x, y, tile_id):
        """Check if a position is on a specific tile ID"""
        if not self.map_loader.map_data:
            return False
        
        tile_width = self.map_loader.map_data.get('tilewidth', 32)
        tile_height = self.map_loader.map_data.get('tileheight', 32)
        map_width = self.map_loader.map_data.get('width', 0)
        
        # Convert world position to tile coordinates
        tile_x = int(x // tile_width)
        tile_y = int(y // tile_height)
        
        # Check if coordinates are within map bounds
        if tile_x < 0 or tile_x >= map_width or tile_y < 0:
            return False
        
        # Get the tile data from the first layer
        if 'layers' in self.map_loader.map_data and len(self.map_loader.map_data['layers']) > 0:
            layer_data = self.map_loader.map_data['layers'][0].get('data', [])
            map_height = self.map_loader.map_data.get('height', 0)
            
            if tile_y >= map_height:
                return False
            
            # Calculate index in the 1D array
            index = tile_y * map_width + tile_x
            
            if 0 <= index < len(layer_data):
                return layer_data[index] == tile_id
        
        return False
    
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
        # Ground is from 0 to 96 pixels from bottom, so spawn enemies above ground
        # Spawn enemies at Y position 520
        ground_level = 520  # 520 pixels from top
        
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
            # Check if initial spawn position is not on tile ID 13
            if not self.is_position_on_tile_id(data['pos'][0], data['pos'][1], 13):
                enemy = EnemyFactory.create_enemy('slime', data['pos'][0], data['pos'][1], data['waypoints'])
                self.enemies.add(enemy)
            else:
                print(f"Skipping enemy spawn at ({data['pos'][0]}, {data['pos'][1]}) - on tile ID 13")
    
    def check_projectile_collisions(self):
        """Check collisions between player and enemy projectiles"""
        for enemy in self.enemies:
            for projectile in enemy.projectiles:
                if projectile.rect.colliderect(self.player.rect):
                    # Player hit by projectile (disabled for testing)
                    # self.player.take_damage(projectile.damage)
                    projectile.kill()
    
    def check_enemy_attack_collisions(self):
        """Check collisions between enemy attacks and player"""
        for enemy in self.enemies:
            if not enemy.is_alive:
                continue
                
            # Check if enemy is colliding with player (simple rectangle collision)
            if enemy.rect.colliderect(self.player.rect):
                # Check if enemy can attack (not on cooldown)
                if hasattr(enemy, 'can_attack') and enemy.can_attack(self.player):
                    # Player takes damage
                    self.player.take_damage(enemy.attack_damage)
                    print(f"Player hit by {enemy.enemy_type}! Health: {self.player.health}/{self.player.max_health}")
                    
                    # Flash health UI
                    self.ui_animations['health_flash'] = 30
                    
                    # Set attack cooldown to prevent continuous damage
                    enemy.attack_cooldown = enemy.attack_cooldown_time
    
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
                    # Add score for killing enemy with position for popup
                    enemy_screen_pos = self.camera.apply(enemy)
                    points_earned = self.add_score(100, "kill", enemy_screen_pos)
                    print(f"Enemy killed! +{points_earned} points (Combo: {self.combo_count}x)")
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
        
        # Update survival time and UI animations
        self.update_survival_time()
        self.update_ui_animations()
        
        # Check if game is over
        if self.player.health <= 0:
            self.game_over = True
            # Don't return here - let the game over screen be drawn
        
        # Update player with proper argumentalsono 
        self.player.update(keys, collision_sprites, self.enemy_sprite)
        
        # Update enemies
        for enemy in self.enemies:
            if hasattr(enemy, 'update') and enemy.__class__.__name__ == 'SlimeEnemy':
                enemy.update(self.player, collision_sprites, self)
            else:
                enemy.update(self.player, collision_sprites)
        
        # Spawn enemies if less than max
        self.spawn_enemies_if_needed()
        
        # Check collisions
        self.check_projectile_collisions()
        self.check_attack_collisions()
        self.check_enemy_attack_collisions()
        
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
        
        # Draw UI elements
        self.draw_ui()
        
        # Draw game stats
        self.draw_game_stats()
        
        # Draw score popups
        self.draw_score_popups()
        
        # Draw game over screen on top of everything
        if self.game_over:
            self.draw_game_over_screen()
        
    def draw_game_stats(self):
        """Draw modern game statistics UI"""
        # UI Constants
        UI_PADDING = 20
        UI_BG_ALPHA = 180
        UI_CORNER_RADIUS = 8
        
        # Create semi-transparent background panels
        panel_bg = pygame.Surface((300, 120), pygame.SRCALPHA)
        pygame.draw.rect(panel_bg, (0, 0, 0, UI_BG_ALPHA), (0, 0, 300, 120), border_radius=UI_CORNER_RADIUS)
        
        # Left panel (Health, Score, Combo)
        self.display_surface.blit(panel_bg, (UI_PADDING, UI_PADDING))
        
        # Right panel (Time, Enemies, Multiplier)
        self.display_surface.blit(panel_bg, (WIDTH - 320, UI_PADDING))
        
        # Fonts
        font_large = pygame.font.Font(None, 32)
        font_medium = pygame.font.Font(None, 24)
        font_small = pygame.font.Font(None, 18)
        
        # Count alive enemies
        alive_enemies = sum(1 for enemy in self.enemies if enemy.is_alive)
        
        # Left Panel Content
        left_x = UI_PADDING + 15
        left_y = UI_PADDING + 15
        
        # Health bar with gradient effect and flashing
        health_percent = self.player.health / self.player.max_health
        
        # Health color based on percentage
        if health_percent > 0.6:
            health_color = (100, 255, 100)  # Green
        elif health_percent > 0.3:
            health_color = (255, 255, 100)  # Yellow
        else:
            health_color = (255, 100, 100)  # Red
        
        # Flash effect when health is low
        if health_percent < 0.3 and self.ui_animations['health_flash'] > 0:
            health_color = (255, 255, 255)  # White flash
        
        health_text = font_medium.render("HEALTH", True, (200, 200, 200))
        self.display_surface.blit(health_text, (left_x, left_y))
        
        # Health bar background with border
        bar_bg_rect = pygame.Rect(left_x, left_y + 25, 200, 12)
        pygame.draw.rect(self.display_surface, (30, 30, 30), bar_bg_rect, border_radius=6)
        pygame.draw.rect(self.display_surface, (60, 60, 60), bar_bg_rect, 2, border_radius=6)
        
        # Health bar fill with gradient effect
        if health_percent > 0:
            bar_fill_rect = pygame.Rect(left_x, left_y + 25, int(200 * health_percent), 12)
            pygame.draw.rect(self.display_surface, health_color, bar_fill_rect, border_radius=6)
            
            # Add highlight effect
            highlight_rect = pygame.Rect(left_x, left_y + 25, int(200 * health_percent), 4)
            highlight_color = tuple(min(255, c + 50) for c in health_color)
            pygame.draw.rect(self.display_surface, highlight_color, highlight_rect, border_radius=6)
        
        # Health text with flash effect
        health_text_color = (255, 255, 255)
        if self.ui_animations['health_flash'] > 0:
            health_text_color = (255, 100, 100)
        
        health_value = font_small.render(f"{self.player.health}/{self.player.max_health}", True, health_text_color)
        self.display_surface.blit(health_value, (left_x + 210, left_y + 25))
        
        # Score with flash effect
        score_text = font_medium.render("SCORE", True, (200, 200, 200))
        self.display_surface.blit(score_text, (left_x, left_y + 50))
        
        # Score value with flash effect
        score_color = (255, 215, 0)  # Gold color
        if self.ui_animations['score_flash'] > 0:
            score_color = (255, 255, 255)  # White flash
        
        score_value = font_large.render(f"{self.score:,}", True, score_color)
        self.display_surface.blit(score_value, (left_x, left_y + 70))
        
        # Combo (if active) with flash effect
        if self.combo_count > 1:
            combo_color = (255, 100, 100)
            if self.ui_animations['combo_flash'] > 0:
                combo_color = (255, 255, 100)  # Yellow flash
            
            combo_text = font_small.render(f"COMBO x{self.combo_count}", True, combo_color)
            self.display_surface.blit(combo_text, (left_x + 150, left_y + 50))
        
        # Right Panel Content
        right_x = WIDTH - 305
        right_y = UI_PADDING + 15
        
        # Survival Time
        time_text = font_medium.render("TIME", True, (200, 200, 200))
        self.display_surface.blit(time_text, (right_x, right_y))
        
        minutes = self.survival_time // 60
        seconds = self.survival_time % 60
        time_value = font_large.render(f"{minutes:02d}:{seconds:02d}", True, (100, 255, 100))
        self.display_surface.blit(time_value, (right_x, right_y + 20))
        
        # Enemies Alive
        enemies_text = font_medium.render("ENEMIES", True, (200, 200, 200))
        self.display_surface.blit(enemies_text, (right_x, right_y + 50))
        
        enemies_value = font_large.render(f"{alive_enemies}", True, (255, 150, 150))
        self.display_surface.blit(enemies_value, (right_x, right_y + 70))
        
        # Multiplier (if > 1)
        if self.score_multiplier > 1.0:
            multiplier_text = font_small.render(f"MULTIPLIER x{self.score_multiplier:.1f}", True, (255, 255, 100))
            self.display_surface.blit(multiplier_text, (right_x + 100, right_y + 50))
    
    def draw_score_popups(self):
        """Draw animated score popups"""
        for popup in self.score_popups:
            if popup['alpha'] > 0:
                # Create text surface with alpha
                font = pygame.font.Font(None, int(24 * popup['scale']))
                text_surface = font.render(popup['text'], True, (255, 215, 0))  # Gold color
                
                # Create surface with alpha
                popup_surface = pygame.Surface(text_surface.get_size(), pygame.SRCALPHA)
                popup_surface.set_alpha(popup['alpha'])
                popup_surface.blit(text_surface, (0, 0))
                
                # Draw with offset for centering
                text_rect = text_surface.get_rect(center=(popup['x'], popup['y']))
                self.display_surface.blit(popup_surface, text_rect)
    
    def draw_game_over_screen(self):
        """Draw game over screen"""
        # Create semi-transparent overlay so game is visible behind
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(120)  # More transparent so game is visible
        overlay.fill((0, 0, 0))
        self.display_surface.blit(overlay, (0, 0))
        
        # Draw game over text with smaller fonts to prevent overlapping
        font_large = pygame.font.Font(None, 80)   # Smaller main title
        font_medium = pygame.font.Font(None, 48)  # Smaller medium text
        font_small = pygame.font.Font(None, 36)   # Smaller small text
        
        # Main game over text with outline for better visibility
        game_over_text = font_large.render("GAME OVER", True, (255, 0, 0))
        game_over_rect = game_over_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 120))
        
        # Draw outline
        outline_color = (0, 0, 0)
        for dx in [-2, 0, 2]:
            for dy in [-2, 0, 2]:
                if dx != 0 or dy != 0:
                    outline_rect = game_over_text.get_rect(center=(WIDTH//2 + dx, HEIGHT//2 - 120 + dy))
                    outline_surface = font_large.render("GAME OVER", True, outline_color)
                    self.display_surface.blit(outline_surface, outline_rect)
        
        self.display_surface.blit(game_over_text, game_over_rect)
        
        you_died_text = font_medium.render("You Died!", True, (255, 255, 255))
        you_died_rect = you_died_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 60))
        self.display_surface.blit(you_died_text, you_died_rect)
        
        # Score breakdown
        score_breakdown = self.get_score_breakdown()
        
        # Final Score
        final_score_text = font_medium.render(f"FINAL SCORE: {self.score:,}", True, (255, 215, 0))
        final_score_rect = final_score_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 10))
        self.display_surface.blit(final_score_text, final_score_rect)
        
        # Stats grid with better spacing
        stats_y = HEIGHT//2 + 40
        stats_spacing = 40  # Increased spacing
        
        # Time survived
        time_text = font_small.render(f"Time Survived: {score_breakdown['survival_time']}s", True, (100, 255, 100))
        time_rect = time_text.get_rect(center=(WIDTH//2, stats_y))
        self.display_surface.blit(time_text, time_rect)
        
        # Enemies killed
        enemies_text = font_small.render(f"Enemies Defeated: {score_breakdown['enemies_killed']}", True, (255, 150, 150))
        enemies_rect = enemies_text.get_rect(center=(WIDTH//2, stats_y + stats_spacing))
        self.display_surface.blit(enemies_text, enemies_rect)
        
        # Max combo
        combo_text = font_small.render(f"Max Combo: {score_breakdown['max_combo']}x", True, (255, 100, 100))
        combo_rect = combo_text.get_rect(center=(WIDTH//2, stats_y + stats_spacing * 2))
        self.display_surface.blit(combo_text, combo_rect)
        
        # Restart instruction with more space
        restart_text = font_small.render("Press R to restart or ESC to exit", True, (200, 200, 200))
        restart_rect = restart_text.get_rect(center=(WIDTH//2, stats_y + stats_spacing * 3 + 20))
        self.display_surface.blit(restart_text, restart_rect)
        
        # Add blinking effect for restart instruction
        import time
        if int(time.time() * 2) % 2:  # Blink every 0.5 seconds
            restart_text = font_small.render("Press R to restart or ESC to exit", True, (255, 255, 255))
            self.display_surface.blit(restart_text, restart_rect)

    def add_score(self, points, reason="kill", position=None):
        """Add points to score with combo system"""
        current_time = pygame.time.get_ticks()
        
        # Combo system - if kills are within 2 seconds, increase combo
        if reason == "kill" and current_time - self.last_kill_time < 2000:
            self.combo_count += 1
            self.score_multiplier = min(1.0 + (self.combo_count * 0.1), 3.0)  # Max 3x multiplier
            self.ui_animations['combo_flash'] = 30  # Flash for 30 frames
        else:
            self.combo_count = 1
            self.score_multiplier = 1.0
        
        # Calculate final score
        final_points = int(points * self.score_multiplier)
        self.score += final_points
        self.last_kill_time = current_time
        self.max_combo = max(self.max_combo, self.combo_count)
        
        # Create score popup
        if position:
            self.score_popups.append({
                'text': f"+{final_points}",
                'x': position[0],
                'y': position[1],
                'timer': 60,  # 1 second at 60fps
                'alpha': 255,
                'scale': 1.0
            })
        
        # Flash score UI
        self.ui_animations['score_flash'] = 15
        
        return final_points
    
    def update_survival_time(self):
        """Update survival time"""
        if not self.game_over:
            self.survival_time = (pygame.time.get_ticks() - self.start_time) // 1000  # Convert to seconds
    
    def update_ui_animations(self):
        """Update UI animations and effects"""
        # Update score popups
        for popup in self.score_popups[:]:
            popup['timer'] -= 1
            popup['y'] -= 2  # Move up
            popup['alpha'] = max(0, popup['alpha'] - 4)  # Fade out
            popup['scale'] = min(1.5, popup['scale'] + 0.02)  # Scale up slightly
            
            if popup['timer'] <= 0:
                self.score_popups.remove(popup)
        
        # Update UI flash effects
        for key in self.ui_animations:
            if self.ui_animations[key] > 0:
                self.ui_animations[key] -= 1
    
    def get_score_breakdown(self):
        """Get detailed score breakdown"""
        return {
            'total_score': self.score,
            'survival_time': self.survival_time,
            'enemies_killed': self.enemies_hit,
            'max_combo': self.max_combo,
            'current_combo': self.combo_count,
            'multiplier': self.score_multiplier
        }

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
            
            # Try to find a valid spawn position (not on tile ID 13)
            max_attempts = 20
            spawn_x = 0
            spawn_y = 0
            valid_position = False
            
            for attempt in range(max_attempts):
                offset_x = random.randint(-400, 400)
                spawn_x = self.player.rect.centerx + offset_x
                
                # Ground is from 0 to 96 pixels from bottom, so spawn enemies above ground
                # Spawn enemies at Y position 520
                spawn_y = 520  # Fixed Y position above ground
                
                # Make sure spawn position is within reasonable bounds
                spawn_x = max(100, min(spawn_x, 2000))
                
                # Check if position is NOT on tile ID 13
                if not self.is_position_on_tile_id(spawn_x, spawn_y, 13):
                    valid_position = True
                    break
            
            # If we couldn't find a valid position, use the last attempt
            if not valid_position:
                print("Warning: Could not find valid spawn position, using fallback")
            
            # Create waypoints around spawn position
            waypoints = [
                (spawn_x, spawn_y),
                (spawn_x + 100, spawn_y),
                (spawn_x, spawn_y + 100),
                (spawn_x - 100, spawn_y)
            ]
            
            enemy = EnemyFactory.create_enemy('slime', spawn_x, spawn_y, waypoints)
            self.enemies.add(enemy)
            self.visible_sprite.add(enemy)
            
            # Reset timer
            self.enemy_spawn_timer = 0

    def get_collision_sprites(self):
        return self.collision_sprite




