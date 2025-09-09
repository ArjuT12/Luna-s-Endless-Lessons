import pygame
import json
import os

class Animation:
    """Handles sprite animations from Aseprite JSON files"""
    
    def __init__(self, spritesheet_path, json_path, scale=1.0):
        self.spritesheet = pygame.image.load(spritesheet_path).convert_alpha()
        self.scale = scale
        
        # Load animation data from JSON
        with open(json_path, 'r') as f:
            self.data = json.load(f)
        
        # Extract frame information
        self.frames = []
        self.frame_durations = []
        
        for frame_name, frame_data in self.data['frames'].items():
            frame_info = frame_data['frame']
            duration = frame_data['duration']
            
            # Extract frame rectangle
            x = frame_info['x']
            y = frame_info['y']
            w = frame_info['w']
            h = frame_info['h']
            
            # Create surface for this frame
            frame_surface = pygame.Surface((w, h), pygame.SRCALPHA)
            frame_surface.blit(self.spritesheet, (0, 0), (x, y, w, h))
            
            # Scale if needed
            if scale != 1.0:
                frame_surface = pygame.transform.scale(frame_surface, 
                                                     (int(w * scale), int(h * scale)))
            
            self.frames.append(frame_surface)
            self.frame_durations.append(duration)
        
        # Animation state
        self.current_frame = 0
        self.frame_timer = 0
        self.loop = True
        self.finished = False
    
    def update(self):
        """Update animation frame"""
        if self.finished and not self.loop:
            return
        
        self.frame_timer += 1
        
        # Check if it's time to advance to next frame
        if self.frame_timer >= self.frame_durations[self.current_frame]:
            self.frame_timer = 0
            self.current_frame += 1
            
            # Check if animation is finished
            if self.current_frame >= len(self.frames):
                if self.loop:
                    self.current_frame = 0
                else:
                    self.current_frame = len(self.frames) - 1
                    self.finished = True
    
    def get_current_frame(self):
        """Get the current frame surface"""
        return self.frames[self.current_frame]
    
    def reset(self):
        """Reset animation to beginning"""
        self.current_frame = 0
        self.frame_timer = 0
        self.finished = False
    
    def set_loop(self, loop):
        """Set whether animation should loop"""
        self.loop = loop


class AnimationManager:
    """Manages multiple animations for an entity"""
    
    def __init__(self):
        self.animations = {}
        self.current_animation = None
        self.facing_right = True
    
    def add_animation(self, name, animation):
        """Add an animation to the manager"""
        self.animations[name] = animation
        if self.current_animation is None:
            self.current_animation = name
    
    def set_animation(self, name, loop=True):
        """Set the current animation"""
        if name in self.animations and self.current_animation != name:
            self.current_animation = name
            self.animations[name].reset()
            self.animations[name].set_loop(loop)
    
    def update(self):
        """Update current animation"""
        if self.current_animation and self.current_animation in self.animations:
            self.animations[self.current_animation].update()
    
    def get_current_frame(self):
        """Get the current frame, flipped if needed"""
        if self.current_animation and self.current_animation in self.animations:
            frame = self.animations[self.current_animation].get_current_frame()
            if not self.facing_right:
                frame = pygame.transform.flip(frame, True, False)
            return frame
        return None
    
    def set_facing(self, facing_right):
        """Set the facing direction"""
        self.facing_right = facing_right
    
    def is_animation_finished(self):
        """Check if current animation is finished"""
        if self.current_animation and self.current_animation in self.animations:
            return self.animations[self.current_animation].finished
        return False


def load_enemy_animations(enemy_type, scale=1.0):
    """Load animations for a specific enemy type"""
    animation_manager = AnimationManager()
    
    # Define animation paths for different enemy types
    animation_paths = {
        'slime': {
            'idle': ('assets/Slime_Idle.png', 'assets/Slime_Idle.json'),
            'walk': ('assets/Slime_Walk.png', 'assets/Slime_walk.json'),
            'attack': ('assets/Slime_Attack.png', 'assets/Slime_attack.json'),
            'death': ('assets/Slime_Death.png', 'assets/Slime_death.json')
        }
        # Add more enemy types here in the future
    }
    
    if enemy_type not in animation_paths:
        raise ValueError(f"Unknown enemy type: {enemy_type}")
    
    # Load all animations for this enemy type
    for anim_name, (image_path, json_path) in animation_paths[enemy_type].items():
        if os.path.exists(image_path) and os.path.exists(json_path):
            animation = Animation(image_path, json_path, scale)
            animation_manager.add_animation(anim_name, animation)
    
    return animation_manager
