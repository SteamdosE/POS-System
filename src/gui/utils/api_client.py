"""
API Client for POS System GUI
Handles all communication with Flask backend API
"""
import requests
import json
from typing import Optional, Dict, List, Any
from ..config import API_BASE_URL, API_TIMEOUT

class APIError(Exception):
    """Custom exception for API errors"""
    pass

class APIClient:
    """
    Client for communicating with POS System Flask API
    Manages JWT authentication and all CRUD operations
    """
    
    def __init__(self):
        self.base_url = API_BASE_URL
        self.timeout = API_TIMEOUT
        self.token = None
        self.user_data = None
    
    def _headers(self) -> Dict[str, str]:
        """Get headers with authorization token"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to API"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, headers=self._headers(), timeout=self.timeout)
            elif method == "POST":
                response = requests.post(url, headers=self._headers(), json=data, timeout=self.timeout)
            elif method == "PUT":
                response = requests.put(url, headers=self._headers(), json=data, timeout=self.timeout)
            elif method == "DELETE":
                response = requests.delete(url, headers=self._headers(), timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise APIError("Request timeout - server not responding")
        except requests.exceptions.ConnectionError:
            raise APIError("Connection error - cannot reach server")
        except requests.exceptions.HTTPError as e:
            raise APIError(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise APIError(f"Request failed: {str(e)}")
    
    # Authentication Methods
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Login user and get JWT token"""
        data = {"username": username, "password": password}
        response = self._request("POST", "/auth/login", data)
        self.token = response.get("token")
        self.user_data = response.get("user")
        return response
    
    def register(self, username: str, email: str, password: str, role: str = "cashier") -> Dict[str, Any]:
        """Register new user"""
        data = {"username": username, "email": email, "password": password, "role": role}
        return self._request("POST", "/auth/register", data)
    
    def logout(self):
        """Clear local token"""
        self.token = None
        self.user_data = None
    
    # Product Methods
    def get_products(self, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        """Get paginated list of products"""
        return self._request("GET", f"/products?page={page}&limit={limit}")
    
    def get_product(self, product_id: int) -> Dict[str, Any]:
        """Get single product by ID"""
        return self._request("GET", f"/products/{product_id}")
    
    def create_product(self, name: str, price: float, category: str, quantity: int, 
                      barcode: str = "", sku: str = "") -> Dict[str, Any]:
        """Create new product"""
        data = {
            "name": name,
            "price": price,
            "category": category,
            "quantity": quantity,
            "barcode": barcode,
            "sku": sku
        }
        return self._request("POST", "/products", data)
    
    def update_product(self, product_id: int, **kwargs) -> Dict[str, Any]:
        """Update product"""
        return self._request("PUT", f"/products/{product_id}", kwargs)
    
    def delete_product(self, product_id: int) -> Dict[str, Any]:
        """Delete product"""
        return self._request("DELETE", f"/products/{product_id}")
    
    # Sales Methods
    def create_sale(self, items: List[Dict], discount: float = 0, 
                   payment_method: str = "cash", customer_id: Optional[int] = None) -> Dict[str, Any]:
        """Create new sale"""
        data = {
            "items": items,
            "discount": discount,
            "payment_method": payment_method,
            "customer_id": customer_id
        }
        return self._request("POST", "/sales", data)
    
    def get_sales(self, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        """Get paginated list of sales"""
        return self._request("GET", f"/sales?page={page}&limit={limit}")
    
    def get_sale(self, sale_id: int) -> Dict[str, Any]:
        """Get single sale by ID"""
        return self._request("GET", f"/sales/{sale_id}")
    
    def get_daily_report(self) -> Dict[str, Any]:
        """Get daily sales report"""
        return self._request("GET", "/sales/report/daily")
    
    def get_monthly_report(self) -> Dict[str, Any]:
        """Get monthly sales report"""
        return self._request("GET", "/sales/report/monthly")
    
    # User Methods
    def get_users(self) -> Dict[str, Any]:
        """Get all users"""
        return self._request("GET", "/users")
    
    def get_user(self, user_id: int) -> Dict[str, Any]:
        """Get single user by ID"""
        return self._request("GET", f"/users/{user_id}")
    
    def create_user(self, username: str, email: str, password: str, role: str) -> Dict[str, Any]:
        """Create new user"""
        data = {"username": username, "email": email, "password": password, "role": role}
        return self._request("POST", "/users", data)
    
    def update_user(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Update user"""
        return self._request("PUT", f"/users/{user_id}", kwargs)
    
    def delete_user(self, user_id: int) -> Dict[str, Any]:
        """Delete user"""
        return self._request("DELETE", f"/users/{user_id}")
    
    def is_authenticated(self) -> bool:
        """Check if user is logged in"""
        return self.token is not None