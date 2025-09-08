import json
import os
import platform
import hashlib
import tempfile
import sys
from typing import Dict, Optional

class GameSettings:
    def __init__(self):
        # Use a hidden location for settings file
        self.settings_file = self._get_hidden_settings_path()
        self.settings_data = self.load_settings()
    
    def _get_hidden_settings_path(self) -> str:
        """Get a hidden path for the settings file"""
        if getattr(sys, 'frozen', False):
            # Running as compiled EXE
            if platform.system() == "Windows":
                # Windows: Use AppData\Local\Temp or create hidden folder
                appdata = os.environ.get('APPDATA', tempfile.gettempdir())
                hidden_dir = os.path.join(appdata, '.LunaGame')
                os.makedirs(hidden_dir, exist_ok=True)
                return os.path.join(hidden_dir, 'settings.dat')
            else:
                # macOS/Linux: Use hidden directory in home
                home = os.path.expanduser("~")
                hidden_dir = os.path.join(home, '.luna_game')
                os.makedirs(hidden_dir, exist_ok=True)
                return os.path.join(hidden_dir, 'settings.dat')
        else:
            # Running as Python script (development)
            return "game_settings.json"
    
    def generate_system_id(self) -> str:
        """Generate a unique system ID based on system information"""
        # Get system information
        system_info = {
            'platform': platform.system(),
            'processor': platform.processor(),
            'machine': platform.machine(),
            'node': platform.node()
        }
        
        # Create a hash from system information
        system_string = f"{system_info['platform']}-{system_info['processor']}-{system_info['machine']}-{system_info['node']}"
        system_id = hashlib.md5(system_string.encode()).hexdigest()[:16]
        
        return system_id
    
    def load_settings(self) -> Dict:
        """Load settings from file or create default settings"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    if getattr(sys, 'frozen', False):
                        # Running as EXE - deobfuscate data
                        obfuscated_data = f.read()
                        json_str = self._deobfuscate_data(obfuscated_data)
                        return json.loads(json_str)
                    else:
                        # Running as Python script - normal JSON
                        return json.load(f)
            except (json.JSONDecodeError, IOError, UnicodeDecodeError):
                print("Error loading settings file, creating new one...")
                return self.create_default_settings()
        else:
            return self.create_default_settings()
    
    def create_default_settings(self) -> Dict:
        """Create default settings for new system"""
        system_id = self.generate_system_id()
        default_settings = {
            'system_id': system_id,
            'is_first_time': True,
            'player_data': {
                'first_name': '',
                'last_name': '',
                'game_name': ''
            },
            'game_settings': {
                'volume': 0.7,
                'fullscreen': False
            }
        }
        self.save_settings(default_settings)
        return default_settings
    
    def save_settings(self, settings_data: Optional[Dict] = None) -> None:
        """Save settings to file with basic obfuscation when running as EXE"""
        if settings_data is None:
            settings_data = self.settings_data
        
        try:
            if getattr(sys, 'frozen', False):
                # Running as EXE - obfuscate data
                json_str = json.dumps(settings_data, separators=(',', ':'))
                obfuscated = self._obfuscate_data(json_str)
                
                with open(self.settings_file, 'w') as f:
                    f.write(obfuscated)
            else:
                # Running as Python script - normal JSON
                with open(self.settings_file, 'w') as f:
                    json.dump(settings_data, f, indent=2)
        except IOError as e:
            print(f"Error saving settings: {e}")
    
    def _obfuscate_data(self, data: str) -> str:
        """Simple obfuscation - XOR with a key"""
        key = "LunaGame2025"
        result = []
        for i, char in enumerate(data):
            result.append(chr(ord(char) ^ ord(key[i % len(key)])))
        return ''.join(result)
    
    def _deobfuscate_data(self, data: str) -> str:
        """Deobfuscate data - XOR with the same key"""
        key = "LunaGame2025"
        result = []
        for i, char in enumerate(data):
            result.append(chr(ord(char) ^ ord(key[i % len(key)])))
        return ''.join(result)
    
    def is_first_time_user(self) -> bool:
        """Check if this is a first-time user"""
        return self.settings_data.get('is_first_time', True)
    
    def get_player_data(self) -> Dict:
        """Get player data"""
        return self.settings_data.get('player_data', {
            'first_name': '',
            'last_name': '',
            'game_name': ''
        })
    
    def update_player_data(self, first_name: str, last_name: str, game_name: str) -> None:
        """Update player data and mark as not first time"""
        self.settings_data['player_data'] = {
            'first_name': first_name,
            'last_name': last_name,
            'game_name': game_name
        }
        self.settings_data['is_first_time'] = False
        self.save_settings()
    
    def get_system_id(self) -> str:
        """Get the system ID"""
        return self.settings_data.get('system_id', self.generate_system_id())
    
    def get_display_name(self) -> str:
        """Get the display name for the player"""
        player_data = self.get_player_data()
        if player_data['game_name']:
            return player_data['game_name']
        elif player_data['first_name'] and player_data['last_name']:
            return f"{player_data['first_name']} {player_data['last_name']}"
        else:
            return "Player"
