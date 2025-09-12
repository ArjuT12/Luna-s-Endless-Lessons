import os
import logging
import random
import string
import json
from datetime import datetime
from flask import Flask, jsonify, request, render_template
from flask_pymongo import PyMongo
from dotenv import load_dotenv
from bson import ObjectId

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_story_progress(system_id, hearts_purchased):
    """Update story_progress.json when hearts are purchased"""
    try:
        story_progress_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'story_progress.json')
        
        # Read current story progress
        if os.path.exists(story_progress_path):
            with open(story_progress_path, 'r') as f:
                story_data = json.load(f)
        else:
            # Create default story progress if file doesn't exist
            story_data = {
                "deaths": 0,
                "hearts_unlocked": True,
                "bow_unlocked": False,
                "current_story_part": 1,
                "has_seen_intro": False,
                "inventory": []
            }
        
        # Update inventory with purchased hearts
        inventory = story_data.get("inventory", [])
        heart_item = None
        
        # Find existing heart item in inventory
        for item in inventory:
            if item.get("type") == "heart":
                heart_item = item
                break
        
        if heart_item:
            # Update existing heart quantity
            heart_item["quantity"] = heart_item.get("quantity", 0) + hearts_purchased
        else:
            # Add new heart item to inventory
            inventory.append({
                "type": "heart",
                "quantity": hearts_purchased
            })
        
        story_data["inventory"] = inventory
        
        # Ensure hearts are unlocked
        story_data["hearts_unlocked"] = True
        
        # Write updated story progress back to file
        with open(story_progress_path, 'w') as f:
            json.dump(story_data, f, indent=2)
        
        logger.info(f"Updated story_progress.json for system_id {system_id}: added {hearts_purchased} hearts")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update story_progress.json: {str(e)}")
        return False

load_dotenv()  # loads .env into os.environ

mongo_uri = os.environ.get("MONGO_URI")
if not mongo_uri:
    logger.error("MONGO_URI not found in environment variables or .env file")

app = Flask(__name__)
app.config["MONGO_URI"] = mongo_uri

# Initialize MongoDB
try:
    mongo = PyMongo(app)
    mongo.cx.admin.command("ping")
    luna_db = mongo.cx.Luna
    logger.info("MongoDB connected successfully")
except Exception as e:
    logger.error(f"MongoDB connection failed: {str(e)}")
    mongo = None
    luna_db = None

# Random data generation functions
def generate_random_username():
    adjectives = ['Swift', 'Brave', 'Mystic', 'Shadow', 'Golden', 'Silver', 'Crimson', 'Azure']
    nouns = ['Player', 'Warrior', 'Mage', 'Hunter', 'Knight', 'Rogue', 'Wizard', 'Archer']
    return f"{random.choice(adjectives)}{random.choice(nouns)}{random.randint(1, 999)}"

def generate_random_email():
    domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'example.com']
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{username}@{random.choice(domains)}"

def generate_random_game_mode():
    modes = ['endless', 'time_trial', 'survival', 'arcade', 'challenge']
    return random.choice(modes)

def generate_random_item_name():
    prefixes = ['Magic', 'Ancient', 'Legendary', 'Rare', 'Epic', 'Mystic', 'Divine']
    items = ['Sword', 'Shield', 'Potion', 'Scroll', 'Gem', 'Ring', 'Amulet', 'Crystal']
    return f"{random.choice(prefixes)} {random.choice(items)}"

def generate_random_transaction_type():
    types = ['earn', 'spend', 'reward', 'purchase', 'refund']
    return random.choice(types)

def generate_random_source():
    sources = ['game_play', 'achievement', 'daily_bonus', 'purchase', 'admin_gift']
    return random.choice(sources)

# Utility functions for validation
def validate_system_id(system_id):
    """Validate system_id format and return validation result"""
    if not system_id:
        return False, "system_id is required"
    
    if not isinstance(system_id, str):
        return False, "system_id must be a string"
    
    if len(system_id) < 8:
        return False, "system_id must be at least 8 characters long"
    
    if len(system_id) > 64:
        return False, "system_id must be no more than 64 characters long"
    
    # Check for valid characters (alphanumeric and some special chars)
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', system_id):
        return False, "system_id can only contain alphanumeric characters, underscores, and hyphens"
    
    return True, "Valid system_id"

def validate_score_data(data):
    """Validate score data and return validation result"""
    errors = []
    
    if not isinstance(data.get("score_value"), (int, float)):
        errors.append("score_value must be a number")
    elif data.get("score_value", 0) < 0:
        errors.append("score_value must be non-negative")
    
    if data.get("level") is not None and not isinstance(data.get("level"), (int, float)):
        errors.append("level must be a number")
    elif data.get("level") is not None and data.get("level", 0) < 0:
        errors.append("level must be non-negative")
    
    if data.get("time_played") is not None and not isinstance(data.get("time_played"), (int, float)):
        errors.append("time_played must be a number")
    elif data.get("time_played") is not None and data.get("time_played", 0) < 0:
        errors.append("time_played must be non-negative")
    
    if data.get("enemies_killed") is not None and not isinstance(data.get("enemies_killed"), (int, float)):
        errors.append("enemies_killed must be a number")
    elif data.get("enemies_killed") is not None and data.get("enemies_killed", 0) < 0:
        errors.append("enemies_killed must be non-negative")
    
    if data.get("items_collected") is not None and not isinstance(data.get("items_collected"), (int, float)):
        errors.append("items_collected must be a number")
    elif data.get("items_collected") is not None and data.get("items_collected", 0) < 0:
        errors.append("items_collected must be non-negative")
    
    return len(errors) == 0, errors

# MongoDB Schema Definitions
class UserSchema:
    @staticmethod
    def create_user(username, email, system_id=None, user_type="player", is_active=True):
        user_doc = {
            "user_id": ObjectId(),
            "username": username,
            "email": email,
            "user_type": user_type,
            "is_active": is_active,
            "last_login": None,
            "login_count": 0,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        if system_id:
            user_doc["system_id"] = system_id
        return user_doc

class PlayerDataSchema:
    @staticmethod
    def create_player(system_id, player_data, game_settings):
        return {
            "system_id": system_id,
            "player_data": player_data,
            "game_settings": game_settings,
            "is_first_time": True,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "last_played": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def update_player(system_id, player_data=None, game_settings=None, is_first_time=None):
        update_data = {"updated_at": datetime.utcnow().isoformat(), "last_played": datetime.utcnow().isoformat()}
        
        if player_data is not None:
            update_data["player_data"] = player_data
        if game_settings is not None:
            update_data["game_settings"] = game_settings
        if is_first_time is not None:
            update_data["is_first_time"] = is_first_time
            
        return update_data

class GameScoreSchema:
    @staticmethod
    def create_score(system_id, score_value, time_played=None, enemies_killed=None, items_collected=None, max_combo=None, survival_time=None):
        return {
            "score_id": ObjectId(),
            "system_id": system_id,
            "score_value": score_value,
            "time_played": time_played,
            "enemies_killed": enemies_killed,
            "items_collected": items_collected,
            "max_combo": max_combo,
            "survival_time": survival_time,
            "created_at": datetime.utcnow().isoformat()
        }

class ScoreSchema:
    @staticmethod
    def create_score(user_id, score_value, game_mode, system_id=None):
        score_doc = {
            "score_id": ObjectId(),
            "user_id": user_id,
            "score_value": score_value,
            "game_mode": game_mode,
            "created_at": datetime.utcnow().isoformat()
        }
        if system_id:
            score_doc["system_id"] = system_id
        return score_doc

class CurrencyTransactionSchema:
    @staticmethod
    def create_transaction(user_id, transaction_type, amount, source, reference_id=None, system_id=None):
        transaction_doc = {
            "transaction_id": ObjectId(),
            "user_id": user_id,
            "type": transaction_type,
            "amount": amount,
            "source": source,
            "reference_id": reference_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        if system_id:
            transaction_doc["system_id"] = system_id
        return transaction_doc

class OrderSchema:
    @staticmethod
    def create_order(user_id, item_id, quantity, total_cost, system_id=None, status="pending"):
        order_doc = {
            "order_id": ObjectId(),
            "user_id": user_id,
            "item_id": item_id,
            "quantity": quantity,
            "total_cost": total_cost,
            "status": status,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        if system_id:
            order_doc["system_id"] = system_id
        return order_doc

class ItemSchema:
    @staticmethod
    def create_item(name, description, base_price, item_type="consumable", rarity="common", category="general", stackable=True, max_stack=99):
        return {
            "item_id": ObjectId(),
            "name": name,
            "description": description,
            "base_price": base_price,
            "item_type": item_type,
            "rarity": rarity,
            "category": category,
            "stackable": stackable,
            "max_stack": max_stack,
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

class CurrencyRuleSchema:
    @staticmethod
    def create_rule(min_score, max_score, currency_rate, active=True, rule_name=None, description=None, priority=0):
        return {
            "rule_id": ObjectId(),
            "rule_name": rule_name or f"Score {min_score}-{max_score} Rule",
            "description": description or f"Currency conversion rule for scores between {min_score} and {max_score}",
            "min_score": min_score,
            "max_score": max_score,
            "currency_rate": currency_rate,
            "priority": priority,
            "active": active,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }



# API Routes
@app.route("/")
def home():
    return "Luna's Endless Lesson Backend is running!"

@app.route("/shop")
def shop():
    """Serve the heart shop webpage"""
    return render_template('shop.html')

@app.route("/api/docs", methods=["GET"])
def api_documentation():
    """API Documentation endpoint"""
    docs = {
        "title": "Luna's Endless Lesson API",
        "version": "1.0.0",
        "description": "Backend API for Luna's Endless Lesson game with MongoDB integration",
        "base_url": request.base_url.replace("/api/docs", ""),
        "endpoints": {
            "player_management": {
                "create_player": {
                    "method": "POST",
                    "url": "/api/player",
                    "description": "Create new player data with system_id",
                    "required_fields": ["system_id"],
                    "optional_fields": ["player_data", "game_settings"]
                },
                "get_player": {
                    "method": "GET",
                    "url": "/api/player/{system_id}",
                    "description": "Get player data by system_id"
                },
                "update_player": {
                    "method": "PUT",
                    "url": "/api/player/{system_id}",
                    "description": "Update player data by system_id",
                    "optional_fields": ["player_data", "game_settings", "is_first_time"]
                },
                "delete_player": {
                    "method": "DELETE",
                    "url": "/api/player/{system_id}",
                    "description": "Delete player and associated data by system_id"
                }
            },
            "score_management": {
                "save_score": {
                    "method": "POST",
                    "url": "/api/scores",
                    "description": "Save game score for a player",
                    "required_fields": ["system_id", "score_value"],
                    "optional_fields": ["time_played", "enemies_killed", "items_collected", "max_combo", "survival_time"]
                },
                "get_player_scores": {
                    "method": "GET",
                    "url": "/api/scores/{system_id}",
                    "description": "Get all scores for a player",
                    "query_params": ["game_mode", "limit", "sort_by", "sort_order"]
                },
                "get_best_score": {
                    "method": "GET",
                    "url": "/api/scores/{system_id}/best",
                    "description": "Get player's best score",
                    "query_params": ["game_mode"]
                },
                "get_score_stats": {
                    "method": "GET",
                    "url": "/api/scores/{system_id}/stats",
                    "description": "Get player's score statistics",
                    "query_params": ["game_mode"]
                }
            },
            "leaderboard": {
                "get_leaderboard": {
                    "method": "GET",
                    "url": "/api/leaderboard",
                    "description": "Get global leaderboard",
                    "query_params": ["game_mode", "limit", "time_period"]
                },
                "get_player_rank": {
                    "method": "GET",
                    "url": "/api/leaderboard/{system_id}/rank",
                    "description": "Get player's rank in leaderboard",
                    "query_params": ["game_mode", "time_period"]
                }
            }
        },
        "data_structures": {
            "player_data": {
                "system_id": "string (required) - Unique system identifier",
                "player_data": {
                    "first_name": "string",
                    "last_name": "string", 
                    "game_name": "string"
                },
                "game_settings": {
                    "volume": "number",
                    "fullscreen": "boolean"
                },
                "is_first_time": "boolean",
                "created_at": "string (ISO format)",
                "updated_at": "string (ISO format)",
                "last_played": "string (ISO format)"
            },
            "game_score": {
                "score_id": "ObjectId",
                "system_id": "string (required)",
                "score_value": "number (required)",
                "time_played": "number (optional)",
                "enemies_killed": "number (optional)",
                "items_collected": "number (optional)",
                "max_combo": "number (optional)",
                "survival_time": "number (optional)",
                "created_at": "string (ISO format)"
            },
            "user": {
                "user_id": "ObjectId",
                "username": "string (required)",
                "email": "string (required)",
                "system_id": "string (optional)",
                "user_type": "string (default: 'player')",
                "is_active": "boolean (default: true)",
                "last_login": "string (ISO format, optional)",
                "login_count": "number (default: 0)",
                "created_at": "string (ISO format)",
                "updated_at": "string (ISO format)"
            },
            "currency_transaction": {
                "transaction_id": "ObjectId",
                "user_id": "ObjectId (required)",
                "system_id": "string (optional)",
                "type": "string (earn, spend, reward, purchase, refund)",
                "amount": "number (required)",
                "source": "string (game_play, achievement, daily_bonus, etc.)",
                "reference_id": "string (optional)",
                "created_at": "string (ISO format)",
                "updated_at": "string (ISO format)"
            },
            "order": {
                "order_id": "ObjectId",
                "user_id": "ObjectId (required)",
                "system_id": "string (optional)",
                "item_id": "ObjectId (required)",
                "quantity": "number (required)",
                "total_cost": "number (required)",
                "status": "string (default: 'pending')",
                "created_at": "string (ISO format)",
                "updated_at": "string (ISO format)"
            },
            "item": {
                "item_id": "ObjectId",
                "name": "string (required)",
                "description": "string (required)",
                "base_price": "number (required)",
                "item_type": "string (default: 'consumable')",
                "rarity": "string (default: 'common')",
                "category": "string (default: 'general')",
                "stackable": "boolean (default: true)",
                "max_stack": "number (default: 99)",
                "is_active": "boolean (default: true)",
                "created_at": "string (ISO format)",
                "updated_at": "string (ISO format)"
            },
            "currency_rule": {
                "rule_id": "ObjectId",
                "rule_name": "string (auto-generated if not provided)",
                "description": "string (auto-generated if not provided)",
                "min_score": "number (required)",
                "max_score": "number (required)",
                "currency_rate": "number (required)",
                "priority": "number (default: 0)",
                "active": "boolean (default: true)",
                "created_at": "string (ISO format)",
                "updated_at": "string (ISO format)"
            }
        },
        "query_parameters": {
            "game_mode": "Filter by game mode (endless, time_trial, survival, etc.)",
            "limit": "Limit number of results (default: 50 for scores, 100 for leaderboard)",
            "sort_by": "Field to sort by (default: 'score_value')",
            "sort_order": "Sort order: 'desc' or 'asc' (default: 'desc')",
            "time_period": "Time filter: 'all', 'daily', 'weekly', 'monthly' (default: 'all')"
        }
    }
    return jsonify(docs)

# Player Data Routes (based on system_id)
@app.route("/api/player/<system_id>", methods=["GET"])
def get_player_data(system_id):
    """Get player data by system_id"""
    if mongo is None or luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        player = luna_db.PlayerData.find_one({"system_id": system_id}, {"_id": 0})
        if not player:
            return jsonify({"error": "Player not found"}), 404
        return jsonify({"player": player})
    except Exception as e:
        logger.error(f"Error fetching player data: {str(e)}")
        return jsonify({"error": "Failed to retrieve player data"}), 500

@app.route("/api/player", methods=["POST"])
def create_player_data():
    """Create new player data with system_id"""
    if mongo is None or luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    data = request.json or {}
    
    # Validate system_id
    system_id = data.get("system_id")
    is_valid_system_id, system_id_error = validate_system_id(system_id)
    if not is_valid_system_id:
        return jsonify({"error": system_id_error}), 400
    
    player_data = data.get("player_data", {})
    game_settings = data.get("game_settings", {})
    
    try:
        # Check if player already exists
        existing_player = luna_db.PlayerData.find_one({"system_id": system_id})
        if existing_player:
            return jsonify({"error": "Player with this system_id already exists"}), 409
        
        player_doc = PlayerDataSchema.create_player(system_id, player_data, game_settings)
        result = luna_db.PlayerData.insert_one(player_doc)
        
        return jsonify({
            "message": "Player created successfully",
            "player": player_doc
        }), 201
    except Exception as e:
        logger.error(f"Error creating player: {str(e)}")
        return jsonify({"error": "Failed to create player"}), 500

@app.route("/api/player/<system_id>", methods=["PUT"])
def update_player_data(system_id):
    """Update player data by system_id"""
    if mongo is None or luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    data = request.json or {}
    
    try:
        # Check if player exists
        existing_player = luna_db.PlayerData.find_one({"system_id": system_id})
        if not existing_player:
            return jsonify({"error": "Player not found"}), 404
        
        # Prepare update data
        update_data = PlayerDataSchema.update_player(
            system_id,
            data.get("player_data"),
            data.get("game_settings"),
            data.get("is_first_time")
        )
        
        result = luna_db.PlayerData.update_one(
            {"system_id": system_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            # Get updated player data
            updated_player = luna_db.PlayerData.find_one({"system_id": system_id}, {"_id": 0})
            return jsonify({
                "message": "Player updated successfully",
                "player": updated_player
            })
        else:
            return jsonify({"error": "No changes made"}), 400
            
    except Exception as e:
        logger.error(f"Error updating player: {str(e)}")
        return jsonify({"error": "Failed to update player"}), 500

@app.route("/api/player/<system_id>", methods=["DELETE"])
def delete_player_data(system_id):
    """Delete player data by system_id"""
    if mongo is None or luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        result = luna_db.PlayerData.delete_one({"system_id": system_id})
        
        if result.deleted_count > 0:
            # Also delete associated scores
            luna_db.GameScores.delete_many({"system_id": system_id})
            return jsonify({"message": "Player and associated data deleted successfully"})
        else:
            return jsonify({"error": "Player not found"}), 404
            
    except Exception as e:
        logger.error(f"Error deleting player: {str(e)}")
        return jsonify({"error": "Failed to delete player"}), 500

# Game Score Routes (based on system_id)
@app.route("/api/scores", methods=["POST"])
def save_game_score():
    """Save a game score for a player by system_id"""
    if mongo is None or luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    data = request.json or {}
    
    # Validate system_id
    system_id = data.get("system_id")
    is_valid_system_id, system_id_error = validate_system_id(system_id)
    if not is_valid_system_id:
        return jsonify({"error": system_id_error}), 400
    
    # Validate score data
    is_valid_score, score_errors = validate_score_data(data)
    if not is_valid_score:
        return jsonify({"error": "Validation failed", "details": score_errors}), 400
    
    score_value = data.get("score_value")
    
    try:
        # Check if player exists
        player = luna_db.PlayerData.find_one({"system_id": system_id})
        if not player:
            return jsonify({"error": "Player not found. Please create player data first."}), 404
        
        # Create score document
        score_doc = GameScoreSchema.create_score(
            system_id=system_id,
            score_value=score_value,
            time_played=data.get("time_played"),
            enemies_killed=data.get("enemies_killed"),
            items_collected=data.get("items_collected"),
            max_combo=data.get("max_combo"),
            survival_time=data.get("survival_time")
        )
        
        result = luna_db.GameScores.insert_one(score_doc)
        
        return jsonify({
            "message": "Score saved successfully",
            "score": score_doc
        }), 201
        
    except Exception as e:
        logger.error(f"Error saving score: {str(e)}")
        return jsonify({"error": "Failed to save score"}), 500

@app.route("/api/scores/<system_id>", methods=["GET"])
def get_player_scores(system_id):
    """Get all scores for a player by system_id"""
    if mongo is None or luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        # Optional query parameters
        game_mode = request.args.get("game_mode")
        limit = int(request.args.get("limit", 50))
        sort_by = request.args.get("sort_by", "score_value")
        sort_order = -1 if request.args.get("sort_order", "desc") == "desc" else 1
        
        # Build query
        query = {"system_id": system_id}
        if game_mode:
            query["game_mode"] = game_mode
        
        # Get scores
        scores = list(luna_db.GameScores.find(query, {"_id": 0})
                     .sort(sort_by, sort_order)
                     .limit(limit))
        
        return jsonify({
            "scores": scores,
            "count": len(scores),
            "system_id": system_id
        })
        
    except Exception as e:
        logger.error(f"Error fetching player scores: {str(e)}")
        return jsonify({"error": "Failed to retrieve player scores"}), 500

@app.route("/api/scores/<system_id>/best", methods=["GET"])
def get_player_best_score(system_id):
    """Get the best score for a player by system_id"""
    if mongo is None or luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        game_mode = request.args.get("game_mode")
        
        # Build query
        query = {"system_id": system_id}
        if game_mode:
            query["game_mode"] = game_mode
        
        # Get best score
        best_score = luna_db.GameScores.find_one(query, {"_id": 0}, sort=[("score_value", -1)])
        
        if not best_score:
            return jsonify({"error": "No scores found for this player"}), 404
        
        return jsonify({
            "best_score": best_score,
            "system_id": system_id
        })
        
    except Exception as e:
        logger.error(f"Error fetching best score: {str(e)}")
        return jsonify({"error": "Failed to retrieve best score"}), 500

@app.route("/api/scores/<system_id>/stats", methods=["GET"])
def get_player_score_stats(system_id):
    """Get score statistics for a player by system_id"""
    if mongo is None or luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        game_mode = request.args.get("game_mode")
        
        # Build query
        query = {"system_id": system_id}
        if game_mode:
            query["game_mode"] = game_mode
        
        # Get all scores for statistics
        scores = list(luna_db.GameScores.find(query, {"score_value": 1, "created_at": 1}))
        
        if not scores:
            return jsonify({"error": "No scores found for this player"}), 404
        
        # Calculate statistics
        score_values = [score["score_value"] for score in scores]
        total_scores = len(score_values)
        best_score = max(score_values)
        worst_score = min(score_values)
        average_score = sum(score_values) / total_scores
        
        # Get recent scores (last 10)
        recent_scores = sorted(scores, key=lambda x: x["created_at"], reverse=True)[:10]
        
        return jsonify({
            "system_id": system_id,
            "total_scores": total_scores,
            "best_score": best_score,
            "worst_score": worst_score,
            "average_score": round(average_score, 2),
            "recent_scores": recent_scores
        })
        
    except Exception as e:
        logger.error(f"Error calculating score stats: {str(e)}")
        return jsonify({"error": "Failed to calculate score statistics"}), 500

# Leaderboard Routes
@app.route("/api/leaderboard", methods=["GET"])
def get_leaderboard():
    """Get global leaderboard for all players"""
    if mongo is None or luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        # Query parameters
        game_mode = request.args.get("game_mode")
        limit = int(request.args.get("limit", 100))
        time_period = request.args.get("time_period", "all")  # all, daily, weekly, monthly
        
        # Build query
        query = {}
        if game_mode:
            query["game_mode"] = game_mode
        
        # Add time filter if specified
        if time_period != "all":
            now = datetime.utcnow()
            if time_period == "daily":
                start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif time_period == "weekly":
                start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
                start_time = start_time.replace(day=start_time.day - start_time.weekday())
            elif time_period == "monthly":
                start_time = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            query["created_at"] = {"$gte": start_time.isoformat()}
        
        # Get top scores with player data
        pipeline = [
            {"$match": query},
            {"$sort": {"score_value": -1}},
            {"$limit": limit},
            {
                "$lookup": {
                    "from": "PlayerData",
                    "localField": "system_id",
                    "foreignField": "system_id",
                    "as": "player_info"
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "score_id": 1,
                    "system_id": 1,
                    "score_value": 1,
                    "game_mode": 1,
                    "level": 1,
                    "time_played": 1,
                    "enemies_killed": 1,
                    "items_collected": 1,
                    "created_at": 1,
                    "player_name": {"$arrayElemAt": ["$player_info.player_data.game_name", 0]},
                    "first_name": {"$arrayElemAt": ["$player_info.player_data.first_name", 0]},
                    "last_name": {"$arrayElemAt": ["$player_info.player_data.last_name", 0]}
                }
            }
        ]
        
        leaderboard = list(luna_db.GameScores.aggregate(pipeline))
        
        return jsonify({
            "leaderboard": leaderboard,
            "count": len(leaderboard),
            "game_mode": game_mode,
            "time_period": time_period,
            "limit": limit
        })
        
    except Exception as e:
        logger.error(f"Error fetching leaderboard: {str(e)}")
        return jsonify({"error": "Failed to retrieve leaderboard"}), 500

@app.route("/api/leaderboard/<system_id>/rank", methods=["GET"])
def get_player_rank(system_id):
    """Get player's rank in the leaderboard"""
    if mongo is None or luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        game_mode = request.args.get("game_mode")
        time_period = request.args.get("time_period", "all")
        
        # Build query
        query = {}
        if game_mode:
            query["game_mode"] = game_mode
        
        # Add time filter if specified
        if time_period != "all":
            now = datetime.utcnow()
            if time_period == "daily":
                start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif time_period == "weekly":
                start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
                start_time = start_time.replace(day=start_time.day - start_time.weekday())
            elif time_period == "monthly":
                start_time = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            query["created_at"] = {"$gte": start_time.isoformat()}
        
        # Get player's best score
        player_query = {**query, "system_id": system_id}
        player_best = luna_db.GameScores.find_one(player_query, sort=[("score_value", -1)])
        
        if not player_best:
            return jsonify({"error": "No scores found for this player"}), 404
        
        # Count players with higher scores
        higher_scores_count = luna_db.GameScores.count_documents({
            **query,
            "score_value": {"$gt": player_best["score_value"]}
        })
        
        # Get total players
        total_players = luna_db.GameScores.count_documents(query)
        
        rank = higher_scores_count + 1
        percentile = round((1 - (rank - 1) / total_players) * 100, 2) if total_players > 0 else 0
        
        return jsonify({
            "system_id": system_id,
            "rank": rank,
            "total_players": total_players,
            "percentile": percentile,
            "best_score": player_best["score_value"],
            "game_mode": game_mode,
            "time_period": time_period
        })
        
    except Exception as e:
        logger.error(f"Error calculating player rank: {str(e)}")
        return jsonify({"error": "Failed to calculate player rank"}), 500

# User Routes
@app.route("/api/users", methods=["GET"])
def get_users():
    if mongo is None or luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        users = list(luna_db.Users.find({}, {"_id": 0}))
        return jsonify({"users": users, "count": len(users)})
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        return jsonify({"error": "Failed to retrieve users"}), 500

@app.route("/api/users", methods=["POST"])
def create_user():
    if mongo is None or luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    data = request.json or {}
    
    # Generate random data if not provided
    username = data.get("username") or generate_random_username()
    email = data.get("email") or generate_random_email()
    system_id = data.get("system_id")
    user_type = data.get("user_type", "player")
    is_active = data.get("is_active", True)
    
    try:
        user_data = UserSchema.create_user(username, email, system_id, user_type, is_active)
        result = luna_db.Users.insert_one(user_data)
        
        return jsonify({
            "message": "User created successfully",
            "user": user_data
        }), 201
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return jsonify({"error": "Failed to create user"}), 500

@app.route("/api/users/<user_id>", methods=["GET"])
def get_user(user_id):
    if mongo is None or luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        user = luna_db.Users.find_one({"user_id": ObjectId(user_id)}, {"_id": 0})
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify({"user": user})
    except Exception as e:
        logger.error(f"Error fetching user: {str(e)}")
        return jsonify({"error": "Failed to retrieve user"}), 500

# Score Routes
@app.route("/api/scores", methods=["GET"])
def get_scores():
    if mongo is None or luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        scores = list(luna_db.Scores.find({}, {"_id": 0}))
        return jsonify({"scores": scores, "count": len(scores)})
    except Exception as e:
        logger.error(f"Error fetching scores: {str(e)}")
        return jsonify({"error": "Failed to retrieve scores"}), 500

@app.route("/api/scores", methods=["POST"])
def create_score():
    if mongo is None or luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    data = request.json or {}
    
    # Generate random data if not provided
    user_id = data.get("user_id") or ObjectId()
    score_value = data.get("score_value") or random.randint(100, 10000)
    game_mode = data.get("game_mode") or generate_random_game_mode()
    
    try:
        score_data = ScoreSchema.create_score(user_id, score_value, game_mode)
        result = luna_db.Scores.insert_one(score_data)
        
        return jsonify({
            "message": "Score created successfully",
            "score": score_data
        }), 201
    except Exception as e:
        logger.error(f"Error creating score: {str(e)}")
        return jsonify({"error": "Failed to create score"}), 500

@app.route("/api/scores/user/<user_id>", methods=["GET"])
def get_user_scores(user_id):
    if mongo is None or luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        scores = list(luna_db.Scores.find({"user_id": ObjectId(user_id)}, {"_id": 0}))
        return jsonify({"scores": scores, "count": len(scores)})
    except Exception as e:
        logger.error(f"Error fetching user scores: {str(e)}")
        return jsonify({"error": "Failed to retrieve user scores"}), 500

# Currency Transaction Routes
@app.route("/api/transactions", methods=["GET"])
def get_transactions():
    if mongo is None or luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        transactions = list(luna_db.CurrencyTransactions.find({}, {"_id": 0}))
        return jsonify({"transactions": transactions, "count": len(transactions)})
    except Exception as e:
        logger.error(f"Error fetching transactions: {str(e)}")
        return jsonify({"error": "Failed to retrieve transactions"}), 500

@app.route("/api/users/<user_id>/currency", methods=["GET"])
def get_user_currency(user_id):
    if mongo is None or luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        # Get all transactions for the user
        transactions = list(luna_db.CurrencyTransactions.find({"user_id": ObjectId(user_id)}, {"_id": 0}))
        
        if not transactions:
            return jsonify({"total_currency": 0})
        
        # Calculate total currency
        total_currency = 0
        for transaction in transactions:
            if transaction["type"] in ["earn", "reward", "refund"]:
                total_currency += transaction["amount"]
            elif transaction["type"] in ["spend", "purchase"]:
                total_currency -= transaction["amount"]
                # Ensure currency never goes below 0
                if total_currency < 0:
                    total_currency = 0
        
        return jsonify({"total_currency": total_currency})
        
    except Exception as e:
        logger.error(f"Error calculating user currency: {str(e)}")
        return jsonify({"error": "Failed to calculate user currency"}), 500

@app.route("/api/transactions", methods=["POST"])
def create_transaction():
    if mongo is None or luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    data = request.json or {}
    
    # Generate random data if not provided
    user_id = data.get("user_id") or ObjectId()
    transaction_type = data.get("type") or generate_random_transaction_type()
    amount = data.get("amount") or random.randint(10, 1000)
    source = data.get("source") or generate_random_source()
    reference_id = data.get("reference_id")
    system_id = data.get("system_id")
    
    try:
        transaction_data = CurrencyTransactionSchema.create_transaction(
            user_id, transaction_type, amount, source, reference_id, system_id
        )
        result = luna_db.CurrencyTransactions.insert_one(transaction_data)
        
        return jsonify({
            "message": "Transaction created successfully",
            "transaction": transaction_data
        }), 201
    except Exception as e:
        logger.error(f"Error creating transaction: {str(e)}")
        return jsonify({"error": "Failed to create transaction"}), 500

# Order Routes
@app.route("/api/orders", methods=["GET"])
def get_orders():
    if mongo is None or luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        orders = list(luna_db.Orders.find({}, {"_id": 0}))
        return jsonify({"orders": orders, "count": len(orders)})
    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}")
        return jsonify({"error": "Failed to retrieve orders"}), 500

@app.route("/api/orders", methods=["POST"])
def create_order():
    if mongo is None or luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    data = request.json or {}
    
    # Generate random data if not provided
    user_id = data.get("user_id") or ObjectId()
    item_id = data.get("item_id") or ObjectId()
    quantity = data.get("quantity") or random.randint(1, 5)
    total_cost = data.get("total_cost") or random.randint(50, 500)
    system_id = data.get("system_id")
    status = data.get("status", "pending")
    
    try:
        order_data = OrderSchema.create_order(user_id, item_id, quantity, total_cost, system_id, status)
        result = luna_db.Orders.insert_one(order_data)
        
        return jsonify({
            "message": "Order created successfully",
            "order": order_data
        }), 201
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        return jsonify({"error": "Failed to create order"}), 500

# Item Routes
@app.route("/api/items", methods=["GET"])
def get_items():
    if mongo is None or luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        items = list(luna_db.Items.find({}, {"_id": 0}))
        return jsonify({"items": items, "count": len(items)})
    except Exception as e:
        logger.error(f"Error fetching items: {str(e)}")
        return jsonify({"error": "Failed to retrieve items"}), 500

@app.route("/api/items", methods=["POST"])
def create_item():
    if mongo is None or luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    data = request.json or {}
    
    # Generate random data if not provided
    name = data.get("name") or generate_random_item_name()
    description = data.get("description") or f"A powerful {name.lower()} with mystical properties"
    base_price = data.get("base_price") or random.randint(100, 1000)
    item_type = data.get("item_type", "consumable")
    rarity = data.get("rarity", "common")
    category = data.get("category", "general")
    stackable = data.get("stackable", True)
    max_stack = data.get("max_stack", 99)
    
    try:
        item_data = ItemSchema.create_item(name, description, base_price, item_type, rarity, category, stackable, max_stack)
        result = luna_db.Items.insert_one(item_data)
        
        return jsonify({
            "message": "Item created successfully",
            "item": item_data
        }), 201
    except Exception as e:
        logger.error(f"Error creating item: {str(e)}")
        return jsonify({"error": "Failed to create item"}), 500

# Currency Rules Routes
@app.route("/api/currency-rules", methods=["GET"])
def get_currency_rules():
    if mongo is None or luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        rules = list(luna_db.CurrencyRules.find({}, {"_id": 0}))
        return jsonify({"currency_rules": rules, "count": len(rules)})
    except Exception as e:
        logger.error(f"Error fetching currency rules: {str(e)}")
        return jsonify({"error": "Failed to retrieve currency rules"}), 500

@app.route("/api/currency-rules", methods=["POST"])
def create_currency_rule():
    if mongo is None or luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    data = request.json or {}
    
    # Generate random data if not provided
    min_score = data.get("min_score") or random.randint(0, 1000)
    max_score = data.get("max_score") or random.randint(min_score + 100, 10000)
    currency_rate = data.get("currency_rate") or round(random.uniform(0.1, 2.0), 2)
    active = data.get("active", True)
    rule_name = data.get("rule_name")
    description = data.get("description")
    priority = data.get("priority", 0)
    
    try:
        rule_data = CurrencyRuleSchema.create_rule(min_score, max_score, currency_rate, active, rule_name, description, priority)
        result = luna_db.CurrencyRules.insert_one(rule_data)
        
        return jsonify({
            "message": "Currency rule created successfully",
            "rule": rule_data
        }), 201
    except Exception as e:
        logger.error(f"Error creating currency rule: {str(e)}")
        return jsonify({"error": "Failed to create currency rule"}), 500

@app.route("/api/currency/calculate", methods=["POST"])
def calculate_currency():
    """Calculate currency reward based on score"""
    if luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        data = request.get_json()
        if not data or "score" not in data:
            return jsonify({"error": "Score is required"}), 400
        
        score = data["score"]
        system_id = data.get("system_id")
        
        # Get active currency rules sorted by priority
        rules = list(luna_db.CurrencyRules.find(
            {"active": True}, 
            {"_id": 0}
        ).sort("priority", 1))
        
        # Find matching rule
        matching_rule = None
        for rule in rules:
            if rule["min_score"] <= score <= rule["max_score"]:
                matching_rule = rule
                break
        
        if not matching_rule:
            return jsonify({
                "currency_earned": 0,
                "rule_applied": None,
                "message": "No matching currency rule found"
            }), 200
        
        # Calculate currency
        currency_earned = int(score * matching_rule["currency_rate"])
        
        # If system_id provided, add currency to player
        if system_id:
            # Get current player data
            player = luna_db.PlayerData.find_one({"system_id": system_id})
            if player:
                current_currency = player.get("currency", 0)
                new_currency = current_currency + currency_earned
                
                # Update player currency
                luna_db.PlayerData.update_one(
                    {"system_id": system_id},
                    {
                        "$set": {
                            "currency": new_currency,
                            "updated_at": datetime.utcnow().isoformat()
                        }
                    }
                )
                
                # Log currency transaction
                transaction_data = CurrencyTransactionSchema.create_transaction(
                    user_id=system_id,
                    transaction_type="earned",
                    amount=currency_earned,
                    source="game_score",
                    system_id=system_id
                )
                luna_db.CurrencyTransactions.insert_one(transaction_data)
        
        return jsonify({
            "currency_earned": currency_earned,
            "rule_applied": matching_rule["rule_name"],
            "currency_rate": matching_rule["currency_rate"],
            "total_currency": new_currency if system_id else None
        }), 200
        
    except Exception as e:
        logger.error(f"Error calculating currency: {str(e)}")
        return jsonify({"error": "Failed to calculate currency"}), 500

@app.route("/api/currency-rules/cleanup", methods=["DELETE"])
def cleanup_currency_rules():
    """Clean up invalid currency rules"""
    if luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        # Delete all existing currency rules
        result = luna_db.CurrencyRules.delete_many({})
        
        # Create proper currency rules
        rules = [
            {"min_score": 0, "max_score": 500, "currency_rate": 0.1, "rule_name": "Beginner", "priority": 1},
            {"min_score": 501, "max_score": 1000, "currency_rate": 0.15, "rule_name": "Intermediate", "priority": 2},
            {"min_score": 1001, "max_score": 2000, "currency_rate": 0.2, "rule_name": "Advanced", "priority": 3},
            {"min_score": 2001, "max_score": 999999, "currency_rate": 0.25, "rule_name": "Expert", "priority": 4}
        ]
        
        created_rules = []
        for rule in rules:
            rule_data = CurrencyRuleSchema.create_rule(
                rule["min_score"], 
                rule["max_score"], 
                rule["currency_rate"], 
                True, 
                rule["rule_name"], 
                f"Currency reward for {rule['rule_name'].lower()} tier players", 
                rule["priority"]
            )
            luna_db.CurrencyRules.insert_one(rule_data)
            created_rules.append(rule_data)
        
        return jsonify({
            "message": f"Cleaned up {result.deleted_count} rules and created {len(created_rules)} new rules",
            "rules": created_rules
        }), 200
        
    except Exception as e:
        logger.error(f"Error cleaning up currency rules: {str(e)}")
        return jsonify({"error": "Failed to cleanup currency rules"}), 500

@app.route("/api/items", methods=["POST"])
def create_shop_item():
    """Create a new item in the shop"""
    if luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        item_data = ItemSchema.create_item(
            name=data.get("name"),
            description=data.get("description"),
            price=data.get("price", 0),
            item_type=data.get("item_type", "consumable"),
            effect=data.get("effect", {}),
            rarity=data.get("rarity", "common"),
            active=data.get("active", True)
        )
        
        result = luna_db.Items.insert_one(item_data)
        
        return jsonify({
            "message": "Item created successfully",
            "item": item_data
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating item: {str(e)}")
        return jsonify({"error": "Failed to create item"}), 500

@app.route("/api/items", methods=["GET"])
def get_shop_items():
    """Get all items from the shop"""
    if luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        items = list(luna_db.Items.find({"is_active": True}, {"_id": 0}))
        return jsonify({
            "items": items,
            "count": len(items)
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving items: {str(e)}")
        return jsonify({"error": "Failed to retrieve items"}), 500

@app.route("/api/shop/purchase", methods=["POST"])
def purchase_shop_item():
    """Purchase an item with currency"""
    if luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        data = request.get_json()
        if not data or "system_id" not in data or "item_id" not in data:
            return jsonify({"error": "system_id and item_id are required"}), 400
        
        system_id = data["system_id"]
        item_id = data["item_id"]
        quantity = data.get("quantity", 1)
        
        # Get item details
        item = luna_db.Items.find_one({"item_id": ObjectId(item_id), "is_active": True})
        if not item:
            return jsonify({"error": "Item not found"}), 404
        
        # Get player data
        player = luna_db.PlayerData.find_one({"system_id": system_id})
        if not player:
            return jsonify({"error": "Player not found"}), 404
        
        # Calculate total cost
        total_cost = item["base_price"] * quantity
        current_currency = player.get("currency", 0)
        
        if current_currency < total_cost:
            return jsonify({"error": "Insufficient currency"}), 400
        
        # Deduct currency
        new_currency = current_currency - total_cost
        luna_db.PlayerData.update_one(
            {"system_id": system_id},
            {
                "$set": {
                    "currency": new_currency,
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        )
        
        # Log currency transaction
        transaction_data = CurrencyTransactionSchema.create_transaction(
            user_id=system_id,
            transaction_type="spent",
            amount=total_cost,
            source="item_purchase",
            reference_id=item_id,
            system_id=system_id
        )
        luna_db.CurrencyTransactions.insert_one(transaction_data)
        
        # Create order
        order_data = OrderSchema.create_order(
            user_id=system_id,
            item_id=item_id,
            quantity=quantity,
            total_cost=total_cost,
            system_id=system_id,
            status="completed"
        )
        luna_db.Orders.insert_one(order_data)
        
        # Update story progress if heart was purchased
        if item.get("name") == "Heart":
            update_story_progress(system_id, quantity)
        
        return jsonify({
            "message": "Purchase successful",
            "item": {
                "name": item["name"],
                "quantity": quantity,
                "total_cost": total_cost
            },
            "remaining_currency": new_currency
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing purchase: {str(e)}")
        return jsonify({"error": "Failed to process purchase"}), 500

# Random Data Generation Route
@app.route("/api/generate-random-data", methods=["POST"])
def generate_random_data():
    if mongo is None or luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        # Generate exactly 5 users
        users = []
        for i in range(5):
            user_data = UserSchema.create_user(
                generate_random_username(),
                generate_random_email()
            )
            result = luna_db.Users.insert_one(user_data)
            users.append(user_data)
        
        # Generate random scores for each user
        scores = []
        for user in users:
            for _ in range(random.randint(1, 3)):  # 1-3 scores per user
                score_data = ScoreSchema.create_score(
                    user["user_id"],
                    random.randint(100, 10000),
                    generate_random_game_mode()
                )
                luna_db.Scores.insert_one(score_data)
                scores.append(score_data)
        
        # Generate random items
        items = []
        for _ in range(10):  # 10 random items
            item_data = ItemSchema.create_item(
                generate_random_item_name(),
                f"A mystical item with unique properties",
                random.randint(100, 1000)
            )
            luna_db.Items.insert_one(item_data)
            items.append(item_data)
        
        # Generate random transactions
        transactions = []
        for user in users:
            for _ in range(random.randint(2, 5)):  # 2-5 transactions per user
                transaction_data = CurrencyTransactionSchema.create_transaction(
                    user["user_id"],
                    generate_random_transaction_type(),
                    random.randint(10, 1000),
                    generate_random_source()
                )
                luna_db.CurrencyTransactions.insert_one(transaction_data)
                transactions.append(transaction_data)
        
        # Generate random orders
        orders = []
        for user in users:
            for _ in range(random.randint(1, 3)):  # 1-3 orders per user
                order_data = OrderSchema.create_order(
                    user["user_id"],
                    random.choice(items)["item_id"],
                    random.randint(1, 3),
                    random.randint(50, 500)
                )
                luna_db.Orders.insert_one(order_data)
                orders.append(order_data)
        
        # Generate currency rules
        rules = []
        for _ in range(5):  # 5 currency rules
            min_score = random.randint(0, 2000)
            rule_data = CurrencyRuleSchema.create_rule(
                min_score,
                min_score + random.randint(500, 2000),
                round(random.uniform(0.1, 2.0), 2),
                True
            )
            luna_db.CurrencyRules.insert_one(rule_data)
            rules.append(rule_data)
        
        return jsonify({
            "message": "Random data generated successfully",
            "summary": {
                "users": len(users),
                "scores": len(scores),
                "items": len(items),
                "transactions": len(transactions),
                "orders": len(orders),
                "currency_rules": len(rules)
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error generating random data: {str(e)}")
        return jsonify({"error": "Failed to generate random data"}), 500

# Legacy routes for backward compatibility
@app.route("/users")
def list_users():
    if mongo is None:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        docs = list(mongo.db.users.find({}, {"_id": 0}))
        return jsonify(docs)
    except Exception as e:
        return jsonify({"error": "Failed to retrieve users"}), 500

@app.route("/luna/users", methods=["POST"])
def create_luna_user():
    if mongo is None or luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    data = request.json or {}
    
    required_fields = ["name", "email"]
    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    
    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400
    
    try:
        user_data = {
            **data,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        res = luna_db.Users.insert_one(user_data)
        
        return jsonify({
            "message": "Luna user created successfully",
            "user_id": str(res.inserted_id),
            "name": data.get("name"),
            "email": data.get("email")
        }), 201
        
    except Exception as e:
        return jsonify({"error": "Failed to create Luna user"}), 500

@app.route("/luna/users")
def list_luna_users():
    if mongo is None or luna_db is None:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        docs = list(luna_db.Users.find({}, {"_id": 0}))
        return jsonify(docs)
    except Exception as e:
        return jsonify({"error": "Failed to retrieve Luna users"}), 500



if __name__ == "__main__":
    app.run(debug=True)
