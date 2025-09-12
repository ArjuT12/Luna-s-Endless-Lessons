import pygame
from entities.bow import Bow
from entities.inventory import Inventory
from story_progression import StoryProgression
from config import *

# player.py


# player.py


class Player(pygame.sprite.Sprite):
    def __init__(self, story_progression=None):
        super().__init__()
        
        # Story progression system
        self.story_progression = story_progression or StoryProgression()

        # Load and scale sprite sheets (unchanged from previous)
        walk_sheet = pygame.image.load("Soldier-Walk.png").convert_alpha()
        attack1_sheet = pygame.image.load("Soldier-Attack01.png").convert_alpha()
        attack2_sheet = pygame.image.load("Soldier-Attack03.png").convert_alpha()

        walk_frame_w = walk_sheet.get_width() // 8
        walk_frame_h = walk_sheet.get_height()
        walk_frames = [
            pygame.transform.scale(
                walk_sheet.subsurface(pygame.Rect(i * walk_frame_w, 0, walk_frame_w, walk_frame_h - CROP_HEIGHT_WALK)),
                (walk_frame_w * SCALE, (walk_frame_h - CROP_HEIGHT_WALK) * SCALE)
            )
            for i in range(8)
        ]

        attack1_frame_w = attack1_sheet.get_width() // 6
        attack1_frame_h = attack1_sheet.get_height()
        attack1_frames = [
            pygame.transform.scale(
                attack1_sheet.subsurface(pygame.Rect(i * attack1_frame_w, 0, attack1_frame_w, attack1_frame_h - CROP_HEIGHT_ATTACK_1)),
                (attack1_frame_w * SCALE, (attack1_frame_h - CROP_HEIGHT_ATTACK_1) * SCALE)
            )
            for i in range(6)
        ]


        attack2_frame_w = attack2_sheet.get_width() // 9
        attack2_frame_h = attack2_sheet.get_height()
        attack2_frames = [
            pygame.transform.scale(
                attack2_sheet.subsurface(pygame.Rect(i * attack2_frame_w, 0, attack2_frame_w, attack2_frame_h - CROP_HEIGHT_ATTACK_2)),
                (attack2_frame_w * SCALE, (attack2_frame_h - CROP_HEIGHT_ATTACK_2) * SCALE)
            )
            for i in range(9)
        ]

        self.walk_frames_right = walk_frames
        self.walk_frames_left = [pygame.transform.flip(f, True, False) for f in self.walk_frames_right]

        self.attack1_frames_right = attack1_frames
        self.attack1_frames_left = [pygame.transform.flip(f, True, False) for f in self.attack1_frames_right]

        self.attack2_frames_right = attack2_frames
        self.attack2_frames_left = [pygame.transform.flip(f, True, False) for f in self.attack2_frames_right]

        self.current_attack_frames_right = self.attack1_frames_right
        self.current_attack_frames_left = self.attack1_frames_left

        self.index = 0
        self.image = self.walk_frames_right[0]
        self.rect = self.image.get_rect()  # Don't set position here, let level setup handle it
        
        # Create a smaller collision box for more precise collision detection
        self.collision_rect = pygame.Rect(0, 0, 24, self.rect.height)  # 24px wide collision box

        self.vel_y = 0
        self.on_ground = True
        self.facing_right = True
        self.walking = False
        self.attacking = False
        self.attack_index = 0
        self.weapon_switched = False
        
        # Weapon system - start with only sword, unlock bow through story progression
        self.current_weapon = 'sword'  # 'sword', 'bow'
        self.weapon_switch_cooldown = 0
        self.can_use_bow = self.story_progression.can_use_bow()
        
        # Ensure player starts with sword if bow is not unlocked
        if not self.can_use_bow:
            self.current_weapon = 'sword'
        
        # Health system
        self.max_health = 100
        self.health = self.max_health
        self.is_alive = True
        self.invulnerable = False
        self.invulnerability_timer = 0
        
        # Inventory system - start empty, unlock hearts through story progression
        self.inventory = Inventory()
        self.inventory_toggle_cooldown = 0
        self.heart_use_cooldown = 0
        
        self.can_use_hearts = self.story_progression.can_use_hearts()
        
        # Load saved inventory if hearts are unlocked
        if self.can_use_hearts:
            saved_inventory = self.story_progression.load_inventory()
            self.inventory.items = saved_inventory.copy()
            print(f"Loaded inventory: {saved_inventory}")
            
            # Add initial hearts only if inventory is empty (first time unlocking)
            if len(self.inventory.items) == 0:
                self.inventory.add_item('heart', 3)  # Start with 3 hearts

    def check_collision(self, dx, dy, collision_sprites):
        """Advanced collision detection that handles edge cases and platform tiles"""
        # Create a test rect for collision detection using the smaller collision box
        test_rect = self.collision_rect.copy()
        test_rect.centerx = self.rect.centerx + dx
        test_rect.bottom = self.rect.bottom + dy
        
        # Check for collisions
        for sprite in collision_sprites:
            if test_rect.colliderect(sprite.rect):
                # Check if this is a platform tile
                if hasattr(sprite, 'is_platform') and sprite.is_platform:
                    # For platform tiles, only allow collision from above (falling down)
                    if dy > 0:  # Player is falling down
                        # Pixel-perfect collision: player's bottom must be at or above platform's top
                        if self.rect.bottom <= sprite.rect.top:
                            return True, sprite
                    # If player is moving up or horizontally, ignore platform collision
                    continue
                else:
                    # Regular solid tile collision
                    return True, sprite
        return False, None
    
    def check_attack_collision(self, enemy_sprites):
        """Check if the sword attack hits any enemies"""
        if not self.attacking or not enemy_sprites:
            return
        
        # Create attack hitbox based on attack frame and direction
        attack_frame = int(self.attack_index)
        
        if attack_frame >= len(self.current_attack_frames_right):
            return
        
        # Create a hitbox for the sword attack
        # The hitbox extends in front of the player based on direction
        hitbox_width = 60  # Width of the attack hitbox
        hitbox_height = 60  # Height of the attack hitbox
        
        if self.facing_right:
            # Attack hitbox extends to the right
            hitbox_x = self.rect.centerx  # Start at player center
            hitbox_y = self.rect.centery - hitbox_height // 2
        else:
            # Attack hitbox extends to the left
            hitbox_x = self.rect.centerx - hitbox_width  # Start at player center
            hitbox_y = self.rect.centery - hitbox_height // 2
        
        attack_hitbox = pygame.Rect(hitbox_x, hitbox_y, hitbox_width, hitbox_height)
        
        # Check collision with enemy tiles
        for enemy in enemy_sprites:
            if hasattr(enemy, 'tile_id') and enemy.tile_id in [41, 42]:  # Check if it's an enemy tile
                if attack_hitbox.colliderect(enemy.rect):
                    print(f"ATTACK HIT! Enemy tile ID {enemy.tile_id} at position ({enemy.rect.x}, {enemy.rect.y})")
                    # You can add more logic here like removing the enemy, dealing damage, etc.

    def update(self, keys, collision_sprites, enemy_sprites=None, dialogue_active=False):
        dx = 0
        self.walking = False

        # Update weapon switch cooldown
        if self.weapon_switch_cooldown > 0:
            self.weapon_switch_cooldown -= 1
        
        # Update inventory and heart use cooldowns
        if self.inventory_toggle_cooldown > 0:
            self.inventory_toggle_cooldown -= 1
        if self.heart_use_cooldown > 0:
            self.heart_use_cooldown -= 1
        
        # Update inventory state
        self.inventory.update()

        # Only allow movement, direction changes, and jumping if not attacking, not in inventory navigation mode, and not in dialogue
        if not self.attacking and not self.inventory.is_open and not dialogue_active:
            # Debug: print when movement is enabled
            if keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]:
                print(f"Movement enabled. Inventory open: {self.inventory.is_open}")
            if keys[pygame.K_RIGHT]:
                dx = 4
                self.facing_right = True
                self.walking = True
            elif keys[pygame.K_LEFT]:
                dx = -4
                self.facing_right = False
                self.walking = True

            if keys[pygame.K_SPACE] and self.on_ground:
                self.vel_y = -JUMP_STRENGTH
                self.on_ground = False

            # Weapon switching (E key) - only if bow is unlocked
            if keys[pygame.K_e] and self.weapon_switch_cooldown <= 0 and self.can_use_bow:
                if self.current_weapon == 'sword':
                    self.current_weapon = 'bow'
                    self.current_attack_frames_right = self.attack2_frames_right
                    self.current_attack_frames_left = self.attack2_frames_left
                    print("Switched to BOW weapon")
                else:
                    self.current_weapon = 'sword'
                    self.current_attack_frames_right = self.attack1_frames_right
                    self.current_attack_frames_left = self.attack1_frames_left
                    print("Switched to SWORD weapon")
                self.weapon_switch_cooldown = 30
            elif keys[pygame.K_e] and not self.can_use_bow:
                print("Bow not yet unlocked! Die to progress the story...")

            if keys[pygame.K_f]:
                # Only allow attacking if current weapon is available
                if self.current_weapon == 'sword' or (self.current_weapon == 'bow' and self.can_use_bow):
                    self.attacking = True
                    self.attack_index = 0
                elif self.current_weapon == 'bow' and not self.can_use_bow:
                    print("Bow not yet unlocked! Die to progress the story...")
            
            # Enter inventory navigation (I key) - only when not in navigation mode and hearts unlocked
            if keys[pygame.K_i] and self.inventory_toggle_cooldown <= 0 and self.can_use_hearts:
                if not self.inventory.is_open:
                    self.inventory.is_open = True
                    print("Entered inventory navigation mode")
                    self.inventory_toggle_cooldown = 5  # 5 frames cooldown
            elif keys[pygame.K_i] and not self.can_use_hearts:
                print("Inventory not yet unlocked! Die to progress the story...")
            
            # Select items with number keys (1-0) - only when not in navigation mode and hearts unlocked
            if not self.inventory.is_open and self.can_use_hearts:
                if keys[pygame.K_1] and self.inventory_toggle_cooldown <= 0:
                    self.inventory.highlight_slot(0)
                    print("Highlighted slot 1")
                    self.inventory_toggle_cooldown = 5
                elif keys[pygame.K_2] and self.inventory_toggle_cooldown <= 0:
                    self.inventory.highlight_slot(1)
                    print("Highlighted slot 2")
                    self.inventory_toggle_cooldown = 5
                elif keys[pygame.K_3] and self.inventory_toggle_cooldown <= 0:
                    self.inventory.highlight_slot(2)
                    print("Highlighted slot 3")
                    self.inventory_toggle_cooldown = 5
                elif keys[pygame.K_4] and self.inventory_toggle_cooldown <= 0:
                    self.inventory.highlight_slot(3)
                    print("Highlighted slot 4")
                    self.inventory_toggle_cooldown = 5
                elif keys[pygame.K_5] and self.inventory_toggle_cooldown <= 0:
                    self.inventory.highlight_slot(4)
                    print("Highlighted slot 5")
                    self.inventory_toggle_cooldown = 5
                elif keys[pygame.K_6] and self.inventory_toggle_cooldown <= 0:
                    self.inventory.highlight_slot(5)
                    print("Highlighted slot 6")
                    self.inventory_toggle_cooldown = 5
                elif keys[pygame.K_7] and self.inventory_toggle_cooldown <= 0:
                    self.inventory.highlight_slot(6)
                    print("Highlighted slot 7")
                    self.inventory_toggle_cooldown = 5
                elif keys[pygame.K_8] and self.inventory_toggle_cooldown <= 0:
                    self.inventory.highlight_slot(7)
                    print("Highlighted slot 8")
                    self.inventory_toggle_cooldown = 5
                elif keys[pygame.K_9] and self.inventory_toggle_cooldown <= 0:
                    self.inventory.highlight_slot(8)
                    print("Highlighted slot 9")
                    self.inventory_toggle_cooldown = 5
                elif keys[pygame.K_0] and self.inventory_toggle_cooldown <= 0:
                    self.inventory.highlight_slot(9)
                    print("Highlighted slot 0")
                    self.inventory_toggle_cooldown = 5
            
        # Inventory navigation when open (works even when movement is disabled)
        if self.inventory.is_open:
            # Exit inventory navigation (U key)
            if keys[pygame.K_u] and self.inventory_toggle_cooldown <= 0:
                self.inventory.is_open = False
                print("Exited inventory navigation mode")
                self.inventory_toggle_cooldown = 5  # 5 frames cooldown
            
            if keys[pygame.K_LEFT] and self.inventory_toggle_cooldown <= 0:
                self.inventory.select_previous_slot()
                self.inventory_toggle_cooldown = 5
            elif keys[pygame.K_RIGHT] and self.inventory_toggle_cooldown <= 0:
                self.inventory.select_next_slot()
                self.inventory_toggle_cooldown = 5
            elif keys[pygame.K_w] and self.heart_use_cooldown <= 0 and self.can_use_hearts:
                self.use_selected_item()
                self.heart_use_cooldown = 10
        
        # Use highlighted item with W key (works in both modes) - only if hearts unlocked
        if keys[pygame.K_w] and self.heart_use_cooldown <= 0 and self.can_use_hearts:
            self.use_highlighted_item()
            self.heart_use_cooldown = 10
        elif keys[pygame.K_w] and not self.can_use_hearts:
            print("Hearts not yet unlocked! Die to progress the story...")

        self.vel_y += GRAVITY
        dy = self.vel_y
        current_bottom = self.rect.bottom

        if self.attacking:
            # Different attack speeds for different weapons
            if self.current_weapon == 'sword':
                self.attack_index += 0.2
                if self.attack_index >= len(self.current_attack_frames_right):
                    self.attacking = False
                    self.attack_index = 0
                current_frame = self.current_attack_frames_right[int(self.attack_index)] if self.facing_right else self.current_attack_frames_left[int(self.attack_index)]
                
                # Check for sword attack collisions with enemies
                self.check_attack_collision(enemy_sprites)
            else:
                # For ranged weapons, use full animation
                self.attack_index += 0.2
                if self.attack_index >= len(self.current_attack_frames_right):
                    self.attacking = False
                    self.attack_index = 0
                current_frame = self.current_attack_frames_right[int(self.attack_index)] if self.facing_right else self.current_attack_frames_left[int(self.attack_index)]

        elif self.walking and self.on_ground:
            self.index += 0.2
            if self.index >= len(self.walk_frames_right):
                self.index = 0
            current_frame = self.walk_frames_right[int(self.index)] if self.facing_right else self.walk_frames_left[int(self.index)]

        else:
            self.index = 0
            current_frame = self.walk_frames_right[int(self.index)] if self.facing_right else self.walk_frames_left[int(self.index)]

        old_centerx = self.rect.centerx
        self.image = current_frame
        self.rect = self.image.get_rect(midbottom=(old_centerx, current_bottom))
        
        # Update collision box position to match player position
        self.collision_rect.centerx = self.rect.centerx
        self.collision_rect.bottom = self.rect.bottom

        # Store original position for collision detection
        old_rect = self.rect.copy()
        
        # Horizontal movement with perfect collision detection
        if dx != 0:
            # Check horizontal collision before moving
            collision, collided_sprite = self.check_collision(dx, 0, collision_sprites)
            if collision:
                if dx > 0:  # Moving right
                    # Position player so collision box touches the tile
                    self.rect.right = collided_sprite.rect.left + (self.rect.width - self.collision_rect.width) // 2
                elif dx < 0:  # Moving left
                    # Position player so collision box touches the tile
                    self.rect.left = collided_sprite.rect.right - (self.rect.width - self.collision_rect.width) // 2
            else:
                self.rect.centerx += dx
        
        # Prevent player from going outside map boundaries
        # Map is 100 tiles wide (3200 pixels), so boundaries are 0 to 3200
        # Player collision box is 24px wide, so keep player center within bounds
        if self.rect.centerx < 12:  # Half collision box width from left edge
            self.rect.centerx = 12
        elif self.rect.centerx > 3200 - 12:  # Half collision box width from right edge
            self.rect.centerx = 3200 - 12

        # Vertical movement with perfect collision detection
        if dy != 0:
            # Check vertical collision before moving
            collision, collided_sprite = self.check_collision(0, dy, collision_sprites)
            if collision:
                if dy > 0:  # Falling down (landing on top)
                    self.rect.bottom = collided_sprite.rect.top
                    self.on_ground = True
                    self.vel_y = 0
                elif dy < 0:  # Moving up (hitting ceiling)
                    self.rect.top = collided_sprite.rect.bottom
                    self.vel_y = 0
            else:
                self.rect.bottom += dy
                # Reset ground state if not colliding
                self.on_ground = False

        # Collision with ground (absolute world position) - only when falling down
        # Player feet should be at 97 pixels from bottom, so ground level = 640 - 97 = 543
        ground_level = HEIGHT - 97
        if self.rect.bottom >= ground_level and self.vel_y >= 0:  # Only when falling down or stationary
            self.rect.bottom = ground_level
            self.on_ground = True
            self.vel_y = 0
        
        # Update invulnerability timer
        if self.invulnerable:
            self.invulnerability_timer -= 1
            if self.invulnerability_timer <= 0:
                self.invulnerable = False
    
    def take_damage(self, damage, dialogue_active=False):
        """Take damage and check if player dies"""
        # Don't take damage during dialogue sequences
        if dialogue_active:
            return False
            
        if self.invulnerable or not self.is_alive:
            return False
            
        self.health -= damage
        self.invulnerable = True
        self.invulnerability_timer = 60  # 1 second of invulnerability
        
        if self.health <= 0:
            self.health = 0
            self.is_alive = False
            # Update story progression when player dies
            self.story_progression.player_died()
            return True  # Player died
        return False  # Player still alive
    
    def draw_health_bar(self, screen):
        """Draw health bar in top-left corner"""
        if self.health < self.max_health:
            # Health bar background
            bar_width = 200
            bar_height = 20
            bar_x = 10
            bar_y = 10
            
            pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
            
            # Health bar
            health_width = (self.health / self.max_health) * bar_width
            pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, health_width, bar_height))
            
            # Health text
            font = pygame.font.Font(None, 24)
            health_text = font.render(f"Health: {self.health}/{self.max_health}", True, (255, 255, 255))
            screen.blit(health_text, (bar_x, bar_y + 25))
    
    def get_current_weapon(self):
        """Get the current weapon type"""
        return self.current_weapon
    
    def is_ranged_weapon(self):
        """Check if current weapon is ranged"""
        return self.current_weapon == 'bow'
    
    def can_attack(self):
        """Check if player can attack (not already attacking)"""
        return not self.attacking
    
    def use_heart(self):
        """Use a heart from inventory to heal - only if hearts are unlocked"""
        if not self.can_use_hearts:
            print("Hearts not yet unlocked! Die to progress the story...")
            return
            
        if self.inventory.use_item('heart'):
            # Heal the player
            heal_amount = 50  # Same as heart heal amount
            old_health = self.health
            self.health = min(self.max_health, self.health + heal_amount)
            actual_heal = self.health - old_health
            print(f"Used heart! Healed {actual_heal} health. Current health: {self.health}/{self.max_health}")
            print(f"Hearts remaining in inventory: {self.inventory.get_item_quantity('heart')}")
            # Save inventory after using heart
            self.save_inventory()
        else:
            print("No hearts available in inventory!")
    
    def use_item_from_slot(self, slot_number):
        """Use item from specific slot (0-9)"""
        if 0 <= slot_number < len(self.inventory.items):
            item = self.inventory.items[slot_number]
            if item['type'] == 'heart':
                self.use_heart()
            else:
                print(f"Cannot use item type: {item['type']}")
        else:
            print(f"No item in slot {slot_number + 1}")
    
    def use_selected_item(self):
        """Use the currently selected item"""
        selected_item = self.inventory.get_selected_item()
        if selected_item:
            if selected_item['type'] == 'heart':
                self.use_heart()
            else:
                print(f"Cannot use item type: {selected_item['type']}")
        else:
            print("No item selected")
    
    def use_highlighted_item(self):
        """Use the highlighted item (from number key selection)"""
        if self.inventory.highlighted_slot >= 0 and self.inventory.highlighted_slot < len(self.inventory.items):
            item = self.inventory.items[self.inventory.highlighted_slot]
            if item['type'] == 'heart':
                slot_num = self.inventory.highlighted_slot + 1
                self.use_heart()
                # Keep the highlight so player can use the same item again
                print(f"Used heart from slot {slot_num}")
            else:
                print(f"Cannot use item type: {item['type']}")
        else:
            print("No item highlighted")
    
    def save_inventory(self):
        """Save current inventory to story progression"""
        if self.can_use_hearts:
            self.story_progression.save_inventory(self.inventory.items)
    
    def update_story_progression(self):
        """Update player abilities based on story progression"""
        self.can_use_hearts = self.story_progression.can_use_hearts()
        self.can_use_bow = self.story_progression.can_use_bow()
        
        # Add hearts if they just got unlocked
        if self.can_use_hearts and self.inventory.get_item_quantity('heart') == 0:
            self.inventory.add_item('heart', 3)  # Give 3 hearts when unlocked
            print("Hearts unlocked! Added 3 hearts to inventory.")
            # Save inventory after adding initial hearts
            self.save_inventory()
    
    def sync_inventory_from_story_progress(self):
        """Sync inventory with story progress file (for real-time updates)"""
        if self.can_use_hearts:
            # Reload story progression to get latest data
            self.story_progression.load_progress()
            
            # Get current inventory from story progress
            saved_inventory = self.story_progression.load_inventory()
            current_hearts = self.inventory.get_item_quantity('heart')
            saved_hearts = 0
            
            # Count hearts in saved inventory
            for item in saved_inventory:
                if item.get('type') == 'heart':
                    saved_hearts = item.get('quantity', 0)
                    break
            
            # Update inventory if there's a difference
            if saved_hearts != current_hearts:
                # Clear current heart items and set to exact amount from story progress
                # Remove all existing heart items
                self.inventory.items = [item for item in self.inventory.items if item.get('type') != 'heart']
                
                # Add the correct number of hearts from story progress
                if saved_hearts > 0:
                    self.inventory.add_item('heart', saved_hearts)
                    print(f"🔄 Synced {saved_hearts} hearts from story progress")
                
                # Don't save back to story progress here - let the game handle that
                # This prevents infinite sync loops
    
    def draw_inventory(self, screen):
        """Draw the inventory UI - always visible"""
        self.inventory.draw(screen)
