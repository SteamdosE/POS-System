"""
Inventory Management Screen
"""
import tkinter as tk
from tkinter import ttk, messagebox
from ..config import *
from ..utils.formatters import format_currency
from ..utils.dialogs import show_error, show_success, show_confirmation, show_input_dialog
from ..utils.api_client import APIError

class InventoryScreen(tk.Frame):
    """Inventory management interface"""
    
    def __init__(self, parent, api_client):
        super().__init__(parent, bg=COLOR_LIGHT)
        self.api_client = api_client
        self.setup_ui()
        self.load_inventory()
    
    def setup_ui(self):
        """Setup inventory UI"""
        # Header
        header = tk.Frame(self, bg=COLOR_PRIMARY, height=50)
        header.pack(fill=tk.X)
        
        header_label = tk.Label(header, text="Inventory Management", font=FONT_HEADING, bg=COLOR_PRIMARY, fg=COLOR_WHITE)
        header_label.pack(pady=10)
        
        # Controls
        controls = tk.Frame(self, bg=COLOR_LIGHT)
        controls.pack(fill=tk.X, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
        
        tk.Label(controls, text="Search:", bg=COLOR_LIGHT).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(controls, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=PADDING_SMALL)
        search_entry.bind("<KeyRelease>", lambda e: self.filter_inventory())
        
        adjust_btn = tk.Button(controls, text="Adjust Stock", bg=COLOR_WARNING, fg=COLOR_WHITE, command=self.adjust_stock, cursor="hand2")
        adjust_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        refresh_btn = tk.Button(controls, text="Refresh", bg=COLOR_PRIMARY, fg=COLOR_WHITE, command=self.load_inventory, cursor="hand2")
        refresh_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        # Inventory tree
        self.inventory_tree = ttk.Treeview(self, columns=("Product", "Current", "Min", "Max", "Status"), height=TABLE_HEIGHT)
        self.inventory_tree.heading("#0", text="ID")
        self.inventory_tree.heading("Product", text="Product")
        self.inventory_tree.heading("Current", text="Current")
        self.inventory_tree.heading("Min", text="Min Level")
        self.inventory_tree.heading("Max", text="Max Level")
        self.inventory_tree.heading("Status", text="Status")
        self.inventory_tree.column("#0", width=40)
        self.inventory_tree.column("Product", width=150)
        self.inventory_tree.column("Current", width=80)
        self.inventory_tree.column("Min", width=80)
        self.inventory_tree.column("Max", width=80)
        self.inventory_tree.column("Status", width=100)
        self.inventory_tree.pack(fill=tk.BOTH, expand=True, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
    
    def load_inventory(self):
        """Load inventory data"""
        try:
            response = self.api_client.get_products()
            self.display_inventory(response.get("products", []))
        except APIError as e:
            show_error("Error", f"Failed to load inventory: {str(e)}")
    
    def display_inventory(self, products):
        """Display inventory in tree"""
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        
        for product in products:
            stock = product.get("quantity", 0)
            min_level = product.get("min_stock", 10)
            max_level = product.get("max_stock", 100)
            
            # Determine status
            if stock <= min_level:
                status = "⚠️ LOW"
                tag = "low"
            elif stock >= max_level:
                status = "⚠️ OVERSTOCKED"
                tag = "overstock"
            else:
                status = "✓ OK"
                tag = "ok"
            
            self.inventory_tree.insert("", tk.END, text=product.get("id", ""), values=(
                product.get("name", ""),
                stock,
                min_level,
                max_level,
                status
            ), tags=(tag,))
        
        # Configure tags
        self.inventory_tree.tag_configure("low", foreground=COLOR_DANGER)
        self.inventory_tree.tag_configure("overstock", foreground=COLOR_WARNING)
        self.inventory_tree.tag_configure("ok", foreground=COLOR_SUCCESS)
    
    def filter_inventory(self):
        """Filter inventory by search term"""
        search_term = self.search_var.get().lower()
        try:
            response = self.api_client.get_products()
            products = response.get("products", [])
            filtered = [p for p in products if search_term in p.get("name", "").lower()]
            self.display_inventory(filtered)
        except APIError:
            pass
    
    def adjust_stock(self):
        """Adjust stock for selected product"""
        selection = self.inventory_tree.selection()
        if not selection:
            show_error("Error", "Select a product first")
            return
        
        item = self.inventory_tree.item(selection[0])
        product_id = item["text"]
        product_name = item["values"][0]
        current_stock = int(item["values"][1])
        
        # Show adjustment dialog
        result = show_input_dialog("Adjust Stock", f"Current stock: {current_stock}\nEnter new quantity:")
        if result is not None:
            try:
                new_quantity = int(result)
                # API call to update stock
                response = self.api_client.update_product_stock(product_id, new_quantity)
                show_success("Success", f"Stock updated: {product_name} → {new_quantity} units")
                self.load_inventory()
            except ValueError:
                show_error("Error", "Invalid quantity")
            except APIError as e:
                show_error("Error", f"Failed to update stock: {str(e)}")
