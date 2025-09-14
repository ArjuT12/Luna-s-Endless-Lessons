import pygame
import sys
import random
import math
from typing import Tuple, Optional, List
from settings import GameSettings
from api_client import LunaAPIClient

class ConfettiParticle:
    def __init__(self, x: int, y: int, screen_width: int, screen_height: int):
        self.x = x
        self.y = y
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Random confetti properties - pastel dots of various sizes
        self.size = random.randint(2, 6)  # Random size from 2-6 pixels (larger starting size)
        self.color = random.choice([
            (255, 182, 193),  # Light pink
            (255, 218, 185),  # Peach
            (255, 239, 213),  # Papaya whip
            (240, 248, 255),  # Alice blue
            (230, 230, 250),  # Lavender
            (255, 228, 225),  # Misty rose
            (240, 255, 240),  # Honeydew
            (255, 250, 240),  # Floral white
            (245, 245, 220),  # Beige
            (255, 255, 224),  # Light yellow
        ])
        
        # Physics - gentle shower (larger dots fall slower)
        self.velocity_x = random.uniform(-0.5, 0.5)  # Less horizontal movement
        self.velocity_y = random.uniform(0.5, 2) / (self.size * 0.5 + 0.5)  # Larger dots fall slower
        self.rotation = 0
        self.rotation_speed = random.uniform(-1, 1)  # Slower rotation
        self.gravity = 0.05 / (self.size * 0.3 + 0.7)  # Larger dots have less gravity
        
    def update(self):
        # Update position
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # Apply gravity
        self.velocity_y += self.gravity
        
        # Update rotation
        self.rotation += self.rotation_speed
        
        # Add gentle wind effect
        self.velocity_x += random.uniform(-0.02, 0.02)
        
        # Keep velocity within bounds
        self.velocity_x = max(-1, min(1, self.velocity_x))
        
    def draw(self, surface: pygame.Surface):
        # Draw dots of various sizes using circles for smooth appearance
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)
    
    def is_off_screen(self) -> bool:
        return (self.y > self.screen_height + 20 or 
                self.x < -20 or 
                self.x > self.screen_width + 20)

class StartScreen:
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.settings = GameSettings()
        self.api_client = LunaAPIClient()
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.GRAY = (128, 128, 128)
        self.LIGHT_GRAY = (200, 200, 200)
        self.DARK_GRAY = (64, 64, 64)
        self.BLUE = (0, 100, 200)
        self.LIGHT_BLUE = (100, 150, 255)
        self.GREEN = (0, 200, 0)
        self.RED = (200, 0, 0)
        
        # Fonts - using system fonts for better clarity
        pygame.font.init()
        try:
            # Try to use system fonts for better clarity (macOS compatible)
            font_names = ['Arial', 'Helvetica', 'Verdana', 'Tahoma', 'arial']
            font_found = False
            
            for font_name in font_names:
                try:
                    self.title_font = pygame.font.SysFont(font_name, 48, bold=True)
                    self.subtitle_font = pygame.font.SysFont(font_name, 32, bold=True)
                    self.text_font = pygame.font.SysFont(font_name, 26)
                    self.small_font = pygame.font.SysFont(font_name, 20)
                    font_found = True
                    break
                except:
                    continue
            
            if not font_found:
                raise Exception("No system fonts available")
                
        except:
            # Fallback to default font if system fonts not available
            self.title_font = pygame.font.Font(None, 48)
            self.subtitle_font = pygame.font.Font(None, 32)
            self.text_font = pygame.font.Font(None, 26)
            self.small_font = pygame.font.Font(None, 20)
        
        # Input fields for first-time setup
        self.first_name_input = ""
        self.last_name_input = ""
        self.game_name_input = ""
        self.active_input = "first_name"  # Which input field is active
        
        # Button states
        self.start_button_hover = False
        self.quit_button_hover = False
        self.submit_button_hover = False
        
        # Confetti system - gentle dot shower
        self.confetti_particles: List[ConfettiParticle] = []
        self.confetti_timer = 0
        self.confetti_spawn_rate = 60  # Spawn new confetti every 60 frames (slower)
        
        # Initial confetti burst
        self.initial_confetti_burst()
        
        # Input field rectangles (centered with proper spacing)
        input_width = 300
        input_height = 45
        input_spacing = 80
        start_y = screen_height // 2 - 120
        
        self.input_rects = {
            'first_name': pygame.Rect((screen_width - input_width) // 2, start_y, input_width, input_height),
            'last_name': pygame.Rect((screen_width - input_width) // 2, start_y + input_spacing, input_width, input_height),
            'game_name': pygame.Rect((screen_width - input_width) // 2, start_y + input_spacing * 2, input_width, input_height)
        }
        
        # Button rectangles (centered with proper spacing)
        button_width = 140
        button_height = 50
        button_spacing = 70
        button_start_y = start_y + input_spacing * 3 + 30
        
        self.button_rects = {
            'start': pygame.Rect((screen_width - button_width) // 2, button_start_y, button_width, button_height),
            'quit': pygame.Rect((screen_width - button_width) // 2, button_start_y + button_spacing, button_width, button_height),
            'submit': pygame.Rect((screen_width - button_width) // 2, button_start_y, button_width, button_height)
        }
    
    def initial_confetti_burst(self):
        """Create a gentle initial shower of small dots"""
        for _ in range(8):  # Much fewer initial dots
            x = random.randint(0, self.screen_width)
            y = random.randint(-20, 0)  # Start from just above screen
            self.confetti_particles.append(ConfettiParticle(x, y, self.screen_width, self.screen_height))
    
    def spawn_confetti(self):
        """Spawn new small dots for gentle shower"""
        # Spawn 1-2 small dots from the top of the screen
        for _ in range(random.randint(1, 2)):
            x = random.randint(0, self.screen_width)
            y = random.randint(-30, -10)  # Start above the screen
            self.confetti_particles.append(ConfettiParticle(x, y, self.screen_width, self.screen_height))
    
    def update_confetti(self):
        """Update all confetti particles"""
        # Update existing confetti
        for particle in self.confetti_particles[:]:  # Use slice to avoid modification during iteration
            particle.update()
            if particle.is_off_screen():
                self.confetti_particles.remove(particle)
        
        # Spawn new confetti
        self.confetti_timer += 1
        if self.confetti_timer >= self.confetti_spawn_rate:
            self.spawn_confetti()
            self.confetti_timer = 0
    
    def draw_confetti(self, surface: pygame.Surface):
        """Draw all confetti particles"""
        for particle in self.confetti_particles:
            particle.draw(surface)
    
    def draw_text(self, surface: pygame.Surface, text: str, font: pygame.font.Font, 
                  color: Tuple[int, int, int], x: int, y: int, center: bool = False) -> None:
        """Draw text on surface"""
        text_surface = font.render(text, True, color)
        if center:
            text_rect = text_surface.get_rect(center=(x, y))
            surface.blit(text_surface, text_rect)
        else:
            surface.blit(text_surface, (x, y))
    
    def draw_input_field(self, surface: pygame.Surface, rect: pygame.Rect, text: str, 
                        active: bool, label: str) -> None:
        """Draw an input field with label"""
        # Draw label with more spacing
        self.draw_text(surface, label, self.text_font, self.WHITE, rect.x, rect.y - 30)
        
        # Create semi-transparent surface for input field
        input_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        
        # Draw input field background with transparency
        if active:
            pygame.draw.rect(input_surface, (*self.LIGHT_BLUE, 180), (0, 0, rect.width, rect.height))
        else:
            pygame.draw.rect(input_surface, (255, 255, 255, 150), (0, 0, rect.width, rect.height))
        
        # Draw border
        pygame.draw.rect(input_surface, (*self.WHITE, 200), (0, 0, rect.width, rect.height), 2)
        
        # Blit the semi-transparent surface
        surface.blit(input_surface, rect)
        
        # Draw text in input field with better padding
        if text:
            text_surface = self.text_font.render(text, True, self.BLACK)
            surface.blit(text_surface, (rect.x + 12, rect.y + 12))
        
        # Draw cursor if active
        if active:
            cursor_x = rect.x + 12 + self.text_font.size(text)[0]
            pygame.draw.line(surface, self.BLACK, (cursor_x, rect.y + 15), (cursor_x, rect.y + 35), 2)
    
    def draw_button(self, surface: pygame.Surface, rect: pygame.Rect, text: str, 
                   hover: bool, color: Tuple[int, int, int] = None) -> None:
        """Draw a button"""
        if color is None:
            color = self.LIGHT_BLUE if hover else self.BLUE
        
        # Create semi-transparent surface for button
        button_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        
        # Draw button background with transparency
        if hover:
            pygame.draw.rect(button_surface, (*color, 200), (0, 0, rect.width, rect.height))
        else:
            pygame.draw.rect(button_surface, (*color, 180), (0, 0, rect.width, rect.height))
        
        # Draw border
        pygame.draw.rect(button_surface, (*self.WHITE, 220), (0, 0, rect.width, rect.height), 2)
        
        # Blit the semi-transparent surface
        surface.blit(button_surface, rect)
        
        # Draw button text
        self.draw_text(surface, text, self.text_font, self.WHITE, 
                      rect.centerx, rect.centery, center=True)
    
    def handle_input_event(self, event: pygame.event.Event) -> None:
        """Handle input events for text fields"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                # Cycle through input fields
                fields = ['first_name', 'last_name', 'game_name']
                current_index = fields.index(self.active_input)
                self.active_input = fields[(current_index + 1) % len(fields)]
            elif event.key == pygame.K_BACKSPACE:
                # Delete character
                if self.active_input == 'first_name':
                    self.first_name_input = self.first_name_input[:-1]
                elif self.active_input == 'last_name':
                    self.last_name_input = self.last_name_input[:-1]
                elif self.active_input == 'game_name':
                    self.game_name_input = self.game_name_input[:-1]
            else:
                # Add character
                if event.unicode.isprintable():
                    if self.active_input == 'first_name':
                        self.first_name_input += event.unicode
                    elif self.active_input == 'last_name':
                        self.last_name_input += event.unicode
                    elif self.active_input == 'game_name':
                        self.game_name_input += event.unicode
    
    def handle_mouse_click(self, pos: Tuple[int, int]) -> Optional[str]:
        """Handle mouse clicks and return action"""
        # Check input field clicks
        for field_name, rect in self.input_rects.items():
            if rect.collidepoint(pos):
                self.active_input = field_name
                return None
        
        # Check button clicks
        if self.settings.is_first_time_user():
            # First-time user buttons
            if self.button_rects['submit'].collidepoint(pos):
                if self.first_name_input.strip() and self.last_name_input.strip() and self.game_name_input.strip():
                    # Update local settings
                    self.settings.update_player_data(
                        self.first_name_input.strip(),
                        self.last_name_input.strip(),
                        self.game_name_input.strip()
                    )
                    
                    # Sync to database
                    try:
                        self.api_client.create_or_update_player()
                        print("✅ Player data synced to database successfully")
                    except Exception as e:
                        print(f"❌ Failed to sync player data to database: {e}")
                        # Continue anyway - local data is saved
                    
                    return "setup_complete"
        else:
            # Returning user buttons
            if self.button_rects['start'].collidepoint(pos):
                return "start_game"
            elif self.button_rects['quit'].collidepoint(pos):
                return "quit_game"
        
        return None
    
    def handle_mouse_motion(self, pos: Tuple[int, int]) -> None:
        """Handle mouse motion for hover effects"""
        if self.settings.is_first_time_user():
            self.submit_button_hover = self.button_rects['submit'].collidepoint(pos)
        else:
            self.start_button_hover = self.button_rects['start'].collidepoint(pos)
            self.quit_button_hover = self.button_rects['quit'].collidepoint(pos)
    
    def draw_first_time_setup(self, surface: pygame.Surface) -> None:
        """Draw the first-time setup screen"""
        # Title
        self.draw_text(surface, "Welcome to Luna's Endless Lesson!", self.title_font, 
                      self.WHITE, self.screen_width // 2, 50, center=True)
        
        self.draw_text(surface, "Please Enter Your Game tag", self.subtitle_font, 
                      self.WHITE, self.screen_width // 2, 100, center=True)
        
        # Input fields
        self.draw_input_field(surface, self.input_rects['first_name'], 
                            self.first_name_input, self.active_input == 'first_name', "First Name:")
        self.draw_input_field(surface, self.input_rects['last_name'], 
                            self.last_name_input, self.active_input == 'last_name', "Last Name:")
        self.draw_input_field(surface, self.input_rects['game_name'], 
                            self.game_name_input, self.active_input == 'game_name', "Game Name:")
        
        # Submit button
        submit_enabled = (self.first_name_input.strip() and 
                         self.last_name_input.strip() and 
                         self.game_name_input.strip())
        
        if submit_enabled:
            self.draw_button(surface, self.button_rects['submit'], "Submit", 
                           self.submit_button_hover, self.GREEN if self.submit_button_hover else self.BLUE)
        else:
            # Disabled button (semi-transparent)
            disabled_surface = pygame.Surface((self.button_rects['submit'].width, self.button_rects['submit'].height), pygame.SRCALPHA)
            pygame.draw.rect(disabled_surface, (*self.DARK_GRAY, 120), (0, 0, self.button_rects['submit'].width, self.button_rects['submit'].height))
            pygame.draw.rect(disabled_surface, (*self.GRAY, 150), (0, 0, self.button_rects['submit'].width, self.button_rects['submit'].height), 2)
            surface.blit(disabled_surface, self.button_rects['submit'])
            self.draw_text(surface, "Submit", self.text_font, self.GRAY, 
                          self.button_rects['submit'].centerx, self.button_rects['submit'].centery, center=True)
        
        # Instructions
        # self.draw_text(surface, "Press TAB to switch between fields", self.small_font, 
        #               self.LIGHT_GRAY, self.screen_width // 2, self.screen_height - 50, center=True)
    
    def draw_returning_user_menu(self, surface: pygame.Surface) -> None:
        """Draw the returning user menu"""
        player_name = self.settings.get_display_name()
        
        # Welcome message (centered)
        self.draw_text(surface, "Welcome back!", self.title_font, 
                      self.WHITE, self.screen_width // 2, self.screen_height // 2 - 150, center=True)
        
        self.draw_text(surface, f"Hello, {player_name}!", self.subtitle_font, 
                      self.WHITE, self.screen_width // 2, self.screen_height // 2 - 100, center=True)
        
        # Buttons (centered)
        self.draw_button(surface, self.button_rects['start'], "Start Game", self.start_button_hover)
        self.draw_button(surface, self.button_rects['quit'], "Quit Game", self.quit_button_hover)
        
        # System info (bottom left)
        # system_id = self.settings.get_system_id()
        # self.draw_text(surface, f"System ID: {system_id}", self.small_font, 
        #               self.LIGHT_GRAY, 10, self.screen_height - 20)
    
    def run(self, screen: pygame.Surface) -> str:
        """Run the start screen and return the action to take"""
        clock = pygame.time.Clock()
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit_game"
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "quit_game"
                    elif event.key == pygame.K_RETURN:
                        if self.settings.is_first_time_user():
                            # Check if all fields are filled
                            if (self.first_name_input.strip() and 
                                self.last_name_input.strip() and 
                                self.game_name_input.strip()):
                                # Update local settings
                                self.settings.update_player_data(
                                    self.first_name_input.strip(),
                                    self.last_name_input.strip(),
                                    self.game_name_input.strip()
                                )
                                
                                # Sync to database
                                try:
                                    self.api_client.create_or_update_player()
                                    print("✅ Player data synced to database successfully")
                                except Exception as e:
                                    print(f"❌ Failed to sync player data to database: {e}")
                                    # Continue anyway - local data is saved
                                
                                return "setup_complete"
                        else:
                            return "start_game"
                    else:
                        self.handle_input_event(event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        action = self.handle_mouse_click(event.pos)
                        if action:
                            return action
                elif event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_motion(event.pos)
            
            # Clear the screen to prevent pixel trails
            screen.fill((0, 0, 0))  # Black fill to clear previous frame
            
            # Update and draw confetti
            self.update_confetti()
            self.draw_confetti(screen)
            
            if self.settings.is_first_time_user():
                self.draw_first_time_setup(screen)
            else:
                self.draw_returning_user_menu(screen)
            
            pygame.display.flip()
            clock.tick(60)
