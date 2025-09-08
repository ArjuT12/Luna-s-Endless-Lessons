import pygame
import os
from config import WIDTH, HEIGHT

class BackgroundLayer:
    """Represents a single background layer with parallax scrolling"""
    
    def __init__(self, image_path, parallax_factor=1.0, y_offset=0, scale_factor=1.0):
        """
        Initialize a background layer
        
        Args:
            image_path: Path to the background image
            parallax_factor: How much this layer moves relative to camera (0.0 = fixed, 1.0 = moves with camera)
            y_offset: Vertical offset for positioning the layer
            scale_factor: Scale factor for the image (1.0 = original size)
        """
        self.image = pygame.image.load(image_path)
        # Convert to alpha format only if pygame display is initialized
        try:
            self.image = self.image.convert_alpha()
        except pygame.error:
            # If convert_alpha fails, just use the loaded image as-is
            pass
        
        self.parallax_factor = parallax_factor
        self.y_offset = y_offset
        self.scale_factor = scale_factor
        
        # Scale the image
        self.scale_image()
    
    def scale_image(self):
        """Scale the image based on scale factor and screen dimensions"""
        # Apply the scale factor first
        if self.scale_factor != 1.0:
            original_width = self.image.get_width()
            original_height = self.image.get_height()
            new_width = int(original_width * self.scale_factor)
            new_height = int(original_height * self.scale_factor)
            self.image = pygame.transform.scale(self.image, (new_width, new_height))
        
        # Store dimensions
        self.scaled_width = self.image.get_width()
        self.scaled_height = self.image.get_height()
    
    def draw(self, screen, camera_offset):
        """
        Draw the background layer with parallax scrolling
        
        Args:
            screen: Pygame screen surface
            camera_offset: Camera position (x, y)
        """
        # Calculate parallax offset
        parallax_x = camera_offset[0] * self.parallax_factor
        parallax_y = camera_offset[1] * self.parallax_factor
        
        # Calculate drawing position
        draw_x = int(-parallax_x % self.scaled_width)
        draw_y = int(self.y_offset - parallax_y)
        
        # Ensure the layer covers the full screen height
        if self.scaled_height < HEIGHT:
            # Center vertically if smaller than screen
            draw_y = int((HEIGHT - self.scaled_height) // 2 + self.y_offset - parallax_y)
        else:
            # Start from top if larger than screen
            if draw_y > 0:
                draw_y = 0
        
        # Draw the main image
        screen.blit(self.image, (draw_x, draw_y))
        
        # Draw additional copies for seamless horizontal scrolling
        if self.scaled_width < WIDTH:
            # Calculate how many copies we need
            copies_needed = int(WIDTH / self.scaled_width) + 2
            for i in range(1, copies_needed):
                x_pos = draw_x + (i * self.scaled_width)
                if x_pos < WIDTH:  # Only draw if visible
                    screen.blit(self.image, (x_pos, draw_y))
        
        # Draw copies to the left for seamless scrolling
        if draw_x > 0:
            copies_left = int(draw_x / self.scaled_width) + 1
            for i in range(1, copies_left + 1):
                x_pos = draw_x - (i * self.scaled_width)
                if x_pos > -self.scaled_width:  # Only draw if partially visible
                    screen.blit(self.image, (x_pos, draw_y))

class LayeredBackground:
    """Manages multiple background layers with different parallax effects"""
    
    def __init__(self, background_folder="Background layers"):
        """
        Initialize the layered background system
        
        Args:
            background_folder: Path to folder containing background layer images
        """
        self.layers = []
        self.background_folder = background_folder
        self.load_background_layers()
    
    def load_background_layers(self):
        """Load all background layer images from the specified folder"""
        if not os.path.exists(self.background_folder):
            print(f"Warning: Background folder '{self.background_folder}' not found")
            return
        
        # Clear existing layers
        self.layers = []
        
        # Get all PNG files in the background folder
        image_files = [f for f in os.listdir(self.background_folder) if f.endswith('.png')]
        
        # Sort by the layer number in the filename
        # We want Layer_0010_1 first (farthest), then Layer_0009_2, etc.
        def extract_layer_number(filename):
            try:
                # Extract number from filename like "Layer_0000_9.png" -> 0
                parts = filename.replace('.png', '').split('_')
                if len(parts) >= 2:
                    layer_num = int(parts[1])  # Get the middle number
                    # Special case: Layer_0011_0 should be last (ground level)
                    if layer_num == 11:
                        return 1  # Put it after all others
                    # Reverse the order so 10 comes first, then 9, 8, etc.
                    return -layer_num
                return 999
            except (ValueError, IndexError):
                return 999
        
        image_files.sort(key=extract_layer_number)
        
        print(f"🌙 Loading {len(image_files)} background layers...")
        
        # Define layer properties for better parallax effect
        # Order: Layer_0010_1 (farthest) → Layer_0000_9 (closest)
        layer_properties = [
            # (parallax_factor, y_offset, scale_factor, description)
            (0.02, 0, 1.2, "Sky"),                    # Layer_0010_1 - Very distant sky
            (0.05, 50, 1.1, "Distant Mountains"),     # Layer_0009_2 - Distant mountains
            (0.1, 100, 1.0, "Far Mountains"),         # Layer_0008_3 - Far mountains
            (0.15, 150, 0.95, "Mid-Far Mountains"),   # Layer_0007_Lights - Mid-far mountains
            (0.25, 200, 0.9, "Mid Mountains"),        # Layer_0006_4 - Mid mountains
            (0.35, 250, 0.85, "Mid-Close Mountains"), # Layer_0005_5 - Mid-close mountains
            (0.45, 300, 0.8, "Close Mountains"),      # Layer_0004_Lights - Close mountains
            (0.55, 350, 0.75, "Very Close Mountains"), # Layer_0003_6 - Very close mountains
            (0.65, 400, 0.7, "Near Foreground"),      # Layer_0002_7 - Near foreground
            (0.75, 450, 0.65, "Close Foreground"),    # Layer_0001_8 - Close foreground
            (0.85, 500, 0.6, "Very Close Foreground"), # Layer_0000_9 - Very close foreground
            (1.0, HEIGHT - 200, 0.55, "Ground Level"), # Layer_0011_0 - Ground level
        ]
        
        # Load each layer in the correct order
        for i, image_file in enumerate(image_files):
            if i >= len(layer_properties):
                break
                
            image_path = os.path.join(self.background_folder, image_file)
            parallax_factor, y_offset, scale_factor, description = layer_properties[i]
            
            try:
                layer = BackgroundLayer(image_path, parallax_factor, y_offset, scale_factor)
                self.layers.append(layer)
                
                # Show the correct layer order in the description
                layer_order = ["Layer_0010_1", "Layer_0009_2", "Layer_0008_3", "Layer_0007_Lights", 
                              "Layer_0006_4", "Layer_0005_5", "Layer_0004_Lights", "Layer_0003_6", 
                              "Layer_0002_7", "Layer_0001_8", "Layer_0000_9", "Layer_0011_0"]
                
                if i < len(layer_order):
                    expected_name = layer_order[i]
                    if image_file == expected_name:
                        print(f"✓ Loaded Layer {i}: {image_file} ({description}) - Parallax: {parallax_factor}, Scale: {scale_factor}")
                    else:
                        print(f"⚠ Loaded Layer {i}: {image_file} (Expected: {expected_name}) - Parallax: {parallax_factor}, Scale: {scale_factor}")
                else:
                    print(f"✓ Loaded Layer {i}: {image_file} ({description}) - Parallax: {parallax_factor}, Scale: {scale_factor}")
                    
            except pygame.error as e:
                print(f"✗ Error loading {image_file}: {e}")
        
        print(f"🎨 Background system ready with {len(self.layers)} layers!")
    
    def draw(self, screen, camera_offset):
        """
        Draw all background layers in order (back to front)
        
        Args:
            screen: Pygame screen surface
            camera_offset: Camera position (x, y)
        """
        # Draw layers from back to front (distant to close)
        for i, layer in enumerate(self.layers):
            layer.draw(screen, camera_offset)
    
    def get_layer_count(self):
        """Return the number of loaded background layers"""
        return len(self.layers)
    
    def get_sky_color(self):
        """Return the sky color (transparent for layered background)"""
        return (0, 0, 0, 0)  # Transparent - let the background layers show through
    
    def get_background_fill_color(self):
        """Return a solid RGB color sampled from the farthest background layer.
        
        This is used for screen.fill() to clear previous frames without
        showing black behind parallax seams.
        """
        if not self.layers:
            return (0, 0, 0)
        
        # Use the first layer (sky/distant) to get a representative color
        surface = self.layers[0].image
        width = surface.get_width()
        height = surface.get_height()
        if width == 0 or height == 0:
            return (0, 0, 0)
        
        # Sample a few pixels across the top area to get a representative sky color
        sample_points = [
            (0, 0),
            (max(0, width // 4), 0),
            (max(0, width // 2), 0),
            (max(0, (3 * width) // 4), 0),
            (max(0, width - 1), 0),
            (max(0, width // 2), min(10, height - 1)),
        ]
        
        r_total = g_total = b_total = 0
        count = 0
        for x, y in sample_points:
            try:
                color = surface.get_at((int(x), int(y)))
                r_total += int(color.r)
                g_total += int(color.g)
                b_total += int(color.b)
                count += 1
            except Exception:
                continue
        
        if count == 0:
            return (0, 0, 0)
        
        return (r_total // count, g_total // count, b_total // count)