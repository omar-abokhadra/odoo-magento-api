import requests
import logging
from typing import Dict, List, Any, Optional, Union
import time

logger = logging.getLogger(__name__)

class MagentoClient:
    """
    Client for interacting with Magento 2.4.7 REST API.
    """
    
    def __init__(self, base_url: str, username: str, password: str):
        """
        Initialize the Magento client with connection parameters.
        
        Args:
            base_url: Magento base URL (e.g., https://example.com)
            username: Magento admin username
            password: Magento admin password
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None
        self.token_expiry = 0
        self.token_lifetime = 3600  # Default token lifetime in seconds (1 hour)
    
    def _get_token(self) -> Optional[str]:
        """
        Get an authentication token from Magento.
        
        Returns:
            Optional[str]: Authentication token if successful, None otherwise
        """
        current_time = time.time()
        
        # Return existing token if it's still valid
        if self.token and current_time < self.token_expiry:
            return self.token
        
        try:
            url = f"{self.base_url}/rest/V1/integration/admin/token"
            headers = {"Content-Type": "application/json"}
            payload = {
                "username": self.username,
                "password": self.password
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            self.token = response.json()
            self.token_expiry = current_time + self.token_lifetime
            logger.info("Successfully obtained Magento authentication token")
            return self.token
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get Magento authentication token: {str(e)}")
            self.token = None
            return None
    
    def _make_api_request(self, method: str, endpoint: str, data: Any = None, params: Dict = None) -> Optional[Any]:
        """
        Make an API request to Magento.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request data for POST/PUT requests
            params: Query parameters
            
        Returns:
            Optional[Any]: Response data if successful, None otherwise
        """
        token = self._get_token()
        if not token:
            logger.error("Cannot make API request without authentication token")
            return None
        
        try:
            url = f"{self.base_url}{endpoint}"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
            
            response = requests.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers
            )
            response.raise_for_status()
            
            if response.content:
                return response.json()
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Magento API request failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}, Response body: {e.response.text}")
            return None
    
    def get_product_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """
        Get product information by SKU.
        
        Args:
            sku: Product SKU
            
        Returns:
            Optional[Dict[str, Any]]: Product information or None if not found
        """
        endpoint = f"/rest/V1/products/{sku}"
        return self._make_api_request("GET", endpoint)
    
    def update_product_stock(self, sku: str, quantity: float) -> bool:
        """
        Update product stock quantity.
        
        Args:
            sku: Product SKU
            quantity: New stock quantity
            
        Returns:
            bool: True if update is successful, False otherwise
        """
        endpoint = f"/rest/V1/products/{sku}/stockItems/1"
        data = {
            "stockItem": {
                "qty": quantity,
                "is_in_stock": quantity > 0
            }
        }
        result = self._make_api_request("PUT", endpoint, data)
        return result is not None
    
    def update_product_price(self, sku: str, price: float) -> bool:
        """
        Update product regular price.
        
        Args:
            sku: Product SKU
            price: New product price
            
        Returns:
            bool: True if update is successful, False otherwise
        """
        endpoint = f"/rest/V1/products/{sku}"
        data = {
            "product": {
                "price": price
            }
        }
        result = self._make_api_request("PUT", endpoint, data)
        return result is not None
    
    def update_product_special_price(self, sku: str, special_price: float, 
                                    from_date: str = None, to_date: str = None) -> bool:
        """
        Update product special price (advanced price).
        
        Args:
            sku: Product SKU
            special_price: Special price value
            from_date: Start date for special price (format: YYYY-MM-DD)
            to_date: End date for special price (format: YYYY-MM-DD)
            
        Returns:
            bool: True if update is successful, False otherwise
        """
        endpoint = f"/rest/V1/products/{sku}"
        data = {
            "product": {
                "custom_attributes": [
                    {
                        "attribute_code": "special_price",
                        "value": str(special_price)
                    }
                ]
            }
        }
        
        # Add date range if provided
        if from_date:
            data["product"]["custom_attributes"].append({
                "attribute_code": "special_from_date",
                "value": from_date
            })
        
        if to_date:
            data["product"]["custom_attributes"].append({
                "attribute_code": "special_to_date",
                "value": to_date
            })
        
        result = self._make_api_request("PUT", endpoint, data)
        return result is not None
    
    def get_orders(self, page_size: int = 10, current_page: int = 1, 
                  status: str = None) -> Optional[Dict[str, Any]]:
        """
        Get orders from Magento.
        
        Args:
            page_size: Number of orders per page
            current_page: Current page number
            status: Filter by order status (e.g., 'pending', 'processing')
            
        Returns:
            Optional[Dict[str, Any]]: Orders data if successful, None otherwise
        """
        endpoint = "/rest/V1/orders"
        params = {
            "searchCriteria[pageSize]": page_size,
            "searchCriteria[currentPage]": current_page
        }
        
        # Add status filter if provided
        if status:
            params["searchCriteria[filterGroups][0][filters][0][field]"] = "status"
            params["searchCriteria[filterGroups][0][filters][0][value]"] = status
            params["searchCriteria[filterGroups][0][filters][0][conditionType]"] = "eq"
        
        return self._make_api_request("GET", endpoint, params=params)
    
    def get_order_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get order details by ID.
        
        Args:
            order_id: Magento order ID
            
        Returns:
            Optional[Dict[str, Any]]: Order details if successful, None otherwise
        """
        endpoint = f"/rest/V1/orders/{order_id}"
        return self._make_api_request("GET", endpoint)
    
    def get_new_orders(self) -> List[Dict[str, Any]]:
        """
        Get new orders that need to be synchronized.
        
        Returns:
            List[Dict[str, Any]]: List of new orders
        """
        # Get orders with status 'pending' or 'processing'
        pending_orders = self.get_orders(status="pending")
        processing_orders = self.get_orders(status="processing")
        
        orders = []
        
        if pending_orders and 'items' in pending_orders:
            orders.extend(pending_orders['items'])
        
        if processing_orders and 'items' in processing_orders:
            orders.extend(processing_orders['items'])
        
        return orders
