import os
import logging
import random
import string
from datetime import datetime
from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from dotenv import load_dotenv
from bson import ObjectId

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

# MongoDB Schema Definitions
class UserSchema:
    @staticmethod
    def create_user(username, email):
        return {
            "user_id": ObjectId(),
            "username": username,
            "email": email,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

class ScoreSchema:
    @staticmethod
    def create_score(user_id, score_value, game_mode):
        return {
            "score_id": ObjectId(),
            "user_id": user_id,
            "score_value": score_value,
            "game_mode": game_mode,
            "created_at": datetime.utcnow().isoformat()
        }

class CurrencyTransactionSchema:
    @staticmethod
    def create_transaction(user_id, transaction_type, amount, source, reference_id=None):
        return {
            "transaction_id": ObjectId(),
            "user_id": user_id,
            "type": transaction_type,
            "amount": amount,
            "source": source,
            "reference_id": reference_id,
            "created_at": datetime.utcnow().isoformat()
        }

class OrderSchema:
    @staticmethod
    def create_order(user_id, item_id, quantity, total_cost):
        return {
            "order_id": ObjectId(),
            "user_id": user_id,
            "item_id": item_id,
            "quantity": quantity,
            "total_cost": total_cost,
            "created_at": datetime.utcnow().isoformat()
        }

class ItemSchema:
    @staticmethod
    def create_item(name, description, base_price):
        return {
            "item_id": ObjectId(),
            "name": name,
            "description": description,
            "base_price": base_price,
            "created_at": datetime.utcnow().isoformat()
        }

class CurrencyRuleSchema:
    @staticmethod
    def create_rule(min_score, max_score, currency_rate, active=True):
        return {
            "rule_id": ObjectId(),
            "min_score": min_score,
            "max_score": max_score,
            "currency_rate": currency_rate,
            "active": active,
            "created_at": datetime.utcnow().isoformat()
        }



# API Routes
@app.route("/")
def home():
    return "Luna's Endless Lesson Backend is running!"

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
    
    try:
        user_data = UserSchema.create_user(username, email)
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
    
    try:
        transaction_data = CurrencyTransactionSchema.create_transaction(
            user_id, transaction_type, amount, source, reference_id
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
    
    try:
        order_data = OrderSchema.create_order(user_id, item_id, quantity, total_cost)
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
    
    try:
        item_data = ItemSchema.create_item(name, description, base_price)
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
    
    try:
        rule_data = CurrencyRuleSchema.create_rule(min_score, max_score, currency_rate, active)
        result = luna_db.CurrencyRules.insert_one(rule_data)
        
        return jsonify({
            "message": "Currency rule created successfully",
            "rule": rule_data
        }), 201
    except Exception as e:
        logger.error(f"Error creating currency rule: {str(e)}")
        return jsonify({"error": "Failed to create currency rule"}), 500

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
