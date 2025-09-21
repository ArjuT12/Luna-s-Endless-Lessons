import json
import os
import time
import sys
import tempfile
from pathlib import Path

class StoryProgression:
    def __init__(self, save_file="story_progress.json"):
        self.save_file = self._get_writable_save_path(save_file)
        self.progress = {
            "deaths": 0,
            "hearts_unlocked": False,
            "bow_unlocked": False,
            "current_story_part": 0,
            "has_seen_intro": False,
            "inventory": []
        }
        self.last_modified = 0
        self.last_check_time = 0
        self.check_interval = 2.0  # Check every 2 seconds
        self.load_progress()
    
    def _get_writable_save_path(self, original_file):
        """Get a writable path for the save file, handling both development and build environments"""
        # Check if we're running from a PyInstaller bundle
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Running from PyInstaller bundle
            print("🔧 Running from build - using user data directory")
            
            # Get user data directory (platform-specific)
            if sys.platform == "win32":
                # Windows: %APPDATA%/LunasEndlessLesson/
                appdata = os.environ.get('APPDATA', '')
                user_data_dir = Path(appdata) / "LunasEndlessLesson"
            elif sys.platform == "darwin":
                # macOS: ~/Library/Application Support/LunasEndlessLesson/
                home = Path.home()
                user_data_dir = home / "Library" / "Application Support" / "LunasEndlessLesson"
            else:
                # Linux: ~/.local/share/LunasEndlessLesson/
                home = Path.home()
                user_data_dir = home / ".local" / "share" / "LunasEndlessLesson"
            
            # Create directory if it doesn't exist
            user_data_dir.mkdir(parents=True, exist_ok=True)
            
            # Use the user data directory for the save file
            writable_path = user_data_dir / original_file
            
            # If the writable file doesn't exist, try to copy from bundled file
            if not writable_path.exists():
                bundled_path = Path(sys._MEIPASS) / original_file
                if bundled_path.exists():
                    print(f"📋 Copying bundled {original_file} to user data directory")
                    try:
                        import shutil
                        shutil.copy2(bundled_path, writable_path)
                        print(f"✅ Copied to: {writable_path}")
                    except Exception as e:
                        print(f"⚠️  Could not copy bundled file: {e}")
                        print(f"📝 Will create new file at: {writable_path}")
            
            return str(writable_path)
        else:
            # Running in development - use original path
            print("🔧 Running in development - using local file")
            return original_file
    
    def load_progress(self, force_reload=False):
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, 'r') as f:
                    new_progress = json.load(f)
                
                # Check if data actually changed
                if force_reload or new_progress != self.progress:
                    old_progress = self.progress.copy()
                    self.progress = new_progress
                    
                    if force_reload:
                        print(f"🔄 Reloaded story progress: {self.progress}")
                    else:
                        print(f"🔄 Story progress updated: {self.progress}")
                        self._notify_changes(old_progress, new_progress)
                else:
                    print(f"📄 Story progress unchanged: {self.progress}")
                    
            except Exception as e:
                print(f"Error loading story progress: {e}")
                self.progress = {
                    "deaths": 0,
                    "hearts_unlocked": False,
                    "bow_unlocked": False,
                    "current_story_part": 0,
                    "has_seen_intro": False,
                    "inventory": []
                }
    
    def save_progress(self):
        try:
            with open(self.save_file, 'w') as f:
                json.dump(self.progress, f, indent=2)
            print(f"Saved story progress: {self.progress}")
            # Update last modified time
            self.last_modified = time.time()
        except Exception as e:
            print(f"Error saving story progress: {e}")
    
    def check_for_updates(self, api_client=None, system_id=None):
        """Check if the story progress file has been updated externally or via API"""
        current_time = time.time()
        
        # Only check if enough time has passed
        if current_time - self.last_check_time < self.check_interval:
            return False
            
        self.last_check_time = current_time
        
        # First check for API updates (cloud hearts)
        if api_client and system_id:
            if self._check_api_heart_updates(api_client, system_id):
                return True
        
        # Then check for file updates (local development)
        if not os.path.exists(self.save_file):
            return False
            
        try:
            # Check file modification time
            file_mtime = os.path.getmtime(self.save_file)
            
            # If file was modified after our last known modification
            if file_mtime > self.last_modified:
                print(f"🔄 File modified externally, reloading...")
                self.load_progress()
                self.last_modified = file_mtime
                return True
                
        except Exception as e:
            print(f"Error checking file updates: {e}")
            
        return False
    
    def _check_api_heart_updates(self, api_client, system_id):
        """Check for heart purchases from API and update local file"""
        try:
            # Get pending hearts from API
            result = api_client.get_pending_hearts(system_id)
            
            if result.get("pending_hearts", 0) > 0:
                print(f"🛒 Found {result['pending_hearts']} pending hearts from API")
                
                # Add hearts to local file
                old_hearts = sum(item.get("quantity", 0) for item in self.progress.get("inventory", []) if item.get("type") == "heart")
                new_hearts = old_hearts + result["pending_hearts"]
                
                # Update inventory
                inventory = self.progress.get("inventory", [])
                heart_item = None
                
                for item in inventory:
                    if item.get("type") == "heart":
                        heart_item = item
                        break
                
                if heart_item:
                    heart_item["quantity"] = new_hearts
                else:
                    inventory.append({"type": "heart", "quantity": result["pending_hearts"]})
                
                self.progress["inventory"] = inventory
                self.progress["hearts_unlocked"] = True
                
                # Save to file
                self.save_progress()
                
                # Mark as processed in API
                process_result = api_client.process_heart_purchases(system_id)
                if process_result.get("success", False):
                    print(f" Processed {result['pending_hearts']} hearts from API")
                else:
                    print(f"Failed to mark hearts as processed: {process_result.get('error', 'Unknown error')}")
                
                return True
                
        except Exception as e:
            print(f"Error checking API heart updates: {e}")
            
        return False
    
    def _notify_changes(self, old_progress, new_progress):
        """Notify about specific changes in story progress"""
        changes = []
        
        # Check for inventory changes
        old_inventory = old_progress.get("inventory", [])
        new_inventory = new_progress.get("inventory", [])
        
        if old_inventory != new_inventory:
            old_hearts = sum(item.get("quantity", 0) for item in old_inventory if item.get("type") == "heart")
            new_hearts = sum(item.get("quantity", 0) for item in new_inventory if item.get("type") == "heart")
            
            if new_hearts > old_hearts:
                changes.append(f"💖 Gained {new_hearts - old_hearts} hearts! (Total: {new_hearts})")
            elif new_hearts < old_hearts:
                changes.append(f"💔 Lost {old_hearts - new_hearts} hearts! (Total: {new_hearts})")
        
        # Check for ability unlocks
        if not old_progress.get("hearts_unlocked", False) and new_progress.get("hearts_unlocked", False):
            changes.append("💖 Hearts unlocked!")
            
        if not old_progress.get("bow_unlocked", False) and new_progress.get("bow_unlocked", False):
            changes.append("🏹 Bow unlocked!")
        
        # Check for story progression
        old_story_part = old_progress.get("current_story_part", 0)
        new_story_part = new_progress.get("current_story_part", 0)
        
        if new_story_part > old_story_part:
            changes.append(f"📖 Story progressed to part {new_story_part}!")
        
        # Print all changes
        for change in changes:
            print(f"🔄 {change}")
    
    def force_reload(self):
        """Force reload the story progress from file"""
        self.load_progress(force_reload=True)
        if os.path.exists(self.save_file):
            self.last_modified = os.path.getmtime(self.save_file)
    
    def player_died(self):
        self.progress["deaths"] += 1
        print(f"Player died! Total deaths: {self.progress['deaths']}")
        
        if self.progress["deaths"] == 1 and not self.progress["hearts_unlocked"]:
            self.progress["hearts_unlocked"] = True
            self.progress["current_story_part"] = 1
            print("Hearts unlocked!")
        
        elif self.progress["deaths"] == 2 and not self.progress["bow_unlocked"]:
            self.progress["bow_unlocked"] = True
            self.progress["current_story_part"] = 2
            print("Bow and arrow unlocked!")
        
        self.save_progress()
    
    def can_use_hearts(self):
        """Check if player can use hearts"""
        return self.progress["hearts_unlocked"]
    
    def can_use_bow(self):
        """Check if player can use bow"""
        return self.progress["bow_unlocked"]
    
    def get_bow_damage_multiplier(self):
        """Calculate bow damage multiplier based on deaths"""
        deaths = self.progress.get("deaths", 0)
        # Base multiplier starts at 1.0, increases by 0.1 for every 5 deaths
        # This means: 0-4 deaths = 1.0x, 5-9 deaths = 1.1x, 10-14 deaths = 1.2x, etc.
        multiplier = 1.0 + (deaths // 5) * 0.1
        return max(1.0, multiplier)  # Ensure minimum 1.0x multiplier
    
    def get_story_dialogue(self, story_part):
        """Get dialogue for specific story part"""
        # Skip dialogue after 2 deaths
        if self.progress["deaths"] >= 2:
            return []
            
        dialogues = {
            0: [  # Intro - no items
                "Welcome, Luna...",
                "You find yourself in a dangerous forest.",
                "You must survive with only your sword.",
                "Remember - each death teaches you something new...",
                "Press R to begin your endless lesson!"
            ],
            1: [  # After first death - hearts unlocked
                "Luna, you have fallen... but learned.",
                "I sense your growing wisdom.",
                "I grant you the power of healing hearts.",
                "HEART CONTROLS:",
                "I - Open/Close Inventory",
                "1-0 - Select Heart Slot",
                "W - Use Selected Heart",
                "Use them wisely to survive longer.",
                "Each death brings new understanding..."
            ],
            2: [  # After second death - bow unlocked
                "Luna, your persistence has impressed me...",
                "You have learned the value of healing.",
                "Now I grant you the ancient bow and arrows.",
                "A Special bow for you, Luna!",
                "This bow can shoot arrows that pierce through walls.",
                "BOW CONTROLS:",
                "E - Switch Sword/Bow",
                "F - Fire Arrow (when bow selected)",
                "Arrow Keys - Aim Direction",
            ]
        }
        return dialogues.get(story_part, [])
    
    def get_intro_dialogue(self):
        """Get intro dialogue"""
        return [
            "Welcome to Luna's Endless Lesson",
            "A tale of learning through failure...",
            "",
            "CONTROLS:",
            "Arrow Keys - Move Left/Right",
            "SPACE - Jump",
            "F - Attack with Sword",
            "",
            
            "Press R to begin Luna's journey!"
        ]
    
    def save_inventory(self, inventory_items):
        """Save inventory items to progress"""
        self.progress["inventory"] = inventory_items
        self.save_progress()
    
    def load_inventory(self):
        """Load inventory items from progress"""
        return self.progress.get("inventory", [])
    
    def reset_progress(self):
        """Reset all story progression"""
        self.progress = {
            "deaths": 0,
            "hearts_unlocked": False,
            "bow_unlocked": False,
            "current_story_part": 0,
            "has_seen_intro": False,
            "inventory": []
        }
        self.save_progress()
        print("Story progress reset!")
