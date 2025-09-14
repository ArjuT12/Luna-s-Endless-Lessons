import json
import os

class StoryProgression:
    def __init__(self, save_file="story_progress.json"):
        self.save_file = save_file
        self.progress = {
            "deaths": 0,
            "hearts_unlocked": False,
            "bow_unlocked": False,
            "current_story_part": 0,
            "has_seen_intro": False,
            "inventory": []  # Store inventory items
        }
        self.load_progress()
    
    def load_progress(self):
        """Load story progression from file"""
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, 'r') as f:
                    self.progress = json.load(f)
                print(f"Loaded story progress: {self.progress}")
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
        """Save story progression to file"""
        try:
            with open(self.save_file, 'w') as f:
                json.dump(self.progress, f, indent=2)
            print(f"Saved story progress: {self.progress}")
        except Exception as e:
            print(f"Error saving story progress: {e}")
    
    def player_died(self):
        """Called when player dies - updates progression"""
        self.progress["deaths"] += 1
        print(f"Player died! Total deaths: {self.progress['deaths']}")
        
        # Unlock hearts after first death
        if self.progress["deaths"] == 1 and not self.progress["hearts_unlocked"]:
            self.progress["hearts_unlocked"] = True
            self.progress["current_story_part"] = 1
            print("Hearts unlocked!")
        
        # Unlock bow after second death
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
    
    def get_story_dialogue(self, story_part):
        """Get dialogue for specific story part"""
        # Skip dialogue after 4 deaths
        if self.progress["deaths"] >= 4:
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
