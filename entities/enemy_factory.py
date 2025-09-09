"""
Enemy Factory - Creates different types of enemies
"""

from .enemy import Enemy
from .slime_enemy import SlimeEnemy

class EnemyFactory:
    """Factory class for creating different types of enemies"""
    
    @staticmethod
    def create_enemy(enemy_type, x, y, waypoints=None):
        """
        Create an enemy of the specified type
        
        Args:
            enemy_type (str): Type of enemy to create ('slime', 'basic', etc.)
            x (int): X position
            y (int): Y position
            waypoints (list): List of waypoints for the enemy
            
        Returns:
            Enemy instance of the specified type
        """
        if enemy_type == 'slime':
            return SlimeEnemy(x, y, waypoints)
        elif enemy_type == 'basic':
            return Enemy(x, y, waypoints)
        else:
            raise ValueError(f"Unknown enemy type: {enemy_type}")
    
    @staticmethod
    def get_available_enemy_types():
        """Get list of available enemy types"""
        return ['slime', 'basic']
    
    @staticmethod
    def get_enemy_properties(enemy_type):
        """Get properties of a specific enemy type"""
        properties = {
            'slime': {
                'name': 'Slime',
                'health': 2,
                'speed': 2,
                'damage': 15,
                'detection_range': 120,
                'attack_range': 50,
                'description': 'A slow but persistent slime that shoots acid blobs'
            },
            'basic': {
                'name': 'Basic Enemy',
                'health': 1,
                'speed': 3,
                'damage': 20,
                'detection_range': 150,
                'attack_range': 80,
                'description': 'A basic enemy with simple AI'
            }
        }
        
        return properties.get(enemy_type, {})


# Example of how to add a new enemy type in the future:
"""
To add a new enemy type (e.g., 'goblin'):

1. Create a new enemy class in a new file (e.g., goblin_enemy.py):
   class GoblinEnemy(BaseEnemy):
       def __init__(self, x, y, waypoints=None):
           super().__init__(x, y, 'goblin', waypoints)
           # Set goblin-specific properties
           self.max_health = 3
           self.speed = 4
           # etc.

2. Add the animation assets to the assets folder:
   - Goblin_Idle.png and Goblin_Idle.json
   - Goblin_Walk.png and Goblin_Walk.json
   - Goblin_Attack.png and Goblin_Attack.json
   - Goblin_Death.png and Goblin_Death.json

3. Update the animation.py file to include goblin animations:
   animation_paths = {
       'goblin': {
           'idle': ('assets/Goblin_Idle.png', 'assets/Goblin_Idle.json'),
           'walk': ('assets/Goblin_Walk.png', 'assets/Goblin_Walk.json'),
           'attack': ('assets/Goblin_Attack.png', 'assets/Goblin_Attack.json'),
           'death': ('assets/Goblin_Death.png', 'assets/Goblin_Death.json')
       }
   }

4. Update this factory file:
   from .goblin_enemy import GoblinEnemy
   
   def create_enemy(enemy_type, x, y, waypoints=None):
       if enemy_type == 'goblin':
           return GoblinEnemy(x, y, waypoints)
       # ... existing code

5. Use the new enemy type in your game:
   enemy = EnemyFactory.create_enemy('goblin', x, y, waypoints)
"""
