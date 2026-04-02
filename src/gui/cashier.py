"""
Cashier Screen - Main POS Interface
"""
import tkinter as tk
from tkinter import ttk, messagebox
from .config import *
from .utils.formatters import format_currency
from .utils.validators import validate_price, validate_quantity
from .utils.dialogs import show_error, show_success, show_confirmation
from .utils.api_client import APIError

class CashierScreen(tk.Frame):
    """Main cashier/POS interface"""
    
    def __init__(self, parent, api_client):
        super().__init__(parent, bg=COLOR_LIGHT)
        self.api_client = api_client
        self.cart_items = []
        self.products = []
        self.setup_ui()
        self.load_products()
    
    def setup_ui(self):
        """Setup cashier UI"""
        # Header
        header = tk.Frame(self, bg=COLOR_PRIMARY, height=50)
        header.pack(fill=tk.X)
        
        header_label = tk.Label(header, text="Cashier - POS System", font=FONT_HEADING, bg=COLOR_PRIMARY, fg=COLOR_WHITE)
        header_label.pack(pady=10)
        
        # Main content area
        content = tk.Frame(self, bg=COLOR_LIGHT)
        content.pack(fill=tk.BOTH, expand=True, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
        
        # Left side - Products
        left_frame = tk.LabelFrame(content, text="Products", font=FONT_HEADING, bg=COLOR_LIGHT, fg=COLOR_DARK)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=PADDING_MEDIUM)
        
        search_frame = tk.Frame(left_frame, bg=COLOR_LIGHT)
        search_frame.pack(fill=tk.X, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
        
        tk.Label(search_frame, text="Search:", bg=COLOR_LIGHT).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_products)
        search_entry = tk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, padx=PADDING_SMALL, fill=tk.X, expand=True)
        
        # Products listbox
        self.products_tree = ttk.Treeview(left_frame, columns=("Name", "Price", "Stock"), height=TABLE_HEIGHT)
        self.products_tree.heading("#0", text="ID")
        self.products_tree.heading("Name", text="Product")
        self.products_tree.heading("Price", text="Price")
        self.products_tree.heading("Stock", text="Stock")
        self.products_tree.column("#0", width=30)
        self.products_tree.column("Name", width=150)
        self.products_tree.column("Price", width=80)
        self.products_tree.column("Stock", width=60)
        self.products_tree.pack(fill=tk.BOTH, expand=True, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
        self.products_tree.bind("<Double-1>", self.add_to_cart_from_tree)
        
        # Right side - Cart
        right_frame = tk.LabelFrame(content, text="Shopping Cart", font=FONT_HEADING, bg=COLOR_LIGHT, fg=COLOR_DARK)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=PADDING_MEDIUM)
        
        # Cart items
        self.cart_tree = ttk.Treeview(right_frame, columns=("Qty", "Price", "Subtotal"), height=TABLE_HEIGHT)
        self.cart_tree.heading("#0", text="Product")
        self.cart_tree.heading("Qty", text="Qty")
        self.cart_tree.heading("Price", text="Unit Price")
        self.cart_tree.heading("Subtotal", text="Subtotal")
        self.cart_tree.pack(fill=tk.BOTH, expand=True, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
        
        # Cart summary
        summary_frame = tk.Frame(right_frame, bg=COLOR_LIGHT)
        summary_frame.pack(fill=tk.X, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
        
        tk.Label(summary_frame, text="Subtotal:", font=FONT_NORMAL, bg=COLOR_LIGHT).pack()
        self.subtotal_label = tk.Label(summary_frame, text=format_currency(0), font=FONT_HEADING, bg=COLOR_LIGHT, fg=COLOR_SUCCESS)
        self.subtotal_label.pack()
        
        tk.Label(summary_frame, text=f"Tax ({TAX_RATE*100:.0f}%):", font=FONT_NORMAL, bg=COLOR_LIGHT).pack()
        self.tax_label = tk.Label(summary_frame, text=format_currency(0), font=FONT_HEADING, bg=COLOR_LIGHT, fg=COLOR_WARNING)
        self.tax_label.pack()
        
        tk.Label(summary_frame, text="Total:", font=FONT_NORMAL, bg=COLOR_LIGHT).pack()
        self.total_label = tk.Label(summary_frame, text=format_currency(0), font=("Helvetica", 14, "bold"), bg=COLOR_LIGHT, fg=COLOR_DANGER)
        self.total_label.pack()
        
        # Checkout section
        checkout_frame = tk.Frame(self, bg=COLOR_LIGHT)
        checkout_frame.pack(fill=tk.X, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
        
        tk.Label(checkout_frame, text="Payment Method:", bg=COLOR_LIGHT).pack(side=tk.LEFT, padx=PADDING_SMALL)
        self.payment_var = tk.StringVar(value="cash")
        payment_combo = ttk.Combobox(checkout_frame, textvariable=self.payment_var, values=["cash", "card", "mobile"], state="readonly")
        payment_combo.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        tk.Label(checkout_frame, text="Discount:", bg=COLOR_LIGHT).pack(side=tk.LEFT, padx=PADDING_SMALL)
        self.discount_var = tk.StringVar(value="0")
        discount_entry = tk.Entry(checkout_frame, textvariable=self.discount_var, width=10)
        discount_entry.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        checkout_btn = tk.Button(checkout_frame, text="Checkout", bg=COLOR_SUCCESS, fg=COLOR_WHITE, command=self.checkout, cursor="hand2")
        checkout_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        clear_btn = tk.Button(checkout_frame, text="Clear Cart", bg=COLOR_WARNING, fg=COLOR_WHITE, command=self.clear_cart, cursor="hand2")
        clear_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
    
    def load_products(self):
        """Load products from API"""
        try:
            response = self.api_client.get_products()
            self.products = response.get("products", [])
            self.display_products(self.products)
        except APIError as e:
            show_error("Error", f"Failed to load products: {str(e)}")
    
    def display_products(self, products):
        """Display products in tree"""
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        for product in products:
            self.products_tree.insert("", tk.END, text=product.get("id", ""), values=(
                product.get("name", ""),
                format_currency(product.get("price", 0)),
                product.get("quantity", 0)
            ))
    
    def filter_products(self, *args):
        """Filter products based on search"""
        search_term = self.search_var.get().lower()
        filtered = [p for p in self.products if search_term in p.get("name", "").lower()]
        self.display_products(filtered)
    
    def add_to_cart_from_tree(self, event):
        """Add selected product to cart"""
        selection = self.products_tree.selection()
        if not selection:
            return
        
        item = self.products_tree.item(selection[0])
        product_id = item["text"]
        product_name = item["values"][0]
        product_price = float(item["values"][1].replace("Ksh ", "").replace(",", ""))
        
        self.add_to_cart(product_id, product_name, product_price)
    
    def add_to_cart(self, product_id, name, price):
        """Add item to cart"""
        for item in self.cart_items:
            if item["id"] == product_id:
                item["qty"] += 1
                self.update_cart_display()
                return
        
        self.cart_items.append({
            "id": product_id,
            "name": name,
            "price": price,
            "qty": 1
        })
        self.update_cart_display()
    
    def update_cart_display(self):
        """Update cart display and totals"""
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        
        subtotal = 0
        for item in self.cart_items:
            subtotal_item = item["price"] * item["qty"]
            subtotal += subtotal_item
            self.cart_tree.insert("", tk.END, text=item["name"], values=(
                item["qty"],
                format_currency(item["price"]),
                format_currency(subtotal_item)
            ))
        
        tax = subtotal * TAX_RATE
        total = subtotal + tax
        
        self.subtotal_label.config(text=format_currency(subtotal))
        self.tax_label.config(text=format_currency(tax))
        self.total_label.config(text=format_currency(total))
    
    def clear_cart(self):
        """Clear shopping cart"""
        if show_confirmation("Confirm", "Clear entire cart?"):
            self.cart_items = []
            self.update_cart_display()
    
    def checkout(self):
        """Process checkout"""
        if not self.cart_items:
            show_error("Error", "Cart is empty")
            return
        
        try:
            items = [{"product_id": item["id"], "quantity": item["qty"]} for item in self.cart_items]
            discount = float(self.discount_var.get()) if self.discount_var.get() else 0
            payment_method = self.payment_var.get()
            
            response = self.api_client.create_sale(items, discount, payment_method)
            show_success("Success", f"Sale completed! ID: {response.get('id', 'N/A')}")
            self.cart_items = []
            self.update_cart_display()
        except APIError as e:
            show_error("Error", f"Checkout failed: {str(e)}")
