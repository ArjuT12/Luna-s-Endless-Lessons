import pygame
from config import *
from entities.player import Player
from entities.enemy import Enemy
from entities.enemy_factory import EnemyFactory
from entities.bow import Bow
from entities.arrow import Arrow
from levels.tile import Tile
from levels.camera import Camera
from levels.map_loader import MapLoader
from story_progression import StoryProgression
from api_client import get_api_client, APIError



class Level:
    def __init__(self):
        
        #Level setup
        self.display_surface = pygame.display.get_surface()
        
        # Story progression system
        self.story_progression = StoryProgression()
        
        # API integration
        self.api_client = get_api_client()
        self.api_connected = False
        self.score_saved = False
        self.player_data_synced = False
        self.game_data_initialized = False
        self.player_progress = None
        
        # Currency system
        self.currency_earned = 0
        self.currency_rule = None

        #sprite Group 
        self.visible_sprite = pygame.sprite.Group()
        self.active_sprite = pygame.sprite.Group()
        self.collision_sprite = pygame.sprite.Group()
        self.enemy_sprite = pygame.sprite.Group()  # Group for enemy tiles
        self.enemies = pygame.sprite.Group()  # Group for actual enemy sprites
        self.enemy_projectiles = pygame.sprite.Group()  # Group for enemy projectiles
        self.hearts = pygame.sprite.Group()  # Group for heart objects
        self.player_arrows = pygame.sprite.Group()  # Group for player arrows
        self.animated_objects = pygame.sprite.Group()  # Group for animated objects
        
        # Game stats
        self.enemies_hit = 0
        self.game_over = False
        self.game_won = False
        self.max_enemies = 5
        self.enemy_spawn_timer = 0
        self.enemy_spawn_delay = 600  # Spawn new enemy every 10 seconds (600 frames at 60fps) - reduced spawn rate
        
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
        
        # Map progression system
        self.current_map = "forest2"  # Start with forest2 map
        self.map_transitioning = False
        self.transition_timer = 0
        self.transition_duration = 120  # 2 seconds at 60fps
        self.transition_progress = 0.0
        self.sunrise_character = None  # Static character for sunrise
        
        # Interaction system
        self.interactive_tiles = []
        self.nearby_interactive = None
        self.show_interaction_prompt = False
        self.dialogue_active = False
        self.current_dialogue = None
        self.dialogue_index = 0
        
        # Story dialogue system
        self.story_dialogue_active = False
        self.current_story_dialogue = None
        self.story_dialogue_index = 0
        self.show_intro_dialogue = False
        
        # Key state tracking for dialogue
        self.z_pressed = False
        self.enter_pressed = False
        self.q_pressed = False
        self.r_pressed = False
        
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
        
        # Initialize all game data through API
        self.initialize_game_data()
    
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
        self.player = Player(self.story_progression)
        self.player.rect.centerx = 32  # Starting position X: 32
        self.player.rect.bottom = 543  # Player feet at 97 pixels from bottom (640 - 97 = 543)
        self.player.on_ground = True  # Ensure player starts on ground
        self.player.vel_y = 0  # Ensure player starts with zero velocity
        
        # Show intro dialogue if not seen before, or story dialogue if player died
        if not self.story_progression.progress["has_seen_intro"]:
            self.show_intro_dialogue = True
            self.story_progression.progress["has_seen_intro"] = True
            self.story_progression.save_progress()
        else:
            # Check if we should show story dialogue after death
            current_story_part = self.story_progression.progress["current_story_part"]
            if current_story_part > 0:
                # Only start dialogue if there is dialogue to show (skip after 4 deaths)
                dialogue = self.story_progression.get_story_dialogue(current_story_part)
                if dialogue:  # Only start if dialogue exists
                    self.start_story_dialogue(current_story_part)
        
        # Create bow weapon using attack2_sheet (bow and arrow sprites)
        bow_frames = self.player.attack2_frames_right  # Use attack2_sheet for bow
        self.bow = Bow(bow_frames, 0, 0)  # Create bow instance
        
        # Create enemies
        self.create_enemies()
        
        # Create sunrise character (static blue and orange man)
        self.create_sunrise_character()
    
    def create_sunrise_character(self):
        """Create a static character for the sunrise map"""
        # Create a simple static character sprite
        character_surface = pygame.Surface((32, 48), pygame.SRCALPHA)
        
        # Draw a simple character with blue and orange colors
        # Head (blue)
        pygame.draw.circle(character_surface, (100, 150, 255), (16, 12), 8)
        
        # Body (orange)
        pygame.draw.rect(character_surface, (255, 165, 0), (12, 20, 8, 16))
        
        # Arms (orange)
        pygame.draw.rect(character_surface, (255, 165, 0), (8, 22, 4, 12))
        pygame.draw.rect(character_surface, (255, 165, 0), (20, 22, 4, 12))
        
        # Legs (blue)
        pygame.draw.rect(character_surface, (100, 150, 255), (12, 36, 4, 12))
        pygame.draw.rect(character_surface, (100, 150, 255), (16, 36, 4, 12))
        
        self.sunrise_character = character_surface
    
    def load_map(self):
        """Load the appropriate map based on current state"""
        if self.current_map == "forest2":
            map_file = 'forest2.json'  # First forest map
        else:
            map_file = 'night_time_map.json'  # Second forest map (night time)
        
        # Load map data (this will also load all referenced tilesets)
        if self.map_loader.load_map(map_file):
            print(f"Map loaded successfully: {map_file}")
            
            # Create tiles from map data
            self.map_tiles = self.map_loader.create_tiles_from_map([self.visible_sprite, self.collision_sprite, self.enemy_sprite])
            
            # Create objects from map data (hearts, animated objects, etc.)
            self.map_objects = self.map_loader.create_objects_from_map([self.hearts, self.animated_objects])
            
            # Collect interactive tiles
            self.interactive_tiles = [tile for tile in self.map_tiles if hasattr(tile, 'is_interactive') and tile.is_interactive]
            print(f"Created {len(self.map_tiles)} map tiles")
            print(f"Created {len(self.map_objects)} map objects")
            print(f"Found {len(self.interactive_tiles)} interactive tiles")
        else:
            print(f"Failed to load map data: {map_file}")
    
    def check_map_transition(self):
        """Check if player has reached the end of the current map and should transition"""
        if self.map_transitioning:
            return
        
        # Check if player has reached the end of the forest2 map
        if self.current_map == "forest2":
            # Get map width in pixels
            map_width = self.map_loader.map_data.get('width', 0) * self.map_loader.map_data.get('tilewidth', 32)
            
            # Check if player is near the end of the map (within 100 pixels)
            if self.player.rect.centerx >= map_width - 100:
                self.start_map_transition()
    
    def check_win_condition(self):
        """Check if player has won by reaching the end of the night map"""
        if self.current_map == "nighttime" and not self.game_won:
            # Night map is 100 tiles wide (3200 pixels), win when player reaches near the end
            if self.player.rect.centerx >= 3000:  # 200 pixels before the end
                self.game_won = True
                print("🎉 CONGRATULATIONS! Luna has completed her endless lesson!")
                print(f"Final Score: {self.score:,}")
                print("Press R to play again or ESC to exit")
    
    def start_map_transition(self):
        """Start the transition to the night time forest map"""
        if self.map_transitioning:
            return
        
        print("Starting map transition to night time forest...")
        self.map_transitioning = True
        self.transition_timer = 0
        self.transition_progress = 0.0
        
        # Clear current enemies and objects
        self.enemies.empty()
        self.hearts.empty()
        self.player_arrows.empty()
        self.animated_objects.empty()  # Clear animated objects from previous map
        
        # Clear all map tiles from sprite groups
        for tile in self.map_tiles:
            tile.kill()  # Remove from all groups
        self.map_tiles.clear()
        
        # Clear interactive tiles
        self.interactive_tiles.clear()
        
        # Switch to night time forest map
        self.current_map = "nighttime"
        self.load_map()
        
        # Reposition player at the start of the new map
        self.player.rect.centerx = 32
        self.player.rect.bottom = 543
        self.player.on_ground = True
        self.player.vel_y = 0
        
        # Create new enemies for night time forest map
        self.create_enemies()
    
    def update_map_transition(self):
        """Update the map transition animation"""
        if not self.map_transitioning:
            return
        
        self.transition_timer += 1
        self.transition_progress = min(self.transition_timer / self.transition_duration, 1.0)
        
        # Transition complete
        if self.transition_progress >= 1.0:
            self.map_transitioning = False
            self.transition_timer = 0
            self.transition_progress = 0.0
            print("Map transition completed!")
    
    def draw_map_transition(self):
        """Draw the map transition effect"""
        if not self.map_transitioning:
            return
        
        # Create transition overlay
        overlay = pygame.Surface((WIDTH, HEIGHT))
        
        # Fade effect during transition
        if self.transition_progress < 0.5:
            # Fade out current map
            alpha = int(255 * (1.0 - (self.transition_progress * 2)))
            overlay.set_alpha(alpha)
            overlay.fill((0, 0, 0))
            self.display_surface.blit(overlay, (0, 0))
        else:
            # Fade in new map
            alpha = int(255 * ((self.transition_progress - 0.5) * 2))
            overlay.set_alpha(255 - alpha)
            overlay.fill((0, 0, 0))
            self.display_surface.blit(overlay, (0, 0))
        
        # Draw transition text
        font = pygame.font.Font(None, 48)
        if self.current_map == "nighttime":
            text = font.render("Night Falls...", True, (255, 255, 255))
        else:
            text = font.render("Entering Forest...", True, (255, 255, 255))
        
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        
        # Add background for text
        bg_rect = text_rect.inflate(40, 20)
        pygame.draw.rect(self.display_surface, (0, 0, 0, 150), bg_rect)
        pygame.draw.rect(self.display_surface, (255, 255, 255), bg_rect, 2)
        
        self.display_surface.blit(text, text_rect)
    
    def draw_sunrise_character(self):
        """Draw the static sunrise character"""
        if self.sunrise_character and self.current_map == "forest2":
            # Position character at the end of the map
            map_width = self.map_loader.map_data.get('width', 0) * self.map_loader.map_data.get('tilewidth', 32)
            char_x = map_width - 100
            char_y = 543 - 48  # Above ground level
            
            # Apply camera offset
            screen_pos = self.camera.apply_pos((char_x, char_y))
            
            # Only draw if visible
            if -32 < screen_pos[0] < WIDTH and -48 < screen_pos[1] < HEIGHT:
                self.display_surface.blit(self.sunrise_character, screen_pos)
    
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
    
    def check_enemy_attack_collisions(self, dialogue_active=False):
        """Check collisions between enemy attacks and player"""
        for enemy in self.enemies:
            if not enemy.is_alive:
                continue
                
            # Check if enemy is colliding with player (simple rectangle collision)
            if enemy.rect.colliderect(self.player.rect):
                # Check if enemy can attack (not on cooldown)
                if hasattr(enemy, 'can_attack') and enemy.can_attack(self.player):
                    # Player takes damage
                    self.player.take_damage(enemy.attack_damage, dialogue_active)
                    print(f"Player hit by {enemy.enemy_type}! Health: {self.player.health}/{self.player.max_health}")
                    
                    # Flash health UI
                    self.ui_animations['health_flash'] = 30
                    
                    # Set attack cooldown to prevent continuous damage
                    enemy.attack_cooldown = enemy.attack_cooldown_time
    
    def check_heart_collisions(self):
        """Check collisions between player and heart objects"""
        # Only check heart collisions if hearts are unlocked
        if self.player.can_use_hearts:
            for heart in self.hearts:
                heart.update(self.player)
    
    def check_bow_attacks(self):
        """Handle bow attacks and arrow shooting"""
        if (self.player.attacking and 
            self.player.get_current_weapon() == 'bow'):
            
            print(f"🎯 BOW ATTACK: attacking=True, weapon=bow, attack_index={self.player.attack_index}, arrow_fired={getattr(self, 'arrow_fired_this_attack', False)}")
            
            # Fire arrow at frame 8 (or any frame >= 8 if animation is shorter)
            if (int(self.player.attack_index) >= 8 and 
                not getattr(self, 'arrow_fired_this_attack', False)):  # Fire at frame 8 or later, only once per attack                                                                                                 
                
                print(f"🎯 FIRING ARROW AT FRAME {int(self.player.attack_index)}!")
                # Shoot arrow
                arrow = self.bow.shoot_arrow(self.player.rect, self.player.facing_right)
                if arrow:
                    self.player_arrows.add(arrow)
                    self.arrow_fired_this_attack = True  # Prevent multiple arrows
                    print(f"🎯 ARROW ADDED TO LEVEL! Total arrows: {len(self.player_arrows)}")
                else:
                    print(f"🎯 FAILED TO ADD ARROW TO LEVEL!")
        
        # Reset flag when attack ends
        if not self.player.attacking:
            self.arrow_fired_this_attack = False
    
    def check_arrow_collisions(self):
        """Check collisions between arrows and enemies/animated objects"""
        for arrow in self.player_arrows:
            # Update arrow with both enemies and animated objects
            arrow.update(self.collision_sprite, self.enemies, self.animated_objects)
            
            # Remove dead arrows
            if not arrow.alive():
                self.player_arrows.remove(arrow)
    
    def check_attack_collisions(self):
        """Check collisions between player attacks and enemies"""
        if not self.player.attacking:
            # Reset hit tracking when not attacking
            for enemy in self.enemies:
                if hasattr(enemy, 'hit_this_attack'):
                    delattr(enemy, 'hit_this_attack')
            for animated_obj in self.animated_objects:
                if hasattr(animated_obj, 'hit_this_attack'):
                    delattr(animated_obj, 'hit_this_attack')
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
                # Mark enemy as hit this attack to prevent multiple hits
                enemy.hit_this_attack = True
                hit_an_enemy = True
                
                # Only count hit if enemy actually dies
                if enemy.take_damage(1):
                    self.enemies_hit += 1
                    # Add score for killing enemy with position for popup
                    enemy_screen_pos = self.camera.apply(enemy)
                    points_earned = self.add_score(100, "kill", enemy_screen_pos)
                    print(f"Enemy killed! +{points_earned} points (Combo: {self.combo_count}x)")
                else:
                    print(f"Enemy hit! Health: {enemy.health}/{enemy.max_health}")
        
        # Check collision with animated objects - only one can be hit per attack
        if not hit_an_enemy:
            for animated_obj in self.animated_objects:
                # Only draw debug hitbox for alive animated objects
                if animated_obj.is_alive:
                    # Debug: Draw animated object hitbox
                    obj_screen_pos = self.camera.apply(animated_obj)
                    obj_debug_rect = pygame.Rect(obj_screen_pos[0], obj_screen_pos[1], animated_obj.rect.width, animated_obj.rect.height)
                    pygame.draw.rect(self.display_surface, (255, 255, 0), obj_debug_rect, 2)
                
                # Only hit one animated object per attack
                if not hit_an_enemy and attack_hitbox.colliderect(animated_obj.rect) and animated_obj.is_alive and not hasattr(animated_obj, 'hit_this_attack'):
                    # Mark as hit this attack to prevent multiple hits
                    animated_obj.hit_this_attack = True
                    hit_an_enemy = True
                    
                    # Deal damage to animated object
                    if animated_obj.take_damage(1):
                        self.enemies_hit += 1
                        # Add score for killing animated object
                        obj_screen_pos = self.camera.apply(animated_obj)
                        points_earned = self.add_score(150, "kill", obj_screen_pos)  # Higher score for animated objects
                        print(f"Animated object killed! +{points_earned} points (Combo: {self.combo_count}x)")
                    else:
                        print(f"Animated object hit! Health: {animated_obj.health}/{animated_obj.max_health}")
                # Mark animated object as hit this attack to prevent multiple hits
                animated_obj.hit_this_attack = True
                hit_an_enemy = True  # Only one target can be hit per attack

    def check_interactions(self, keys):
        """Check if player is near interactive tiles and handle interactions"""
        # Handle story dialogue first
        if self.show_intro_dialogue or self.story_dialogue_active:
            # R key for starting/continuing story dialogue
            if keys[pygame.K_r] and not self.r_pressed:
                if self.show_intro_dialogue:
                    self.end_intro_dialogue()  # End intro dialogue when R is pressed
                else:
                    self.next_story_dialogue()
                self.r_pressed = True
            elif not keys[pygame.K_r]:
                self.r_pressed = False
            
            # Z key for continuing story dialogue
            if keys[pygame.K_z] and not self.z_pressed:
                if self.show_intro_dialogue:
                    self.end_intro_dialogue()  # End intro dialogue when Z is pressed
                else:
                    self.next_story_dialogue()
                self.z_pressed = True
            elif not keys[pygame.K_z]:
                self.z_pressed = False
            
            # ENTER key for continuing story dialogue
            if keys[pygame.K_RETURN] and not self.enter_pressed:
                if self.show_intro_dialogue:
                    self.end_intro_dialogue()  # End intro dialogue when ENTER is pressed
                else:
                    self.next_story_dialogue()
                self.enter_pressed = True
            elif not keys[pygame.K_RETURN]:
                self.enter_pressed = False
            
            # ESC key for exiting story dialogue
            if keys[pygame.K_ESCAPE]:
                self.end_story_dialogue()
            return
        
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
        # Reset key press flags to ensure proper input handling after dialogue
        self.z_pressed = False
        self.enter_pressed = False
    
    def start_story_dialogue(self, story_part):
        """Start story dialogue for the given story part"""
        dialogue = self.story_progression.get_story_dialogue(story_part)
        if dialogue:
            print(f"Starting story dialogue for part {story_part}, {len(dialogue)} lines")
            self.current_story_dialogue = dialogue
            self.story_dialogue_index = 0
            self.story_dialogue_active = True
            self.show_intro_dialogue = False
    
    def next_story_dialogue(self):
        """Move to next story dialogue line"""
        if self.story_dialogue_active and self.current_story_dialogue:
            self.story_dialogue_index += 1
            print(f"Story dialogue index: {self.story_dialogue_index}/{len(self.current_story_dialogue)}")
            if self.story_dialogue_index >= len(self.current_story_dialogue):
                print("Ending story dialogue - reached end")
                self.end_story_dialogue()
    
    def end_story_dialogue(self):
        """End current story dialogue"""
        print("Ending story dialogue - movement should be restored")
        self.story_dialogue_active = False
        self.current_story_dialogue = None
        self.story_dialogue_index = 0
        self.show_intro_dialogue = False
        # Reset key press flags to ensure proper input handling after dialogue
        self.r_pressed = False
        self.z_pressed = False
        self.enter_pressed = False
    
    def end_intro_dialogue(self):
        """End intro dialogue"""
        self.show_intro_dialogue = False
        # Reset key press flags to ensure proper input handling after dialogue
        self.r_pressed = False
        self.z_pressed = False
        self.enter_pressed = False
    
    def draw_ui(self):
        """Draw interaction prompts and dialogue"""
        font = pygame.font.Font(None, 36)
        
        # Draw story dialogue
        if self.show_intro_dialogue or self.story_dialogue_active:
            if self.show_intro_dialogue:
                # Get intro dialogue from story progression
                intro_dialogue = self.story_progression.get_intro_dialogue()
                dialogue_text = "\n".join(intro_dialogue)
            elif self.story_dialogue_active and self.current_story_dialogue:
                dialogue_text = self.current_story_dialogue[self.story_dialogue_index]
            else:
                dialogue_text = ""
            
            if dialogue_text:
                # Create story dialogue box (smaller and positioned 70px up)
                # Make it taller for intro dialogue and story dialogues with controls
                if self.show_intro_dialogue:
                    box_height = 200
                elif self.story_dialogue_active:
                    box_height = 250  # Taller for story dialogues with controls
                else:
                    box_height = 150
                dialogue_rect = pygame.Rect(50, HEIGHT - 320, WIDTH - 100, box_height)
                pygame.draw.rect(self.display_surface, (0, 0, 0, 220), dialogue_rect)
                pygame.draw.rect(self.display_surface, (255, 215, 0), dialogue_rect, 4)  # Gold border
                
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
                y_offset = dialogue_rect.y + 15
                # More lines for intro and story dialogues with controls
                max_lines = 6 if self.show_intro_dialogue else 8 if self.story_dialogue_active else 3
                for i, line in enumerate(lines[:max_lines]):
                    # Style controls differently
                    if (self.show_intro_dialogue and line in ["CONTROLS:", "Arrow Keys - Move Left/Right", "SPACE - Jump", "F - Attack with Sword"]) or \
                       (self.story_dialogue_active and line in ["HEART CONTROLS:", "BOW CONTROLS:", "I - Open/Close Inventory", "1-0 - Select Heart Slot", "W - Use Selected Heart", "E - Switch Sword/Bow", "F - Fire Arrow (when bow selected)", "Arrow Keys - Aim Direction"]):
                        if line in ["CONTROLS:", "HEART CONTROLS:", "BOW CONTROLS:"]:
                            text_color = (255, 215, 0)  # Gold for title
                        else:
                            text_color = (200, 255, 200)  # Light green for controls
                    else:
                        text_color = (255, 255, 255)  # White for regular text
                    
                    text_surface = font.render(line, True, text_color)
                    text_rect = text_surface.get_rect(centerx=dialogue_rect.centerx, y=y_offset)
                    self.display_surface.blit(text_surface, text_rect)
                    y_offset += 25
                
                # Draw continue prompt
                if self.show_intro_dialogue:
                    continue_text = font.render("Press R to begin", True, (255, 215, 0))
                else:
                    continue_text = font.render("Press R, Z, or ENTER to continue", True, (200, 200, 200))
                continue_rect = continue_text.get_rect(centerx=dialogue_rect.centerx, y=dialogue_rect.bottom - 25)
                self.display_surface.blit(continue_text, continue_rect)
            return
        
        # Draw interaction prompt
        if self.show_interaction_prompt:
            prompt_text = font.render("Press Q to interact", True, (255, 255, 255))
            prompt_rect = prompt_text.get_rect(center=(WIDTH // 2, HEIGHT - 100))
            
            # Draw background for prompt
            bg_rect = prompt_rect.inflate(20, 10)
            pygame.draw.rect(self.display_surface, (0, 0, 0, 150), bg_rect)
            pygame.draw.rect(self.display_surface, (255, 255, 255), bg_rect, 2)
            
            self.display_surface.blit(prompt_text, prompt_rect)
        
        # Draw regular dialogue
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

    def initialize_game_data(self):
        """Initialize all game data through API"""
        if self.game_data_initialized:
            return
            
        try:
            # Initialize all game data through API
            init_result = self.api_client.initialize_game_data()
            
            if init_result["success"]:
                self.api_connected = True
                self.player_data_synced = True
                self.game_data_initialized = True
                self.player_progress = init_result
                print("✅ Game data initialized successfully")
            else:
                self.api_connected = False
                print(f"❌ Failed to initialize game data: {init_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.api_connected = False
            print(f"❌ Unexpected error initializing game data: {e}")
    
    def save_game_session(self):
        """Save complete game session through API"""
        if not self.api_connected or self.score_saved:
            return
            
        try:
            # Calculate survival time in seconds
            survival_time = (pygame.time.get_ticks() - self.start_time) / 1000.0 if self.start_time > 0 else 0
            
            # Prepare comprehensive score data
            score_data = {
                "score_value": self.score,
                "time_played": survival_time,
                "enemies_killed": self.enemies_hit,
                "max_combo": self.max_combo,
                "survival_time": survival_time
            }
            
            # Calculate currency reward based on score
            currency_result = self.api_client.calculate_currency(self.score)
            if currency_result.get("currency_earned", 0) > 0:
                print(f"💰 Earned {currency_result['currency_earned']} coins! ({currency_result['rule_applied']})")
                self.currency_earned = currency_result['currency_earned']
                self.currency_rule = currency_result['rule_applied']
            else:
                print(f"💰 No currency earned: {currency_result.get('message', 'Unknown reason')}")
                self.currency_earned = 0
                self.currency_rule = None
            
            # Save complete game session
            save_result = self.api_client.save_game_session(score_data)
            
            if save_result["success"]:
                self.score_saved = True
                print(f"✅ Game session saved successfully")
            else:
                print(f"❌ Failed to save game session: {save_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Unexpected error saving game session: {e}")
    
    def get_leaderboard_data(self, limit=10):
        """Get leaderboard data from API"""
        if not self.api_connected:
            return []
            
        try:
            return self.api_client.get_leaderboard(limit=limit)
        except Exception as e:
            print(f"❌ Failed to get leaderboard: {e}")
            return []
    
    def get_player_progress(self):
        """Get comprehensive player progress from API"""
        if not self.api_connected:
            return None
            
        try:
            return self.api_client.get_player_progress()
        except Exception as e:
            print(f"❌ Failed to get player progress: {e}")
            return None
    
    def update_player_data(self, player_data=None, game_settings=None):
        """Update player data through API"""
        if not self.api_connected:
            return False
            
        try:
            result = self.api_client.create_or_update_player(player_data, game_settings)
            if result:
                print("✅ Player data updated successfully")
                return True
            return False
        except Exception as e:
            print(f"❌ Failed to update player data: {e}")
            return False

    def run(self, keys, collision_sprites):
        #run whole game(level)
        
        # Auto-sync player data periodically (every 5 seconds)
        if not hasattr(self, 'last_sync_time'):
            self.last_sync_time = 0
        current_time = pygame.time.get_ticks()
        if current_time - self.last_sync_time > 5000:  # 5 seconds
            if self.api_connected:
                sync_result = self.api_client.auto_sync_player_data()
                if sync_result["success"]:
                    print("🔄 Auto-sync completed during gameplay")
                else:
                    print(f"❌ Auto-sync failed during gameplay: {sync_result.get('error', 'Unknown error')}")
            self.last_sync_time = current_time
        
        # Update survival time and UI animations
        self.update_survival_time()
        self.update_ui_animations()
        
        # Check if game is over
        if self.player.health <= 0:
            self.game_over = True
            # Save complete game session when game over
            self.save_game_session()
            # Don't show story dialogue during death screen - it will be shown after restart
            # Don't return here - let the game over screen be drawn
        
        # Update player with proper argumentalsono 
        # Check if any dialogue is active
        dialogue_active = self.show_intro_dialogue or self.story_dialogue_active
        self.player.update(keys, collision_sprites, self.enemy_sprite, dialogue_active)
        
        # Update player's story progression abilities
        self.player.update_story_progression()
        
        # Sync inventory with story progress for real-time updates
        self.player.sync_inventory_from_story_progress()
        
        # Update enemies
        for enemy in self.enemies:
            if hasattr(enemy, 'update') and enemy.__class__.__name__ == 'SlimeEnemy':
                enemy.update(self.player, collision_sprites, self)
            else:
                enemy.update(self.player, collision_sprites)
        
        # Update animated objects
        for animated_obj in self.animated_objects:
            animated_obj.update(self.player, self)
        
        # Spawn enemies if less than max
        self.spawn_enemies_if_needed()
        
        # Check collisions
        self.check_projectile_collisions()
        self.check_attack_collisions()
        # Check if any dialogue is active
        dialogue_active = self.show_intro_dialogue or self.story_dialogue_active
        self.check_enemy_attack_collisions(dialogue_active)
        self.check_heart_collisions()
        
        # Update bow and check bow attacks and arrow collisions
        self.bow.update(self.player.rect, self.player.facing_right, self.player.attacking)
        self.check_bow_attacks()
        self.check_arrow_collisions()
        
        # Check interactions
        self.check_interactions(keys)
        
        # Check for map transition
        self.check_map_transition()
        
        # Check for win condition
        self.check_win_condition()
        
        # Update map transition
        self.update_map_transition()
        
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
        
        # Draw hearts only if hearts are unlocked
        if self.player.can_use_hearts:
            for heart in self.hearts:
                if not heart.collected:
                    screen_pos = self.camera.apply(heart)
                    heart.draw(self.display_surface, screen_pos)
        
        # Draw animated objects (only if visible)
        for animated_obj in self.animated_objects:
            if animated_obj.visible:
                screen_pos = self.camera.apply(animated_obj)
                self.display_surface.blit(animated_obj.image, screen_pos)
                
                # Draw health bar above animated object
                if animated_obj.is_alive:
                    self.draw_animated_object_health_bar(animated_obj, screen_pos)
        
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
        
        # Weapon animation is handled by the player sprite itself
        
        # Draw sunrise character (only during daytime)
        self.draw_sunrise_character()
        
        # Draw UI elements
        self.draw_ui()
        
        # Draw game stats
        self.draw_game_stats()
        
        # Draw score popups
        self.draw_score_popups()
        
        # Draw inventory UI only if hearts are unlocked
        if self.player.can_use_hearts:
            self.player.draw_inventory(self.display_surface)
        
        # Draw map transition effect
        self.draw_map_transition()
        
        # Draw player arrows
        if len(self.player_arrows) > 0:
            print(f"🎯 DRAWING {len(self.player_arrows)} arrows")
            for arrow in self.player_arrows:
                print(f"🎯 Drawing arrow at {arrow.rect}")
                arrow.draw(self.display_surface, self.camera)
        else:
            print(f"🎯 NO ARROWS TO DRAW")
        
        # Draw game over screen on top of everything
        if self.game_over:
            self.draw_game_over_screen()
        
        # Draw win screen on top of everything
        if self.game_won:
            self.draw_win_screen()
        
    def draw_game_stats(self):
        """Draw modern game statistics UI"""
        # UI Constants
        UI_PADDING = 20
        UI_BG_ALPHA = 180
        UI_CORNER_RADIUS = 8
        
        # Create semi-transparent background panels
        panel_bg = pygame.Surface((300, 150), pygame.SRCALPHA)
        pygame.draw.rect(panel_bg, (0, 0, 0, UI_BG_ALPHA), (0, 0, 300, 150), border_radius=UI_CORNER_RADIUS)
        
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
        
        # Weapon display - positioned below combo to fit within panel
        weapon_text = font_medium.render("WEAPON", True, (200, 200, 200))
        self.display_surface.blit(weapon_text, (left_x, left_y + 100))
        
        # Weapon type with color coding
        current_weapon = self.player.get_current_weapon()
        if current_weapon == 'bow':
            weapon_name = "Bow & Arrow"
            weapon_color = (100, 200, 255)  # Blue for ranged weapon
        else:
            weapon_name = "Sword"
            weapon_color = (255, 200, 100)  # Orange for melee weapon
        
        weapon_value = font_small.render(weapon_name, True, weapon_color)
        self.display_surface.blit(weapon_value, (left_x, left_y + 120))
        
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
        
        # Enemies Alive - REMOVED from UI
        
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
        
        you_died_text = font_medium.render("Luna Has Fallen...", True, (255, 255, 255))
        you_died_rect = you_died_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 60))
        self.display_surface.blit(you_died_text, you_died_rect)
        
        learning_text = font_small.render("But each fall teaches her something new...", True, (200, 200, 200))
        learning_rect = learning_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 20))
        self.display_surface.blit(learning_text, learning_rect)
        
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
        
        # Enemies killed - REMOVED from end screen
        
        # Max combo
        combo_text = font_small.render(f"Max Combo: {score_breakdown['max_combo']}x", True, (255, 100, 100))
        combo_rect = combo_text.get_rect(center=(WIDTH//2, stats_y + stats_spacing))
        self.display_surface.blit(combo_text, combo_rect)
        
        # Restart instruction with more space
        restart_text = font_small.render("Press R for Luna to try again or ESC to exit", True, (200, 200, 200))
        restart_rect = restart_text.get_rect(center=(WIDTH//2, stats_y + stats_spacing * 2 + 20))
        self.display_surface.blit(restart_text, restart_rect)
        
        # Add blinking effect for restart instruction
        import time
        if int(time.time() * 2) % 2:  # Blink every 0.5 seconds
            restart_text = font_small.render("Press R for Luna to try again or ESC to exit", True, (255, 255, 255))
            self.display_surface.blit(restart_text, restart_rect)
        
        # Currency and API Status
        api_y = stats_y + stats_spacing * 4 + 40
        
        # Currency earned display
        if self.currency_earned > 0:
            currency_text = font_medium.render(f"💰 +{self.currency_earned} Coins Earned!", True, (255, 215, 0))
            currency_rect = currency_text.get_rect(center=(WIDTH//2, api_y))
            self.display_surface.blit(currency_text, currency_rect)
            
            if self.currency_rule:
                rule_text = font_small.render(f"({self.currency_rule})", True, (200, 200, 200))
                rule_rect = rule_text.get_rect(center=(WIDTH//2, api_y + 30))
                self.display_surface.blit(rule_text, rule_rect)
        else:
            no_currency_text = font_small.render("No coins earned this round", True, (150, 150, 150))
            no_currency_rect = no_currency_text.get_rect(center=(WIDTH//2, api_y))
            self.display_surface.blit(no_currency_text, no_currency_rect)
        
        # API Connection Status
        api_status_y = api_y + 60
        if self.api_connected:
            api_status_text = font_small.render("✓ Score and currency saved", True, (100, 255, 100))
        else:
            api_status_text = font_small.render("✗ Offline mode - data not saved", True, (255, 100, 100))
        
        api_status_rect = api_status_text.get_rect(center=(WIDTH//2, api_status_y))
        self.display_surface.blit(api_status_text, api_status_rect)

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

    def draw_win_screen(self):
        """Draw win screen when player completes the night map"""
        # Create semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(120)
        overlay.fill((0, 0, 0))
        self.display_surface.blit(overlay, (0, 0))
        
        # Draw win text with smaller fonts
        font_large = pygame.font.Font(None, 80)
        font_medium = pygame.font.Font(None, 48)
        font_small = pygame.font.Font(None, 36)
        
        # Main win text with outline
        win_text = font_large.render("VICTORY!", True, (255, 215, 0))
        win_rect = win_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 120))
        
        # Draw outline
        outline_color = (0, 0, 0)
        for dx in [-2, 0, 2]:
            for dy in [-2, 0, 2]:
                if dx != 0 or dy != 0:
                    outline_rect = win_text.get_rect(center=(WIDTH//2 + dx, HEIGHT//2 - 120 + dy))
                    outline_surface = font_large.render("VICTORY!", True, outline_color)
                    self.display_surface.blit(outline_surface, outline_rect)
        
        self.display_surface.blit(win_text, win_rect)
        
        # Congratulations text
        congrats_text = font_medium.render("Luna has completed her endless lesson!", True, (255, 255, 255))
        congrats_rect = congrats_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 60))
        self.display_surface.blit(congrats_text, congrats_rect)
        
        # Score breakdown
        score_breakdown = self.get_score_breakdown()
        
        # Final Score
        final_score_text = font_medium.render(f"FINAL SCORE: {self.score:,}", True, (255, 215, 0))
        final_score_rect = final_score_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 10))
        self.display_surface.blit(final_score_text, final_score_rect)
        
        # Stats grid
        stats_y = HEIGHT//2 + 40
        stats_spacing = 40
        
        # Time survived
        time_text = font_small.render(f"Time Survived: {score_breakdown['survival_time']}s", True, (100, 255, 100))
        time_rect = time_text.get_rect(center=(WIDTH//2, stats_y))
        self.display_surface.blit(time_text, time_rect)
        
        # Enemies killed - REMOVED from end screen
        
        # Max combo
        combo_text = font_small.render(f"Max Combo: {score_breakdown['max_combo']}x", True, (255, 100, 100))
        combo_rect = combo_text.get_rect(center=(WIDTH//2, stats_y + stats_spacing))
        self.display_surface.blit(combo_text, combo_rect)
        
        # Restart instruction
        restart_text = font_small.render("Press R to play again or ESC to exit", True, (200, 200, 200))
        restart_rect = restart_text.get_rect(center=(WIDTH//2, stats_y + stats_spacing * 2 + 20))
        self.display_surface.blit(restart_text, restart_rect)
        
        # Add blinking effect for restart instruction
        import time
        if int(time.time() * 2) % 2:  # Blink every 0.5 seconds
            restart_text = font_small.render("Press R to play again or ESC to exit", True, (255, 255, 255))
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
        should_spawn = ((self.enemy_spawn_timer >= self.enemy_spawn_delay) or (alive_enemies < 2)) and (alive_enemies < 5)
        
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
                # Spawn enemies all over the map instead of just near player
                # Map width is typically 3200 pixels (100 tiles * 32px), spawn across entire width
                spawn_x = random.randint(100, 3100)  # Spawn across entire map width
                
                # Ground is from 0 to 96 pixels from bottom, so spawn enemies above ground
                # Spawn enemies at Y position 520
                spawn_y = 520  # Fixed Y position above ground
                
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

    def draw_animated_object_health_bar(self, animated_obj, screen_pos):
        """Draw health bar above animated object"""
        if not hasattr(animated_obj, 'health') or not hasattr(animated_obj, 'max_health'):
            return
        
        # Health bar dimensions
        bar_width = 60
        bar_height = 8
        bar_x = screen_pos[0] + (animated_obj.rect.width - bar_width) // 2
        bar_y = screen_pos[1] - 15  # 15 pixels above the object
        
        # Background (red)
        background_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(self.display_surface, (255, 0, 0), background_rect)
        
        # Health (green)
        health_percentage = animated_obj.health / animated_obj.max_health
        health_width = int(bar_width * health_percentage)
        if health_width > 0:
            health_rect = pygame.Rect(bar_x, bar_y, health_width, bar_height)
            pygame.draw.rect(self.display_surface, (0, 255, 0), health_rect)
        
        # Border (white)
        border_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(self.display_surface, (255, 255, 255), border_rect, 1)

    def get_collision_sprites(self):
        return self.collision_sprite




