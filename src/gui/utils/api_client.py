"""API client for POS System GUI and NiceGUI frontend."""

import requests
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

    @staticmethod
    def _extract_items(response: Dict[str, Any], key: str) -> List[Dict[str, Any]]:
        """Support both legacy and envelope API response shapes."""
        if isinstance(response.get(key), list):
            return response.get(key, [])
        data = response.get("data") or {}
        if isinstance(data, dict):
            if isinstance(data.get(key), list):
                return data.get(key, [])
            if isinstance(data.get("items"), list):
                return data.get("items", [])
        return []
    
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
        payload = response.get("data") or {}
        self.token = payload.get("access_token")
        self.user_data = payload.get("user")
        return response
    
    def register(self, username: str, email: str, password: str, role: str = "cashier") -> Dict[str, Any]:
        """Register new user"""
        data = {"username": username, "email": email, "password": password, "role": role}
        return self._request("POST", "/auth/register", data)

    def forgot_password(self, username: str, email: str, new_password: str) -> Dict[str, Any]:
        """Reset a user's password with username and email verification."""
        data = {"username": username, "email": email, "new_password": new_password}
        return self._request("POST", "/auth/forgot-password", data)
    
    def logout(self):
        """Clear local token"""
        self.token = None
        self.user_data = None
    
    # Product Methods
    def get_products(self, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Get paginated list of products"""
        response = self._request("GET", f"/products?page={page}&per_page={per_page}")
        response["products"] = self._extract_items(response, "products")
        return response
    
    def get_product(self, product_id: int) -> Dict[str, Any]:
        """Get single product by ID"""
        return self._request("GET", f"/products/{product_id}")
    
    def create_product(
        self,
        name: str,
        sku: str,
        price: float,
        quantity_in_stock: int = 0,
        category: str = "",
        description: str = "",
    ) -> Dict[str, Any]:
        """Create new product."""
        data = {
            "name": name,
            "sku": sku,
            "price": price,
            "category": category,
            "quantity_in_stock": quantity_in_stock,
            "description": description,
        }
        return self._request("POST", "/products", data)
    
    def update_product(self, product_id: int, **kwargs) -> Dict[str, Any]:
        """Update product"""
        return self._request("PUT", f"/products/{product_id}", kwargs)
    
    def delete_product(self, product_id: int) -> Dict[str, Any]:
        """Delete product"""
        return self._request("DELETE", f"/products/{product_id}")

    # Category Methods
    def get_categories(self) -> Dict[str, Any]:
        """Get list of product categories."""
        response = self._request("GET", "/categories")
        response["categories"] = self._extract_items(response, "categories")
        return response

    def create_category(self, name: str) -> Dict[str, Any]:
        """Create a product category."""
        return self._request("POST", "/categories", {"name": name})

    def update_category(self, category_id: int, name: str) -> Dict[str, Any]:
        """Rename a product category."""
        return self._request("PUT", f"/categories/{category_id}", {"name": name})

    def delete_category(self, category_id: int) -> Dict[str, Any]:
        """Delete a product category."""
        return self._request("DELETE", f"/categories/{category_id}")
    
    # Sales Methods
    def create_sale(self, items: List[Dict], discount: float = 0, 
                   payment_method: str = "cash", customer_id: Optional[int] = None) -> Dict[str, Any]:
        """Create new sale"""
        if isinstance(items, dict):
            data = items
        else:
            data = {
                "items": items,
                "discount": discount,
                "payment_method": payment_method,
                "customer_id": customer_id,
            }
        return self._request("POST", "/sales", data)
    
    def get_sales(self, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Get paginated list of sales."""
        response = self._request("GET", f"/sales?page={page}&per_page={per_page}")
        response["sales"] = self._extract_items(response, "sales")
        return response
    
    def get_sale(self, sale_id: int) -> Dict[str, Any]:
        """Get single sale by ID"""
        return self._request("GET", f"/sales/{sale_id}")
    
    def get_daily_report(self) -> Dict[str, Any]:
        """Get daily sales report"""
        return self._request("GET", "/sales/report/daily")
    
    def get_monthly_report(self) -> Dict[str, Any]:
        """Get monthly sales report"""
        return self._request("GET", "/sales/report/monthly")

    # Customer Methods
    def get_customers(self, page: int = 1, per_page: int = 100, search: str = "") -> Dict[str, Any]:
        """Get paginated list of customers."""
        endpoint = f"/customers?page={page}&per_page={per_page}"
        if search:
            endpoint += f"&search={search}"
        response = self._request("GET", endpoint)
        response["customers"] = self._extract_items(response, "customers")
        return response

    def create_customer(self, name: str, phone_number: str = "", email: str = "", address: str = "") -> Dict[str, Any]:
        """Create new customer profile."""
        data = {
            "name": name,
            "phone_number": phone_number,
            "email": email,
            "address": address,
        }
        return self._request("POST", "/customers", data)

    def update_customer(self, customer_id: int, **kwargs) -> Dict[str, Any]:
        """Update customer profile."""
        return self._request("PUT", f"/customers/{customer_id}", kwargs)

    def delete_customer(self, customer_id: int) -> Dict[str, Any]:
        """Soft-delete customer profile."""
        return self._request("DELETE", f"/customers/{customer_id}")

    def get_customer_history(self, customer_id: int) -> Dict[str, Any]:
        """Get purchase history for customer."""
        return self._request("GET", f"/customers/{customer_id}/history")

    # Payment Methods
    def get_payments(self, page: int = 1, per_page: int = 50) -> Dict[str, Any]:
        """Get paginated payment records."""
        response = self._request("GET", f"/payments?page={page}&per_page={per_page}")
        response["payments"] = self._extract_items(response, "payments")
        return response

    def get_sale_payments(self, sale_id: int) -> Dict[str, Any]:
        """Get payments for a sale."""
        response = self._request("GET", f"/payments/sale/{sale_id}")
        response["payments"] = self._extract_items(response, "payments")
        return response

    def initialize_paystack_payment(
        self,
        amount: float,
        customer_name: str,
        method: str,
        email: str = "",
        phone: str = "",
        callback_url: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Initialize a Paystack transaction."""
        data: Dict[str, Any] = {
            "amount": amount,
            "customer_name": customer_name,
            "method": method,
        }
        if email:
            data["email"] = email
        if phone:
            data["phone"] = phone
        if callback_url:
            data["callback_url"] = callback_url
        if metadata:
            data["metadata"] = metadata
        return self._request("POST", "/payments/paystack/initialize", data)

    def verify_paystack_payment(self, reference: str) -> Dict[str, Any]:
        """Verify a Paystack transaction by reference."""
        return self._request("GET", f"/payments/paystack/verify/{reference}")
    
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

    # Paystack Payment Methods
    def initialize_paystack_payment(self, email: str, amount: float,
                                    reference: Optional[str] = None) -> Dict[str, Any]:
        """Initialize a Paystack transaction.

        Args:
            email: Customer e-mail address.
            amount: Amount in the local currency unit (e.g. KES).
            reference: Optional custom reference string.

        Returns:
            dict with ``authorization_url``, ``access_code``, and ``reference``.
        """
        data: Dict[str, Any] = {"email": email, "amount": amount}
        if reference:
            data["reference"] = reference
        return self._request("POST", "/payments/paystack/initialize", data)

    def verify_paystack_payment(self, reference: str) -> Dict[str, Any]:
        """Verify a Paystack transaction by its reference.

        Args:
            reference: The reference returned by :meth:`initialize_paystack_payment`.

        Returns:
            dict with ``status``, ``reference``, ``amount``, ``currency``,
            ``paid_at``, and ``channel``.
        """
        return self._request("GET", f"/payments/paystack/verify/{reference}")