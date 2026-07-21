"""Monday.com GraphQL API client for fetching board data.

This module provides a MondayClient class that handles all interactions
with the Monday.com platform via GraphQL API, including connection testing,
board fetching, pagination, and error handling.
"""

import requests
import logging
from typing import Dict, List, Optional, Any, Tuple
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MondayClient:
    """Client for interacting with Monday.com GraphQL API.
    
    This class handles authentication, GraphQL queries, pagination,
    and error handling for Monday.com board operations.
    """
    
    # GraphQL query for testing connection
    TEST_QUERY = """
    query {
        me {
            id
            name
        }
    }
    """
    
    # GraphQL query for fetching board items with pagination
    FETCH_ITEMS_QUERY = """
    query ($boardId: ID!, $limit: Int!, $cursor: String) {
        boards(ids: [$boardId]) {
            name
            columns {
                id
                title
            }
            items_page(limit: $limit, cursor: $cursor) {
                cursor
                items {
                    id
                    name
                    column_values {
                        id
                        text
                        value
                    }
                }
            }
        }
    }
    """
    
    def __init__(self):
        """Initialize Monday.com client with configuration.
        
        Raises:
            ValueError: If required configuration values are missing.
        """
        self.api_token = Config.MONDAY_API_TOKEN
        self.api_url = Config.MONDAY_API_URL
        self.deals_board_id = Config.DEALS_BOARD_ID
        self.work_orders_board_id = Config.WORK_ORDERS_BOARD_ID
        
        # Validate configuration
        if not self.api_token:
            raise ValueError("MONDAY_API_TOKEN is not configured")
        if not self.api_url:
            raise ValueError("MONDAY_API_URL is not configured")
        if not self.deals_board_id:
            raise ValueError("DEALS_BOARD_ID is not configured")
        if not self.work_orders_board_id:
            raise ValueError("WORK_ORDERS_BOARD_ID is not configured")
        
        # Request headers
        self.headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json"
        }
        
        logger.info("Connecting to Monday.com API...")
    
    def test_connection(self) -> bool:
        """Test connection to Monday.com API.
        
        Returns:
            bool: True if connection is successful, False otherwise.
        """
        try:
            logger.info("Testing Monday.com API connection...")
            response = self._execute_query(self.TEST_QUERY)
            
            if response and "me" in response:
                user_name = response.get("me", {}).get("name", "Unknown")
                logger.info(f"Connection successful. Authenticated as: {user_name}")
                return True
            else:
                logger.error("Connection test failed: Invalid response format")
                return False
                
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def fetch_deals(self) -> Dict[str, Any]:
        """Fetch all deals from the Deals board.
        
        Returns:
            dict: Structured data containing deals or error information.
        """
        logger.info(f"Fetching deals from board ID: {self.deals_board_id}")
        try:
            items = self._fetch_board_items(self.deals_board_id)
            logger.info(f"Successfully fetched {len(items)} deals")
            return {
                "success": True,
                "board_id": self.deals_board_id,
                "board_name": "Deals",
                "item_count": len(items),
                "items": items
            }
        except Exception as e:
            error_msg = f"Failed to fetch deals: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "board_id": self.deals_board_id,
                "board_name": "Deals",
                "error": error_msg
            }
    
    def fetch_work_orders(self) -> Dict[str, Any]:
        """Fetch all work orders from the Work Orders board.
        
        Returns:
            dict: Structured data containing work orders or error information.
        """
        logger.info(f"Fetching work orders from board ID: {self.work_orders_board_id}")
        try:
            items = self._fetch_board_items(self.work_orders_board_id)
            logger.info(f"Successfully fetched {len(items)} work orders")
            return {
                "success": True,
                "board_id": self.work_orders_board_id,
                "board_name": "Work Orders",
                "item_count": len(items),
                "items": items
            }
        except Exception as e:
            error_msg = f"Failed to fetch work orders: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "board_id": self.work_orders_board_id,
                "board_name": "Work Orders",
                "error": error_msg
            }
    
    def fetch_all(self) -> Dict[str, Any]:
        """Fetch all data from both Deals and Work Orders boards.
        
        Returns:
            dict: Combined structured data from both boards.
        """
        logger.info("Fetching all board data...")
        deals = self.fetch_deals()
        work_orders = self.fetch_work_orders()
        
        return {
            "deals": deals,
            "work_orders": work_orders,
            "timestamp": self._get_timestamp()
        }
    
    def _fetch_board_items(self, board_id: str) -> List[Dict[str, Any]]:
        """Fetch all items from a board with pagination handling.
        
        Args:
            board_id: Monday.com board ID.
            
        Returns:
            list: List of items from the board.
            
        Raises:
            ValueError: If board not found.
            requests.exceptions.RequestException: If API request fails.
        """
        all_items = []
        cursor = None
        page_number = 0
        
        while True:
            page_number += 1
            logger.info(f"Fetching page {page_number} from board {board_id}...")
            
            # Prepare variables
            variables = {
                "boardId": board_id,
                "limit": 50,  # Monday.com maximum per page
                "cursor": cursor
            }
            
            # Execute query
            response = self._execute_query(self.FETCH_ITEMS_QUERY, variables)
            
            # Validate response
            if not response or "boards" not in response:
                raise ValueError(f"Invalid response format for board {board_id}")
            
            boards = response.get("boards", [])
            if not boards:
                raise ValueError(f"Board {board_id} not found or not accessible")
            
            board = boards[0]
            board_columns = board.get("columns", [])
            items_page = board.get("items_page", {})
            items = items_page.get("items", [])
            
            # Build column schema map: {column_id: {id, title}}
            column_schema = {col.get("id"): col for col in board_columns}
            
            # Format and add items
            for item in items:
                formatted_item = {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "columns": self._format_columns(item.get("column_values", []), column_schema)
                }
                all_items.append(formatted_item)
            
            logger.info(f"Page {page_number}: Fetched {len(items)} items")
            
            # Check for more pages
            next_cursor = items_page.get("cursor")
            if not next_cursor or not items:
                logger.info(f"Pagination complete for board {board_id}")
                break
            
            cursor = next_cursor
        
        return all_items
    
    def _execute_query(self, query: str, variables: Optional[Dict] = None) -> Optional[Dict]:
        """Execute a GraphQL query against Monday.com API.
        
        Args:
            query: GraphQL query string.
            variables: Optional variables for the query.
            
        Returns:
            dict: Response data from the API.
            
        Raises:
            requests.exceptions.RequestException: If API request fails.
            ValueError: If API returns an error.
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        try:
            response = requests.post(
                self.api_url,
                json=payload,
                headers=self.headers,
                timeout=30
            )
            
            # Check for HTTP errors
            if response.status_code == 401:
                raise ValueError("Authentication failed: Invalid API token")
            elif response.status_code == 429:
                raise ValueError("Rate limit exceeded: Too many requests")
            elif response.status_code >= 500:
                raise ValueError(f"Server error: {response.status_code}")
            elif response.status_code >= 400:
                raise ValueError(f"API error: {response.status_code}")
            
            # Parse JSON response
            response_json = response.json()
            
            # Check for GraphQL errors
            if "errors" in response_json:
                errors = response_json.get("errors", [])
                error_messages = [error.get("message", "Unknown error") for error in errors]
                raise ValueError(f"GraphQL error: {', '.join(error_messages)}")
            
            # Return data
            return response_json.get("data")
            
        except requests.exceptions.Timeout:
            raise ValueError("Request timeout: API took too long to respond")
        except requests.exceptions.ConnectionError:
            raise ValueError("Network error: Could not connect to API")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Request failed: {str(e)}")
    
    @staticmethod
    def _format_columns(column_values: List[Dict], column_schema: Optional[Dict] = None) -> Dict[str, Dict]:
        """Format column values into a structured dictionary.
        
        Args:
            column_values: List of column value objects from API.
            column_schema: Optional dict mapping column IDs to column metadata (id, title).
            
        Returns:
            dict: Formatted columns with id as key, including title from schema.
        """
        if column_schema is None:
            column_schema = {}
            
        formatted = {}
        for col in column_values:
            col_id = col.get("id")
            if col_id:
                # Get title from schema if available
                col_title = column_schema.get(col_id, {}).get("title", "")
                formatted[col_id] = {
                    "title": col_title,
                    "text": col.get("text"),
                    "value": col.get("value")
                }
        return formatted
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp in ISO format.
        
        Returns:
            str: Current timestamp.
        """
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
