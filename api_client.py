"""
API Client for Luna's Endless Lesson Backend Integration
Handles all communication with the backend API for player data and score management
"""

import requests
import json
import logging
from typing import Dict, Optional, List, Any
from settings import GameSettings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LunaAPIClient:
    def __init__(self, base_url: str = "http://localhost:5000"):
        """
        Initialize the API client
        
        Args:
            base_url: Base URL of the backend API
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'LunaGame/1.0'
        })
        
        # Game settings for system_id
        self.game_settings = GameSettings()
        
        # Cache for player data to avoid repeated API calls
        self._player_data_cache = None
        self._cache_timestamp = 0
        self._cache_duration = 300  # 5 minutes
        
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
        """
        Make a request to the API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            
        Returns:
            Response data as dictionary
            
        Raises:
            APIError: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url)
            else:
                raise APIError(f"Unsupported HTTP method: {method}")
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Return JSON response
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise APIError(f"API request failed: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise APIError(f"Invalid JSON response: {str(e)}")
    
    def get_system_id(self) -> str:
        """Get the system ID from game settings"""
        return self.game_settings.get_system_id()
    
    def create_or_update_player(self, player_data: Optional[Dict] = None, game_settings: Optional[Dict] = None) -> Dict:
        """
        Create or update player data
        
        Args:
            player_data: Player information dictionary
            game_settings: Game settings dictionary
            
        Returns:
            Player data from API
        """
        system_id = self.get_system_id()
        
        # Use provided data or get from game settings
        if player_data is None:
            player_data = self.game_settings.get_player_data()
        if game_settings is None:
            game_settings = self.game_settings.settings_data.get('game_settings', {})
        
        # Get current player data
        try:
            current_player = self.get_player_data()
            # Update existing player with current data
            update_data = {
                'player_data': player_data,
                'game_settings': game_settings
            }
            return self._make_request('PUT', f'/api/player/{system_id}', data=update_data)
            
        except APIError as e:
            if "not found" in str(e).lower():
                # Player doesn't exist, create new one
                create_data = {
                    'system_id': system_id,
                    'player_data': player_data,
                    'game_settings': game_settings
                }
                return self._make_request('POST', '/api/player', data=create_data)
            else:
                raise e
    
    def get_player_data(self) -> Dict:
        """
        Get player data by system_id
        
        Returns:
            Player data dictionary
        """
        system_id = self.get_system_id()
        response = self._make_request('GET', f'/api/player/{system_id}')
        return response.get('player', {})
    
    def save_score(self, score_value: int, time_played: Optional[float] = None, 
                   enemies_killed: Optional[int] = None, items_collected: Optional[int] = None,
                   max_combo: Optional[int] = None, survival_time: Optional[float] = None) -> Dict:
        """
        Save a game score
        
        Args:
            score_value: The final score achieved
            time_played: Time played in seconds
            enemies_killed: Number of enemies killed
            items_collected: Number of items collected
            max_combo: Maximum combo achieved
            survival_time: Total survival time in seconds
            
        Returns:
            Score data from API
        """
        system_id = self.get_system_id()
        
        score_data = {
            'system_id': system_id,
            'score_value': score_value,
            'time_played': time_played,
            'enemies_killed': enemies_killed,
            'items_collected': items_collected,
            'max_combo': max_combo,
            'survival_time': survival_time
        }
        
        # Remove None values
        score_data = {k: v for k, v in score_data.items() if v is not None}
        
        return self._make_request('POST', '/api/scores', data=score_data)
    
    def get_player_scores(self, limit: int = 50, sort_by: str = "score_value", sort_order: str = "desc") -> List[Dict]:
        """
        Get player's scores
        
        Args:
            limit: Maximum number of scores to return
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            
        Returns:
            List of score dictionaries
        """
        system_id = self.get_system_id()
        params = {
            'limit': limit,
            'sort_by': sort_by,
            'sort_order': sort_order
        }
        
        response = self._make_request('GET', f'/api/scores/{system_id}', params=params)
        return response.get('scores', [])
    
    def get_best_score(self) -> Optional[Dict]:
        """
        Get player's best score
        
        Returns:
            Best score dictionary or None if no scores
        """
        system_id = self.get_system_id()
        try:
            response = self._make_request('GET', f'/api/scores/{system_id}/best')
            return response.get('best_score')
        except APIError as e:
            if "not found" in str(e).lower():
                return None
            raise e
    
    def get_score_stats(self) -> Optional[Dict]:
        """
        Get player's score statistics
        
        Returns:
            Score statistics dictionary or None if no scores
        """
        system_id = self.get_system_id()
        try:
            response = self._make_request('GET', f'/api/scores/{system_id}/stats')
            return response
        except APIError as e:
            if "not found" in str(e).lower():
                return None
            raise e
    
    def get_leaderboard(self, limit: int = 100, time_period: str = "all") -> List[Dict]:
        """
        Get global leaderboard
        
        Args:
            limit: Maximum number of entries to return
            time_period: Time period filter (all, daily, weekly, monthly)
            
        Returns:
            List of leaderboard entries
        """
        params = {
            'limit': limit,
            'time_period': time_period
        }
        
        response = self._make_request('GET', '/api/leaderboard', params=params)
        return response.get('leaderboard', [])
    
    def get_leaderboard_data(self, limit: int = 10) -> List[Dict]:
        """
        Get leaderboard data (alias for get_leaderboard)
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of leaderboard entries
        """
        return self.get_leaderboard(limit=limit)
    
    def calculate_currency(self, score: int) -> Dict:
        """
        Calculate currency reward based on score
        
        Args:
            score: Player's score
            
        Returns:
            Currency calculation result
        """
        try:
            data = {
                "score": score,
                "system_id": self.get_system_id()
            }
            return self._make_request('POST', '/api/currency/calculate', data=data)
        except APIError as e:
            logger.error(f"Failed to calculate currency: {e}")
            return {
                "currency_earned": 0,
                "rule_applied": None,
                "message": f"Currency calculation failed: {e}"
            }
    
    def get_shop_items(self) -> Dict:
        """
        Get all available shop items
        
        Returns:
            List of shop items
        """
        try:
            return self._make_request('GET', '/api/items')
        except APIError as e:
            logger.error(f"Failed to get shop items: {e}")
            return {"items": [], "count": 0, "error": str(e)}
    
    def purchase_item(self, item_id: str, quantity: int = 1) -> Dict:
        """
        Purchase an item from the shop
        
        Args:
            item_id: ID of the item to purchase
            quantity: Number of items to purchase
            
        Returns:
            Purchase result
        """
        try:
            data = {
                "system_id": self.get_system_id(),
                "item_id": item_id,
                "quantity": quantity
            }
            return self._make_request('POST', '/api/shop/purchase', data=data)
        except APIError as e:
            logger.error(f"Failed to purchase item: {e}")
            return {"success": False, "error": str(e)}
    
    def get_player_rank(self, time_period: str = "all") -> Optional[Dict]:
        """
        Get player's rank in leaderboard
        
        Args:
            time_period: Time period filter (all, daily, weekly, monthly)
            
        Returns:
            Player rank information or None if no scores
        """
        system_id = self.get_system_id()
        try:
            params = {'time_period': time_period}
            response = self._make_request('GET', f'/api/leaderboard/{system_id}/rank', params=params)
            return response
        except APIError as e:
            if "not found" in str(e).lower():
                return None
            raise e
    
    def get_player_stats(self) -> Optional[Dict]:
        """
        Get player statistics from API
        
        Returns:
            Player statistics dictionary or None if no scores
        """
        system_id = self.get_system_id()
        try:
            response = self._make_request('GET', f'/api/scores/{system_id}/stats')
            return response
        except APIError as e:
            if "not found" in str(e).lower():
                return None
            raise e
    
    def test_connection(self) -> bool:
        """
        Test connection to the API
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self.session.get(f"{self.base_url}/")
            response.raise_for_status()
            return True
        except Exception:
            return False
    
    def initialize_game_data(self) -> Dict:
        """
        Initialize all game data for a new player session
        
        Returns:
            Dictionary with initialization status
        """
        try:
            # Test API connection first
            if not self.test_connection():
                return {"success": False, "error": "API not available"}
            
            # Get or create player data
            player_data = self.create_or_update_player()
            
            # Get player statistics
            stats = self.get_player_stats()
            
            # Get leaderboard data
            leaderboard = self.get_leaderboard_data(limit=10)
            
            return {
                "success": True,
                "player_data": player_data,
                "stats": stats,
                "leaderboard": leaderboard,
                "api_connected": True
            }
            
        except Exception as e:
            logger.error(f"Failed to initialize game data: {e}")
            return {
                "success": False,
                "error": str(e),
                "api_connected": False
            }
    
    def save_game_session(self, score_data: Dict) -> Dict:
        """
        Save a complete game session with all data
        
        Args:
            score_data: Dictionary containing all game session data
            
        Returns:
            Dictionary with save status
        """
        try:
            # Save the main score
            score_result = self.save_score(**score_data)
            
            # Update player's last played time
            self.update_player_last_played()
            
            return {
                "success": True,
                "score_saved": True,
                "score_data": score_result
            }
            
        except Exception as e:
            logger.error(f"Failed to save game session: {e}")
            return {
                "success": False,
                "error": str(e),
                "score_saved": False
            }
    
    def update_player_last_played(self) -> bool:
        """
        Update player's last played timestamp
        
        Returns:
            True if successful, False otherwise
        """
        try:
            system_id = self.get_system_id()
            update_data = {
                "last_played": True  # This will trigger last_played update
            }
            self._make_request('PUT', f'/api/player/{system_id}', data=update_data)
            return True
        except Exception as e:
            logger.error(f"Failed to update last played: {e}")
            return False
    
    def get_player_progress(self) -> Dict:
        """
        Get comprehensive player progress data
        
        Returns:
            Dictionary with player progress information
        """
        try:
            system_id = self.get_system_id()
            
            # Get player data
            player_data = self.get_player_data()
            
            # Get score statistics
            stats = self.get_score_stats()
            
            # Get recent scores
            recent_scores = self.get_player_scores(limit=10)
            
            # Get player rank
            rank_data = self.get_player_rank()
            
            return {
                "success": True,
                "player_data": player_data,
                "stats": stats,
                "recent_scores": recent_scores,
                "rank": rank_data
            }
            
        except Exception as e:
            logger.error(f"Failed to get player progress: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_cached_player_data(self) -> Optional[Dict]:
        """
        Get cached player data if available and not expired
        
        Returns:
            Cached player data or None
        """
        import time
        current_time = time.time()
        
        if (self._player_data_cache and 
            current_time - self._cache_timestamp < self._cache_duration):
            return self._player_data_cache
        
        return None
    
    def cache_player_data(self, player_data: Dict) -> None:
        """
        Cache player data with timestamp
        
        Args:
            player_data: Player data to cache
        """
        import time
        self._player_data_cache = player_data
        self._cache_timestamp = time.time()
    
    def clear_cache(self) -> None:
        """Clear all cached data"""
        self._player_data_cache = None
        self._cache_timestamp = 0

class APIError(Exception):
    """Custom exception for API errors"""
    pass

# Global API client instance
api_client = LunaAPIClient()

def get_api_client() -> LunaAPIClient:
    """Get the global API client instance"""
    return api_client

def test_api_connection() -> bool:
    """Test API connection and return status"""
    try:
        return api_client.test_connection()
    except Exception as e:
        logger.error(f"API connection test failed: {e}")
        return False
