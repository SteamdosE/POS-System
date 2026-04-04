"""
Cashier Screen - Main POS Interface
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from .config import *
from .utils.formatters import format_currency
from .utils.dialogs import show_error, show_success, show_confirmation
from .utils.api_client import APIError

class CashierScreen(tk.Frame):
    """Main cashier POS interface"""
    
    def __init__(self, parent, api_client):
        super().__init__(parent, bg=COLOR_LIGHT)
        self.api_client = api_client
        self.cart_items = []
        self.products = []
        self.setup_ui()
        self.load_products()
    
    def setup_ui(self):
        """Setup cashier screen UI"""
        # Header
        header = tk.Frame(self, bg=COLOR_PRIMARY, height=60)
        header.pack(fill=tk.X)
        
        header_label = tk.Label(header, text="POS - Cashier", font=FONT_HEADING, bg=COLOR_PRIMARY, fg=COLOR_WHITE)
        header_label.pack(pady=10)
        
        # Main content - split into left (products) and right (cart)
        content = tk.Frame(self, bg=COLOR_LIGHT)
        content.pack(fill=tk.BOTH, expand=True, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
        
        # LEFT: Products Section
        products_frame = tk.Frame(content, bg=COLOR_WHITE, relief=tk.RIDGE, bd=1)
        products_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, PADDING_MEDIUM))
        
        tk.Label(products_frame, text="Products", font=FONT_HEADING, bg=COLOR_DARK, fg=COLOR_WHITE).pack(fill=tk.X, padx=5, pady=5)
        
        # Search products
        search_frame = tk.Frame(products_frame, bg=COLOR_WHITE)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(search_frame, text="Search:", bg=COLOR_WHITE).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<KeyRelease>", lambda e: self.filter_products())
        
        # Products listbox
        scrollbar = tk.Scrollbar(products_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.products_listbox = tk.Listbox(products_frame, yscrollcommand=scrollbar.set, font=FONT_NORMAL, height=20)
        self.products_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.config(command=self.products_listbox.yview)
        self.products_listbox.bind("<Double-Button-1>", lambda e: self.add_to_cart())
        
        # RIGHT: Cart Section
        cart_frame = tk.Frame(content, bg=COLOR_WHITE, relief=tk.RIDGE, bd=1)
        cart_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        tk.Label(cart_frame, text="Shopping Cart", font=FONT_HEADING, bg=COLOR_PRIMARY, fg=COLOR_WHITE).pack(fill=tk.X, padx=5, pady=5)
        
        # Cart items tree
        self.cart_tree = ttk.Treeview(cart_frame, columns=("Name", "Qty", "Price", "Total"), height=15)
        self.cart_tree.heading("#0", text="ID")
        self.cart_tree.heading("Name", text="Name")
        self.cart_tree.heading("Qty", text="Qty")
        self.cart_tree.heading("Price", text="Unit Price")
        self.cart_tree.heading("Total", text="Total")
        self.cart_tree.column("#0", width=30)
        self.cart_tree.column("Name", width=100)
        self.cart_tree.column("Qty", width=50)
        self.cart_tree.column("Price", width=70)
        self.cart_tree.column("Total", width=70)
        self.cart_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Cart controls
        cart_controls = tk.Frame(cart_frame, bg=COLOR_WHITE)
        cart_controls.pack(fill=tk.X, padx=5, pady=5)
        
        remove_btn = tk.Button(cart_controls, text="Remove", bg=COLOR_DANGER, fg=COLOR_WHITE, command=self.remove_from_cart, cursor="hand2")
        remove_btn.pack(side=tk.LEFT, padx=2)
        
        clear_btn = tk.Button(cart_controls, text="Clear Cart", bg=COLOR_WARNING, fg=COLOR_WHITE, command=self.clear_cart, cursor="hand2")
        clear_btn.pack(side=tk.LEFT, padx=2)
        
        # Totals section
        totals_frame = tk.Frame(cart_frame, bg=COLOR_LIGHT)
        totals_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(totals_frame, text="Subtotal:", font=FONT_NORMAL, bg=COLOR_LIGHT).grid(row=0, column=0, sticky="w")
        self.subtotal_label = tk.Label(totals_frame, text="$0.00", font=FONT_NORMAL, bg=COLOR_LIGHT, fg=COLOR_SUCCESS)
        self.subtotal_label.grid(row=0, column=1, sticky="e")
        
        tk.Label(totals_frame, text="Discount:", font=FONT_NORMAL, bg=COLOR_LIGHT).grid(row=1, column=0, sticky="w")
        self.discount_entry = tk.Entry(totals_frame, width=15, font=FONT_NORMAL)
        self.discount_entry.insert(0, "0")
        self.discount_entry.grid(row=1, column=1, sticky="e", padx=5)
        self.discount_entry.bind("<KeyRelease>", lambda e: self.update_totals())
        
        tk.Label(totals_frame, text=f"Tax ({TAX_RATE*100:.0f}%):", font=FONT_NORMAL, bg=COLOR_LIGHT).grid(row=2, column=0, sticky="w")
        self.tax_label = tk.Label(totals_frame, text="$0.00", font=FONT_NORMAL, bg=COLOR_LIGHT, fg=COLOR_WARNING)
        self.tax_label.grid(row=2, column=1, sticky="e")
        
        tk.Label(totals_frame, text="Total:", font=("Arial", 12, "bold"), bg=COLOR_LIGHT).grid(row=3, column=0, sticky="w")
        self.total_label = tk.Label(totals_frame, text="$0.00", font=("Arial", 12, "bold"), bg=COLOR_LIGHT, fg=COLOR_DANGER)
        self.total_label.grid(row=3, column=1, sticky="e")
        
        # Checkout section
        checkout_frame = tk.Frame(cart_frame, bg=COLOR_LIGHT)
        checkout_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(checkout_frame, text="Payment Method:", bg=COLOR_LIGHT).pack(side=tk.LEFT)
        self.payment_var = tk.StringVar(value="cash")
        payment_combo = ttk.Combobox(checkout_frame, textvariable=self.payment_var, values=["cash", "card", "mobile"], state="readonly", width=15)
        payment_combo.pack(side=tk.LEFT, padx=5)
        
        checkout_btn = tk.Button(checkout_frame, text="Checkout", bg=COLOR_SUCCESS, fg=COLOR_WHITE, command=self.checkout, cursor="hand2", font=FONT_NORMAL)
        checkout_btn.pack(side=tk.RIGHT, padx=5)
    
    def load_products(self):
        """Load products from API"""
        try:
            response = self.api_client.get_products()
            self.products = response.get("products", [])
            self.display_products()
        except APIError as e:
            show_error("Error", f"Failed to load products: {str(e)}")
    
    def display_products(self):
        """Display products in listbox"""
        self.products_listbox.delete(0, tk.END)
        for product in self.products:
            display_text = f"{product.get('name', '')} - {format_currency(product.get('price', 0))} (Stock: {product.get('quantity', 0)})"
            self.products_listbox.insert(tk.END, display_text)
    
    def filter_products(self):
        """Filter products by search term"""
        search_term = self.search_var.get().lower()
        self.products_listbox.delete(0, tk.END)
        
        for product in self.products:
            if search_term in product.get('name', '').lower():
                display_text = f"{product.get('name', '')} - {format_currency(product.get('price', 0))} (Stock: {product.get('quantity', 0)})"
                self.products_listbox.insert(tk.END, display_text)
    
    def add_to_cart(self):
        """Add selected product to cart"""
        selection = self.products_listbox.curselection()
        if not selection:
            show_error("Error", "Select a product first")
            return
        
        # Find the product
        display_text = self.products_listbox.get(selection[0])
        product_name = display_text.split(" - ")[0]
        
        product = next((p for p in self.products if p['name'] == product_name), None)
        if not product:
            show_error("Error", "Product not found")
            return
        
        # Check if product already in cart
        cart_item = next((item for item in self.cart_items if item['id'] == product['id']), None)
        if cart_item:
            cart_item['qty'] += 1
        else:
            self.cart_items.append({
                'id': product['id'],
                'name': product['name'],
                'price': product['price'],
                'qty': 1
            })
        
        self.update_cart_display()
        self.update_totals()
    
    def remove_from_cart(self):
        """Remove selected item from cart"""
        selection = self.cart_tree.selection()
        if not selection:
            show_error("Error", "Select an item to remove")
            return
        
        item = self.cart_tree.item(selection[0])
        product_id = int(item["text"])
        self.cart_items = [item for item in self.cart_items if item['id'] != product_id]
        self.update_cart_display()
        self.update_totals()
    
    def clear_cart(self):
        """Clear entire cart"""
        if show_confirmation("Confirm", "Clear all items from cart?"):
            self.cart_items = []
            self.update_cart_display()
            self.update_totals()
    
    def update_cart_display(self):
        """Update cart display in tree"""
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        
        for item in self.cart_items:
            total = item['price'] * item['qty']
            self.cart_tree.insert("", tk.END, text=item['id'], values=(
                item['name'],
                item['qty'],
                format_currency(item['price']),
                format_currency(total)
            ))
    
    def update_totals(self):
        """Update total calculations"""
        if not self.cart_items:
            self.subtotal_label.config(text="$0.00")
            self.tax_label.config(text="$0.00")
            self.total_label.config(text="$0.00")
            return
        
        subtotal = sum(item['price'] * item['qty'] for item in self.cart_items)
        
        try:
            discount = float(self.discount_entry.get() or 0)
        except ValueError:
            discount = 0
            self.discount_entry.delete(0, tk.END)
            self.discount_entry.insert(0, "0")
        
        tax = (subtotal - discount) * TAX_RATE
        total = subtotal - discount + tax
        
        self.subtotal_label.config(text=format_currency(subtotal))
        self.tax_label.config(text=format_currency(tax))
        self.total_label.config(text=format_currency(total))
    
    def checkout(self):
        """Process checkout and create sale"""
        if not self.cart_items:
            show_error("Error", "Cart is empty")
            return
        
        try:
            # Calculate totals
            subtotal = sum(item['price'] * item['qty'] for item in self.cart_items)
            discount = float(self.discount_entry.get() or 0)
            tax = (subtotal - discount) * TAX_RATE
            total = subtotal - discount + tax
            payment_method = self.payment_var.get()
            
            # Prepare sale data
            sale_data = {
                "items": [
                    {
                        "product_id": item['id'],
                        "quantity": item['qty'],
                        "unit_price": item['price']
                    }
                    for item in self.cart_items
                ],
                "discount": discount,
                "payment_method": payment_method
            }
            
            # Create sale in API
            response = self.api_client.create_sale(sale_data)
            sale_id = response.get('id', 'N/A')
            
            # Generate receipt
            from .utils.receipt import Receipt
            receipt = Receipt(sale_id, self.cart_items, subtotal, tax, total, discount, payment_method)
            receipt_text = receipt.generate_text_receipt()
            
            # Show receipt dialog
            from .utils.receipt_dialog import ReceiptDialog
            ReceiptDialog(self.master, receipt_text)
            
            # Clear cart
            self.cart_items = []
            self.update_cart_display()
            self.update_totals()
            self.discount_entry.delete(0, tk.END)
            self.discount_entry.insert(0, "0")
            
            # Reload products (to refresh stock)
            self.load_products()
            
            show_success("Success", f"Sale completed! Receipt ID: {sale_id}")
        
        except ValueError as e:
            show_error("Error", "Invalid discount amount")
        except APIError as e:
            show_error("Error", f"Failed to process sale: {str(e)}")
        except Exception as e:
            show_error("Error", f"Unexpected error: {str(e)}")
