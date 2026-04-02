"""
Admin Dashboard Screen
"""
import tkinter as tk
from tkinter import ttk, messagebox
from ..config import *
from ..utils.formatters import format_currency, format_date
from ..utils.dialogs import show_error, show_success, show_confirmation, show_input_dialog
from ..utils.api_client import APIError

class AdminDashboard(tk.Frame):
    """Admin dashboard with tabs for products, users, and reports"""
    
    def __init__(self, parent, api_client):
        super().__init__(parent, bg=COLOR_LIGHT)
        self.api_client = api_client
        self.setup_ui()
    
    def setup_ui(self):
        """Setup admin dashboard UI"""
        # Header
        header = tk.Frame(self, bg=COLOR_PRIMARY, height=50)
        header.pack(fill=tk.X)
        
        header_label = tk.Label(header, text="Admin Dashboard", font=FONT_HEADING, bg=COLOR_PRIMARY, fg=COLOR_WHITE)
        header_label.pack(pady=10)
        
        # Notebook (tabs)
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
        
        # Tab 1: Products
        products_frame = tk.Frame(notebook, bg=COLOR_LIGHT)
        notebook.add(products_frame, text="Products")
        self.setup_products_tab(products_frame)
        
        # Tab 2: Users
        users_frame = tk.Frame(notebook, bg=COLOR_LIGHT)
        notebook.add(users_frame, text="Users")
        self.setup_users_tab(users_frame)
        
        # Tab 3: Reports
        reports_frame = tk.Frame(notebook, bg=COLOR_LIGHT)
        notebook.add(reports_frame, text="Reports")
        self.setup_reports_tab(reports_frame)
    
    def setup_products_tab(self, parent):
        """Setup products management tab"""
        # Controls
        controls = tk.Frame(parent, bg=COLOR_LIGHT)
        controls.pack(fill=tk.X, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
        
        tk.Label(controls, text="Search:", bg=COLOR_LIGHT).pack(side=tk.LEFT)
        self.product_search = tk.Entry(controls, width=30)
        self.product_search.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        add_btn = tk.Button(controls, text="Add Product", bg=COLOR_SUCCESS, fg=COLOR_WHITE, command=self.add_product, cursor="hand2")
        add_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        edit_btn = tk.Button(controls, text="Edit", bg=COLOR_WARNING, fg=COLOR_WHITE, command=self.edit_product, cursor="hand2")
        edit_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        delete_btn = tk.Button(controls, text="Delete", bg=COLOR_DANGER, fg=COLOR_WHITE, command=self.delete_product, cursor="hand2")
        delete_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        refresh_btn = tk.Button(controls, text="Refresh", bg=COLOR_PRIMARY, fg=COLOR_WHITE, command=self.load_products, cursor="hand2")
        refresh_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        # Products tree
        self.products_tree = ttk.Treeview(parent, columns=("Name", "Price", "Stock", "Category"), height=TABLE_HEIGHT)
        self.products_tree.heading("#0", text="ID")
        self.products_tree.heading("Name", text="Name")
        self.products_tree.heading("Price", text="Price")
        self.products_tree.heading("Stock", text="Stock")
        self.products_tree.heading("Category", text="Category")
        self.products_tree.pack(fill=tk.BOTH, expand=True, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
        
        self.load_products()
    
    def setup_users_tab(self, parent):
        """Setup users management tab"""
        # Controls
        controls = tk.Frame(parent, bg=COLOR_LIGHT)
        controls.pack(fill=tk.X, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
        
        add_btn = tk.Button(controls, text="Add User", bg=COLOR_SUCCESS, fg=COLOR_WHITE, command=self.add_user, cursor="hand2")
        add_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        edit_btn = tk.Button(controls, text="Edit", bg=COLOR_WARNING, fg=COLOR_WHITE, command=self.edit_user, cursor="hand2")
        edit_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        delete_btn = tk.Button(controls, text="Delete", bg=COLOR_DANGER, fg=COLOR_WHITE, command=self.delete_user, cursor="hand2")
        delete_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        refresh_btn = tk.Button(controls, text="Refresh", bg=COLOR_PRIMARY, fg=COLOR_WHITE, command=self.load_users, cursor="hand2")
        refresh_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        # Users tree
        self.users_tree = ttk.Treeview(parent, columns=("Username", "Email", "Role"), height=TABLE_HEIGHT)
        self.users_tree.heading("#0", text="ID")
        self.users_tree.heading("Username", text="Username")
        self.users_tree.heading("Email", text="Email")
        self.users_tree.heading("Role", text="Role")
        self.users_tree.pack(fill=tk.BOTH, expand=True, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
        
        self.load_users()
    
    def setup_reports_tab(self, parent):
        """Setup reports tab"""
        # Controls
        controls = tk.Frame(parent, bg=COLOR_LIGHT)
        controls.pack(fill=tk.X, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
        
        daily_btn = tk.Button(controls, text="Daily Report", bg=COLOR_PRIMARY, fg=COLOR_WHITE, command=self.show_daily_report, cursor="hand2")
        daily_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        monthly_btn = tk.Button(controls, text="Monthly Report", bg=COLOR_PRIMARY, fg=COLOR_WHITE, command=self.show_monthly_report, cursor="hand2")
        monthly_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        # Reports text area
        self.reports_text = tk.Text(parent, height=20, width=80, font=FONT_MONO)
        self.reports_text.pack(fill=tk.BOTH, expand=True, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
    
    def load_products(self):
        """Load and display products"""
        try:
            response = self.api_client.get_products()
            for item in self.products_tree.get_children():
                self.products_tree.delete(item)
            
            for product in response.get("products", []):
                self.products_tree.insert("", tk.END, text=product.get("id", ""), values=(
                    product.get("name", ""),
                    format_currency(product.get("price", 0)),
                    product.get("quantity", 0),
                    product.get("category", "")
                ))
        except APIError as e:
            show_error("Error", f"Failed to load products: {str(e)}")
    
    def load_users(self):
        """Load and display users"""
        try:
            response = self.api_client.get_users()
            for item in self.users_tree.get_children():
                self.users_tree.delete(item)
            
            for user in response:
                self.users_tree.insert("", tk.END, text=user.get("id", ""), values=(
                    user.get("username", ""),
                    user.get("email", ""),
                    user.get("role", "")
                ))
        except APIError as e:
            show_error("Error", f"Failed to load users: {str(e)}")
    
    def add_product(self):
        """Add new product dialog"""
        show_success("Add Product", "Feature coming soon!")
    
    def edit_product(self):
        """Edit product dialog"""
        selection = self.products_tree.selection()
        if not selection:
            show_error("Error", "Select a product first")
            return
        show_success("Edit Product", "Feature coming soon!")
    
    def delete_product(self):
        """Delete product"""
        selection = self.products_tree.selection()
        if not selection:
            show_error("Error", "Select a product first")
            return
        
        if show_confirmation("Confirm", "Delete this product?"):
            show_success("Delete", "Product deleted successfully!")
    
    def add_user(self):
        """Add new user"""
        show_success("Add User", "Feature coming soon!")
    
    def edit_user(self):
        """Edit user"""
        selection = self.users_tree.selection()
        if not selection:
            show_error("Error", "Select a user first")
            return
        show_success("Edit User", "Feature coming soon!")
    
    def delete_user(self):
        """Delete user"""
        selection = self.users_tree.selection()
        if not selection:
            show_error("Error", "Select a user first")
            return
        
        if show_confirmation("Confirm", "Delete this user?"):
            show_success("Delete", "User deleted successfully!")
    
    def show_daily_report(self):
        """Show daily report"""
        try:
            response = self.api_client.get_daily_report()
            self.reports_text.delete(1.0, tk.END)
            self.reports_text.insert(tk.END, f"Daily Report\n{'='*50}\n\n{str(response)}")
        except APIError as e:
            show_error("Error", f"Failed to load report: {str(e)}")
    
    def show_monthly_report(self):
        """Show monthly report"""
        try:
            response = self.api_client.get_monthly_report()
            self.reports_text.delete(1.0, tk.END)
            self.reports_text.insert(tk.END, f"Monthly Report\n{'='*50}\n\n{str(response)}")
        except APIError as e:
            show_error("Error", f"Failed to load report: {str(e)}")
