"""
Complete Product Management Screen
"""
import tkinter as tk
from tkinter import ttk, simpledialog
from ..config import *
from ..utils.formatters import format_currency
from ..utils.dialogs import show_error, show_success, show_confirmation
from ..utils.api_client import APIError

class ProductManagement(tk.Frame):
    """Complete product CRUD operations"""
    
    def __init__(self, parent, api_client):
        super().__init__(parent, bg=COLOR_LIGHT)
        self.api_client = api_client
        self.products = []
        self.setup_ui()
        self.load_products()
    
    def setup_ui(self):
        """Setup product management UI"""
        # Header
        header = tk.Frame(self, bg=COLOR_PRIMARY, height=50)
        header.pack(fill=tk.X)
        
        header_label = tk.Label(header, text="Product Management", font=FONT_HEADING, bg=COLOR_PRIMARY, fg=COLOR_WHITE)
        header_label.pack(pady=10)
        
        # Controls
        controls_frame = tk.Frame(self, bg=COLOR_LIGHT)
        controls_frame.pack(fill=tk.X, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
        
        add_btn = tk.Button(controls_frame, text="➕ Add Product", bg=COLOR_SUCCESS, fg=COLOR_WHITE, command=self.add_product_dialog, cursor="hand2")
        add_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        edit_btn = tk.Button(controls_frame, text="✏️ Edit", bg=COLOR_WARNING, fg=COLOR_WHITE, command=self.edit_product_dialog, cursor="hand2")
        edit_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        delete_btn = tk.Button(controls_frame, text="🗑️ Delete", bg=COLOR_DANGER, fg=COLOR_WHITE, command=self.delete_product, cursor="hand2")
        delete_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        refresh_btn = tk.Button(controls_frame, text="🔄 Refresh", bg=COLOR_PRIMARY, fg=COLOR_WHITE, command=self.load_products, cursor="hand2")
        refresh_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        # Products tree
        self.products_tree = ttk.Treeview(self, columns=("Name", "Price", "Stock", "Category", "Barcode"), height=TABLE_HEIGHT)
        self.products_tree.heading("#0", text="ID")
        self.products_tree.heading("Name", text="Product Name")
        self.products_tree.heading("Price", text="Price")
        self.products_tree.heading("Stock", text="Stock")
        self.products_tree.heading("Category", text="Category")
        self.products_tree.heading("Barcode", text="Barcode")
        self.products_tree.pack(fill=tk.BOTH, expand=True, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
    
    def load_products(self):
        """Load products from API"""
        try:
            response = self.api_client.get_products()
            self.products = response.get("products", [])
            self.display_products()
        except APIError as e:
            show_error("Error", f"Failed to load products: {str(e)}")
    
    def display_products(self):
        """Display products in tree"""
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        for product in self.products:
            self.products_tree.insert("", tk.END, text=product.get("id", ""), values=(
                product.get("name", ""),
                format_currency(product.get("price", 0)),
                product.get("quantity", 0),
                product.get("category", "N/A"),
                product.get("barcode", "N/A")
            ))
    
    def add_product_dialog(self):
        """Show add product dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Add Product")
        dialog.geometry("400x500")
        
        # Name
        tk.Label(dialog, text="Product Name:").grid(row=0, column=0, padx=10, pady=5)
        name_entry = tk.Entry(dialog, width=30)
        name_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # Category
        tk.Label(dialog, text="Category:").grid(row=1, column=0, padx=10, pady=5)
        category_entry = tk.Entry(dialog, width=30)
        category_entry.grid(row=1, column=1, padx=10, pady=5)
        
        # Price
        tk.Label(dialog, text="Price:").grid(row=2, column=0, padx=10, pady=5)
        price_entry = tk.Entry(dialog, width=30)
        price_entry.grid(row=2, column=1, padx=10, pady=5)
        
        # Stock
        tk.Label(dialog, text="Initial Stock:").grid(row=3, column=0, padx=10, pady=5)
        stock_entry = tk.Entry(dialog, width=30)
        stock_entry.grid(row=3, column=1, padx=10, pady=5)
        
        # Barcode
        tk.Label(dialog, text="Barcode:").grid(row=4, column=0, padx=10, pady=5)
        barcode_entry = tk.Entry(dialog, width=30)
        barcode_entry.grid(row=4, column=1, padx=10, pady=5)
        
        # Min Stock
        tk.Label(dialog, text="Min Stock Level:").grid(row=5, column=0, padx=10, pady=5)
        min_stock_entry = tk.Entry(dialog, width=30)
        min_stock_entry.insert(0, "10")
        min_stock_entry.grid(row=5, column=1, padx=10, pady=5)
        
        # Max Stock
        tk.Label(dialog, text="Max Stock Level:").grid(row=6, column=0, padx=10, pady=5)
        max_stock_entry = tk.Entry(dialog, width=30)
        max_stock_entry.insert(0, "100")
        max_stock_entry.grid(row=6, column=1, padx=10, pady=5)
        
        def save():
            try:
                data = {
                    "name": name_entry.get(),
                    "category": category_entry.get(),
                    "price": float(price_entry.get()),
                    "quantity": int(stock_entry.get()),
                    "barcode": barcode_entry.get(),
                    "min_stock": int(min_stock_entry.get()),
                    "max_stock": int(max_stock_entry.get())
                }
                
                if not data["name"]:
                    show_error("Error", "Product name required")
                    return
                
                response = self.api_client.create_product(data)
                show_success("Success", "Product added successfully!")
                self.load_products()
                dialog.destroy()
            except ValueError:
                show_error("Error", "Invalid price or stock quantity")
            except APIError as e:
                show_error("Error", f"Failed to add product: {str(e)}")
        
        tk.Button(dialog, text="Save", bg=COLOR_SUCCESS, fg=COLOR_WHITE, command=save).grid(row=7, column=0, columnspan=2, pady=20)
    
    def edit_product_dialog(self):
        """Show edit product dialog"""
        selection = self.products_tree.selection()
        if not selection:
            show_error("Error", "Select a product first")
            return
        
        item = self.products_tree.item(selection[0])
        product_id = item["text"]
        product = next((p for p in self.products if str(p["id"]) == product_id), None)
        
        if not product:
            show_error("Error", "Product not found")
            return
        
        dialog = tk.Toplevel(self)
        dialog.title(f"Edit Product: {product['name']}")
        dialog.geometry("400x500")
        
        # Pre-fill fields
        tk.Label(dialog, text="Product Name:").grid(row=0, column=0, padx=10, pady=5)
        name_entry = tk.Entry(dialog, width=30)
        name_entry.insert(0, product.get("name", ""))
        name_entry.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(dialog, text="Category:").grid(row=1, column=0, padx=10, pady=5)
        category_entry = tk.Entry(dialog, width=30)
        category_entry.insert(0, product.get("category", ""))
        category_entry.grid(row=1, column=1, padx=10, pady=5)
        
        tk.Label(dialog, text="Price:").grid(row=2, column=0, padx=10, pady=5)
        price_entry = tk.Entry(dialog, width=30)
        price_entry.insert(0, str(product.get("price", "")))
        price_entry.grid(row=2, column=1, padx=10, pady=5)
        
        tk.Label(dialog, text="Stock:").grid(row=3, column=0, padx=10, pady=5)
        stock_entry = tk.Entry(dialog, width=30)
        stock_entry.insert(0, str(product.get("quantity", "")))
        stock_entry.grid(row=3, column=1, padx=10, pady=5)
        
        tk.Label(dialog, text="Barcode:").grid(row=4, column=0, padx=10, pady=5)
        barcode_entry = tk.Entry(dialog, width=30)
        barcode_entry.insert(0, product.get("barcode", ""))
        barcode_entry.grid(row=4, column=1, padx=10, pady=5)
        
        def save():
            try:
                data = {
                    "name": name_entry.get(),
                    "category": category_entry.get(),
                    "price": float(price_entry.get()),
                    "quantity": int(stock_entry.get()),
                    "barcode": barcode_entry.get()
                }
                
                response = self.api_client.update_product(product_id, data)
                show_success("Success", "Product updated successfully!")
                self.load_products()
                dialog.destroy()
            except ValueError:
                show_error("Error", "Invalid price or stock quantity")
            except APIError as e:
                show_error("Error", f"Failed to update product: {str(e)}")
        
        tk.Button(dialog, text="Save Changes", bg=COLOR_SUCCESS, fg=COLOR_WHITE, command=save).grid(row=5, column=0, columnspan=2, pady=20)
    
    def delete_product(self):
        """Delete selected product"""
        selection = self.products_tree.selection()
        if not selection:
            show_error("Error", "Select a product first")
            return
        
        item = self.products_tree.item(selection[0])
        product_id = item["text"]
        product_name = item["values"][0]
        
        if show_confirmation("Confirm Delete", f"Delete product '{product_name}'?"):
            try:
                response = self.api_client.delete_product(product_id)
                show_success("Success", "Product deleted successfully!")
                self.load_products()
            except APIError as e:
                show_error("Error", f"Failed to delete product: {str(e)}")
