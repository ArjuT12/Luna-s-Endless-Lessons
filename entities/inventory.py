import pygame
from config import *

# Heart image will be loaded when first needed
HEART_IMAGE = None

def load_heart_image():
    """Load heart image for inventory display"""
    global HEART_IMAGE
    if HEART_IMAGE is None:
        try:
            heart_img = pygame.image.load('hearts1.png').convert_alpha()
            # Resize heart image to fit inventory slot
            HEART_IMAGE = pygame.transform.scale(heart_img, (24, 24))
            print("Heart image loaded successfully for inventory")
        except pygame.error as e:
            print(f"Warning: Could not load hearts1.png for inventory display: {e}")
            # Create a fallback heart image
            HEART_IMAGE = pygame.Surface((24, 24), pygame.SRCALPHA)
            pygame.draw.circle(HEART_IMAGE, (255, 0, 0), (12, 12), 10)
            pygame.draw.circle(HEART_IMAGE, (255, 0, 0), (8, 8), 6)
            pygame.draw.circle(HEART_IMAGE, (255, 0, 0), (16, 8), 6)
    return HEART_IMAGE

class Inventory:
    def __init__(self, max_size=10):
        self.max_size = max_size
        self.items = []
        self.selected_slot = 0
        self.is_open = False  # For keyboard navigation mode
        self.highlighted_slot = -1  # For number key highlighting (-1 = no highlight)
        self.highlight_timer = 0  # Timer for number key highlight
        
    def add_item(self, item_type, quantity=1):
        """Add an item to the inventory"""
        # Check if item already exists in inventory
        for item in self.items:
            if item['type'] == item_type:
                # No stack size limit for hearts, allow unlimited stacking
                item['quantity'] += quantity
                return True
        
        # If inventory is full, can't add new item
        if len(self.items) >= self.max_size:
            print(f"Inventory is full! Cannot collect {item_type}.")
            return False
            
        # Add new item with full quantity
        self.items.append({
            'type': item_type,
            'quantity': quantity
        })
        return True
    
    def remove_item(self, item_type, quantity=1):
        """Remove an item from the inventory"""
        for item in self.items:
            if item['type'] == item_type:
                if item['quantity'] > quantity:
                    item['quantity'] -= quantity
                else:
                    self.items.remove(item)
                return True
        return False
    
    def get_item_quantity(self, item_type):
        """Get the quantity of a specific item type"""
        for item in self.items:
            if item['type'] == item_type:
                return item['quantity']
        return 0
    
    def use_item(self, item_type):
        """Use an item from the inventory"""
        if self.get_item_quantity(item_type) > 0:
            self.remove_item(item_type, 1)
            return True
        return False
    
    def get_selected_item(self):
        """Get the currently selected item"""
        if 0 <= self.selected_slot < len(self.items):
            return self.items[self.selected_slot]
        return None
    
    def select_next_slot(self):
        """Move to next inventory slot"""
        self.selected_slot = (self.selected_slot + 1) % self.max_size
    
    def select_previous_slot(self):
        """Move to previous inventory slot"""
        self.selected_slot = (self.selected_slot - 1) % self.max_size
    
    def select_slot(self, slot_number):
        """Select a specific slot (0-9)"""
        if 0 <= slot_number < self.max_size:
            self.selected_slot = slot_number
    
    def toggle_open(self):
        """Toggle inventory open/closed state"""
        self.is_open = not self.is_open
        print(f"Inventory toggle called. New state: {self.is_open}")
    
    def highlight_slot(self, slot_number):
        """Highlight a slot when number key is pressed"""
        if 0 <= slot_number < self.max_size:
            self.highlighted_slot = slot_number
            self.highlight_timer = 30  # 30 frames highlight duration
    
    def clear_highlight(self):
        """Clear the highlighted slot"""
        self.highlighted_slot = -1
        self.highlight_timer = 0
    
    def update(self):
        """Update inventory state (call this every frame)"""
        if self.highlight_timer > 0:
            self.highlight_timer -= 1
        # Don't reset highlighted_slot automatically - keep it until new selection or use
    
    def draw(self, screen, x=10, y=None):
        """Draw the inventory UI - always visible at bottom"""
        # Position at bottom of screen
        if y is None:
            y = screen.get_height() - 80
        
        # Inventory background - wider for 10 slots
        inventory_width = 400
        inventory_height = 60
        slot_size = 35
        slots_per_row = 10
        
        # Draw inventory background
        pygame.draw.rect(screen, (50, 50, 50), (x, y, inventory_width, inventory_height))
        pygame.draw.rect(screen, (100, 100, 100), (x, y, inventory_width, inventory_height), 2)
        
        # Draw inventory slots
        for i in range(self.max_size):
            slot_x = x + 5 + (i % slots_per_row) * (slot_size + 5)
            slot_y = y + 5 + (i // slots_per_row) * (slot_size + 5)
            
            # Draw slot background with different colors for selection and highlighting
            if i == self.highlighted_slot:
                color = (150, 150, 150)  # Light gray when highlighted by number key
            elif i == self.selected_slot and self.is_open:
                color = (100, 150, 255)  # Blue when in navigation mode and selected
            else:
                color = (60, 60, 60)  # Dark gray for unselected
            
            pygame.draw.rect(screen, color, (slot_x, slot_y, slot_size, slot_size))
            pygame.draw.rect(screen, (150, 150, 150), (slot_x, slot_y, slot_size, slot_size), 1)
            
            # Draw slot number (1-0 for keys 1-0)
            font = pygame.font.Font(None, 16)
            slot_number = (i + 1) % 10  # 1-9, then 0
            number_text = font.render(str(slot_number), True, (255, 255, 255))
            screen.blit(number_text, (slot_x + 2, slot_y + 2))
            
            # Draw item if exists
            if i < len(self.items):
                item = self.items[i]
                if item['type'] == 'heart':
                    # Draw heart icon using actual heart image
                    heart_image = load_heart_image()
                    if heart_image:
                        # Center the heart image in the slot
                        heart_x = slot_x + (slot_size - heart_image.get_width()) // 2
                        heart_y = slot_y + (slot_size - heart_image.get_height()) // 2
                        screen.blit(heart_image, (heart_x, heart_y))
                    else:
                        # Fallback to red square if image not available
                        heart_rect = pygame.Rect(slot_x + 2, slot_y + 2, slot_size - 4, slot_size - 4)
                        pygame.draw.rect(screen, (255, 0, 0), heart_rect)
                    
                    # Draw quantity
                    if item['quantity'] > 1:
                        font = pygame.font.Font(None, 16)
                        quantity_text = font.render(str(item['quantity']), True, (255, 255, 255))
                        screen.blit(quantity_text, (slot_x + slot_size - 15, slot_y + slot_size - 15))
        
        # Draw inventory title
        font = pygame.font.Font(None, 20)
        title_text = font.render("Inventory", True, (255, 255, 255))
        screen.blit(title_text, (x, y - 25))
        
        # Draw instructions
        instruction_font = pygame.font.Font(None, 16)
        if self.is_open:
            instructions = [
                "Use LEFT/RIGHT arrows to navigate",
                "Press W to use selected item",
                "Press U to exit navigation mode"
            ]
        else:
            instructions = [
                "Press I for navigation mode",
                "Press 1-0 to select items, W to use"
            ]
        
        for i, instruction in enumerate(instructions):
            text = instruction_font.render(instruction, True, (200, 200, 200))
            screen.blit(text, (x, y + inventory_height + 5 + i * 15))
