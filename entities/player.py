import pygame
from entities.gun import Gun
from config import *

# player.py


# player.py


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

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
                attack2_sheet.subsurface(pygame.Rect(i * attack2_frame_w, 0, attack2_frame_h, attack2_frame_h - CROP_HEIGHT_ATTACK_2)),
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
        
        # Health system
        self.max_health = 100
        self.health = self.max_health
        self.is_alive = True
        self.invulnerable = False
        self.invulnerability_timer = 0

    def check_collision(self, dx, dy, collision_sprites):
        """Advanced collision detection that handles edge cases"""
        # Create a test rect for collision detection using the smaller collision box
        test_rect = self.collision_rect.copy()
        test_rect.centerx = self.rect.centerx + dx
        test_rect.bottom = self.rect.bottom + dy
        
        # Check for collisions
        for sprite in collision_sprites:
            if test_rect.colliderect(sprite.rect):
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

    def update(self, keys, collision_sprites, enemy_sprites=None):
        dx = 0
        self.walking = False

        # Only allow movement, direction changes, and jumping if not attacking
        if not self.attacking:
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

            if keys[pygame.K_f]:
                self.attacking = True
                self.attack_index = 0

        self.vel_y += GRAVITY
        dy = self.vel_y
        current_bottom = self.rect.bottom

        if self.attacking:
            self.attack_index += 0.2
            if self.attack_index >= len(self.current_attack_frames_right):
                self.attacking = False
                self.attack_index = 0

            current_frame = self.current_attack_frames_right[int(self.attack_index)] if self.facing_right else self.current_attack_frames_left[int(self.attack_index)]
            
            # Check for attack collisions with enemies
            self.check_attack_collision(enemy_sprites)

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
    
    def take_damage(self, damage):
        """Take damage and check if player dies"""
        if self.invulnerable or not self.is_alive:
            return False
            
        self.health -= damage
        self.invulnerable = True
        self.invulnerability_timer = 60  # 1 second of invulnerability
        
        if self.health <= 0:
            self.health = 0
            self.is_alive = False
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
