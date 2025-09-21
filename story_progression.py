import json
import os
import time

class StoryProgression:
    def __init__(self, save_file="story_progress.json"):
        self.save_file = save_file
        self.progress = {
            "deaths": 0,
            "hearts_unlocked": False,
            "bow_unlocked": False,
            "current_story_part": 0,
            "has_seen_intro": False,
            "inventory": []
        }
        self.last_check_time = 0
        self.check_interval = 5.0  # Check every 5 seconds
        self.load_progress()
    
    def load_progress(self):
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
        try:
            with open(self.save_file, 'w') as f:
                json.dump(self.progress, f, indent=2)
            print(f"Saved story progress: {self.progress}")
        except Exception as e:
            print(f"Error saving story progress: {e}")
    
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
    
    def check_for_heart_purchases(self, api_client, system_id):
        """Check for heart purchases from API and update local file"""
        current_time = time.time()
        
        # Only check if enough time has passed
        if current_time - self.last_check_time < self.check_interval:
            return False
            
        self.last_check_time = current_time
        
        try:
            print("🔄 Checking for heart purchases...")
            
            # Check if we can get player data to see recent purchases
            if api_client and system_id:
                try:
                    # Get player data to check for recent heart purchases
                    player_data = api_client.get_player_data()
                    if player_data:
                        # Check if player has currency (indicates recent activity)
                        currency = player_data.get('currency', 0)
                        print(f"Player currency: {currency}")
                        
                        # Check for actual heart purchases using the heart-specific endpoints
                        try:
                            # Get pending heart purchases
                            hearts_response = api_client.get_pending_hearts(system_id)
                            if hearts_response and hearts_response.get('pending_hearts', 0) > 0:
                                purchases = hearts_response.get('purchases', [])
                                total_hearts = 0
                                
                                # Process all pending heart purchases
                                for purchase in purchases:
                                    if not purchase.get('processed', True):  # Only unprocessed purchases
                                        quantity = purchase.get('quantity', 1)
                                        total_hearts += quantity
                                        print(f"🛒 Found heart purchase: {quantity} hearts!")
                                
                                if total_hearts > 0:
                                    # Add all hearts at once
                                    self._add_hearts(total_hearts)
                                    print(f"💖 Added {total_hearts} hearts from purchases!")
                                    
                                    # Mark purchases as processed
                                    try:
                                        api_client.process_heart_purchases(system_id)
                                        print("✅ Marked heart purchases as processed")
                                    except Exception as e:
                                        print(f"Could not mark purchases as processed: {e}")
                                    
                                    return True
                                        
                        except Exception as e:
                            print(f"Could not check heart purchases: {e}")
                            
                except Exception as e:
                    print(f"Could not check player data: {e}")
            
            # No heart purchases found
            return False
                
        except Exception as e:
            print(f"Error checking heart purchases: {e}")
            
        return False
    
    def _add_hearts(self, quantity):
        """Add hearts to inventory"""
        inventory = self.progress.get("inventory", [])
        heart_item = None
        
        for item in inventory:
            if item.get("type") == "heart":
                heart_item = item
                break
        
        if heart_item:
            heart_item["quantity"] = heart_item.get("quantity", 0) + quantity
        else:
            inventory.append({"type": "heart", "quantity": quantity})
        
        self.progress["inventory"] = inventory
        self.progress["hearts_unlocked"] = True
        
        # Save to file
        self.save_progress()
        
        print(f"💖 Added {quantity} hearts! Total: {heart_item['quantity'] if heart_item else quantity}")
    
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
