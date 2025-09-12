import pygame
import json
import os
from config import *
from levels.tile import Tile


class MapLoader:
    def __init__(self):
        self.tile_images = {}
        self.tileset_data = None
        self.tilesets = []  # Store multiple tilesets
        self.map_data = None
        
    def load_tileset(self, tileset_path):
        """Load tileset data from JSON file"""
        try:
            with open(tileset_path, 'r') as f:
                self.tileset_data = json.load(f)
            print(f"Loaded tileset: {self.tileset_data['name']}")
            return True
        except FileNotFoundError:
            print(f"Tileset file not found: {tileset_path}")
            return False
        except json.JSONDecodeError:
            print(f"Invalid JSON in tileset file: {tileset_path}")
            return False
    
    def load_map(self, map_path):
        """Load map data from JSON file and all referenced tilesets"""
        try:
            with open(map_path, 'r') as f:
                self.map_data = json.load(f)
            print(f"Loaded map: {map_path}")
            print(f"Map size: {self.map_data.get('width', 0)}x{self.map_data.get('height', 0)}")
            print(f"Infinite: {self.map_data.get('infinite', False)}")
            
            # Load all tilesets referenced in the map
            if 'tilesets' in self.map_data:
                self.tilesets = []
                for tileset_info in self.map_data['tilesets']:
                    if 'source' in tileset_info:
                        tileset_path = tileset_info['source']
                        # Remove the ../ prefix if present
                        if tileset_path.startswith('../'):
                            tileset_path = tileset_path[3:]
                        
                        # Load the tileset
                        tileset_data = self._load_single_tileset(tileset_path)
                        if tileset_data:
                            tileset_data['firstgid'] = tileset_info['firstgid']
                            self.tilesets.append(tileset_data)
                            print(f"Loaded tileset: {tileset_data['name']} (firstgid: {tileset_data['firstgid']})")
            
            return True
        except FileNotFoundError:
            print(f"Map file not found: {map_path}")
            return False
        except json.JSONDecodeError:
            print(f"Invalid JSON in map file: {map_path}")
            return False
    
    def _load_single_tileset(self, tileset_path):
        """Load a single tileset from JSON file"""
        try:
            with open(tileset_path, 'r') as f:
                tileset_data = json.load(f)
            return tileset_data
        except FileNotFoundError:
            print(f"Tileset file not found: {tileset_path}")
            return None
        except json.JSONDecodeError:
            print(f"Invalid JSON in tileset file: {tileset_path}")
            return None
    
    def create_tile_image(self, tile_id):
        """Create a tile image based on tile ID from multiple tilesets"""
        if tile_id == 0:
            return None  # Empty tile
        
        # Find which tileset contains this tile ID
        tileset = None
        local_tile_id = tile_id
        
        for ts in self.tilesets:
            if tile_id >= ts['firstgid'] and tile_id < ts['firstgid'] + ts['tilecount']:
                tileset = ts
                local_tile_id = tile_id - ts['firstgid'] + 1  # Convert to local tile ID (1-based)
                break
        
        if not tileset:
            print(f"Warning: Tile ID {tile_id} not found in any tileset")
            return self.create_fallback_tile(tile_id)
        
        # Load the tileset image if not already loaded
        tileset_key = tileset['name']
        if tileset_key not in self.tile_images:
            try:
                # Use the image path from the tileset
                image_path = tileset['image']
                if image_path.startswith('../'):
                    image_path = image_path[3:]  # Remove ../ prefix
                
                self.tile_images[tileset_key] = pygame.image.load(image_path).convert_alpha()
                print(f"Loaded tileset image: {image_path}")
            except pygame.error as e:
                print(f"Failed to load tileset image {tileset['image']}: {e}")
                return self.create_fallback_tile(tile_id)
        
        tileset_image = self.tile_images[tileset_key]
        
        # Calculate tile position in the tileset
        columns = tileset['columns']
        tile_x = (local_tile_id - 1) % columns  # -1 because local tile IDs start from 1
        tile_y = (local_tile_id - 1) // columns
        
        # Create a surface for the tile
        tile_size = tileset['tilewidth']  # Use the tileset's tile size
        tile_image = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        
        # Extract the tile from the tileset
        source_rect = pygame.Rect(tile_x * tile_size, tile_y * tile_size, tile_size, tile_size)
        tile_image.blit(tileset_image, (0, 0), source_rect)
        
        return tile_image
    
    def create_fallback_tile(self, tile_id):
        """Create a colored fallback tile if tileset image fails to load"""
        colors = {
            1: (34, 139, 34),   # Forest green
            2: (34, 139, 34),   # Forest green
            3: (34, 139, 34),   # Forest green
            11: (139, 69, 19),  # Brown
            12: (139, 69, 19),  # Brown
            13: (139, 69, 19),  # Brown
            21: (105, 105, 105), # Gray
            22: (105, 105, 105), # Gray
            23: (105, 105, 105), # Gray
        }
        
        color = colors.get(tile_id, (128, 128, 128))  # Default gray
        
        tile_image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        tile_image.fill(color)
        
        # Add a border to distinguish tiles
        pygame.draw.rect(tile_image, (0, 0, 0), (0, 0, TILE_SIZE, TILE_SIZE), 1)
        
        return tile_image
    
    def create_tiles_from_map(self, groups):
        """Create tile sprites from the loaded map data"""
        if not self.map_data:
            print("No map data loaded")
            return []
        
        tiles = []
        tile_width = self.map_data.get('tilewidth', TILE_SIZE)
        tile_height = self.map_data.get('tileheight', TILE_SIZE)
        map_width = self.map_data.get('width', 0)
        map_height = self.map_data.get('height', 0)
        
        # Define which tile IDs are solid/collision tiles
        # Include all solid tiles that should have collision
        # First tileset (1-60): solid tiles
        first_tileset_solid = {1, 2, 3, 11, 12, 13, 21, 22, 23, 31}
        # Sunrise tileset (61+): only specific platform tiles are solid for walking
        sunrise_tileset_solid = {61, 62, 63, 64}  # Only these tiles are walkable platforms
        # Tiles 72, 73, 74, 83, 84, 85, 86 are decorative support tiles with NO collision
        solid_tiles = first_tileset_solid | sunrise_tileset_solid
        
        # Define which tile IDs are enemy tiles
        # First tileset enemies
        first_tileset_enemies = {41, 42}
        # Sunrise tileset enemies (61+ versions) - excluding 102 which is now interactive
        sunrise_tileset_enemies = {101}  # 61+ versions of enemy tiles
        enemy_tiles = first_tileset_enemies | sunrise_tileset_enemies
        
        # Define which tile IDs are interactive tiles
        interactive_tiles = {102}  # Tile 102 is now interactive
        
        # Process each layer
        for layer in self.map_data.get('layers', []):
            if layer.get('type') == 'tilelayer':
                layer_data = layer.get('data', [])
                layer_width = layer.get('width', map_width)
                layer_height = layer.get('height', map_height)
                
                for i, tile_id in enumerate(layer_data):
                    if tile_id != 0:  # Skip empty tiles
                        # Calculate position within the layer using map width for consistency
                        x = i % map_width
                        y = i // map_width
                        
                        # Calculate world position
                        world_x = x * tile_width
                        world_y = y * tile_height
                        

                        
                        # Create tile image
                        tile_image = self.create_tile_image(tile_id)
                        if tile_image:
                            # Create tile sprite
                            # Only add solid tiles to collision groups
                            if tile_id in solid_tiles:
                                tile = Tile((world_x, world_y), groups)
                            elif tile_id in enemy_tiles:
                                # For enemy tiles, add to enemy group (last group in the list)
                                enemy_groups = [groups[-1]] if groups else []
                                tile = Tile((world_x, world_y), enemy_groups)
                                tile.tile_id = tile_id  # Store tile ID for enemy detection
                            elif tile_id in interactive_tiles:
                                # For interactive tiles, create without collision but store tile ID
                                tile = Tile((world_x, world_y), [])
                                tile.tile_id = tile_id  # Store tile ID for interaction detection
                                tile.is_interactive = True  # Mark as interactive
                            else:
                                # For decorative tiles, create without collision
                                tile = Tile((world_x, world_y), [])
                            tile.image = tile_image
                            tiles.append(tile)
        
        print(f"Created {len(tiles)} tiles from map data")
        return tiles
    
    def create_objects_from_map(self, groups):
        """Create object sprites from object layers in the map data"""
        if not self.map_data:
            print("No map data loaded")
            return []
        
        objects = []
        
        # Process each layer
        for layer in self.map_data.get('layers', []):
            if layer.get('type') == 'objectgroup':
                layer_name = layer.get('name', '')
                print(f"Processing object layer: {layer_name}")
                
                # Process objects in this layer
                for obj in layer.get('objects', []):
                    obj_type = obj.get('type', '')
                    obj_name = obj.get('name', '')
                    obj_x = obj.get('x', 0)
                    obj_y = obj.get('y', 0)
                    obj_width = obj.get('width', 32)
                    obj_height = obj.get('height', 32)
                    obj_gid = obj.get('gid', 0)
                    
                    print(f"Object: {obj_name} (type: {obj_type}, gid: {obj_gid}) at ({obj_x}, {obj_y})")
                    
                    # Create heart objects for Health layer
                    if layer_name.lower() == 'health' or obj_type.lower() == 'heart' or obj_gid == 117:
                        from entities.heart import Heart
                        # Adjust Y position to place heart 20 pixels above the floor
                        heart_y = obj_y - 20
                        heart = Heart(obj_x, heart_y, groups)
                        objects.append(heart)
                        print(f"Created heart object at ({obj_x}, {heart_y}) (adjusted from {obj_y})")
        
        print(f"Created {len(objects)} objects from map data")
        return objects
    
    def get_visible_tiles(self, camera_rect, tiles):
        """Get tiles that are visible within the camera view"""
        visible_tiles = []
        for tile in tiles:
            if tile.rect.colliderect(camera_rect):
                visible_tiles.append(tile)
        return visible_tiles
