"""
Customer Management Screen
"""
import tkinter as tk
from tkinter import ttk
from .config import *
from .utils.dialogs import show_error, show_success, show_confirmation
from .utils.api_client import APIError

class CustomerManagement(tk.Frame):
    """Customer management interface"""
    
    def __init__(self, parent, api_client):
        super().__init__(parent, bg=COLOR_LIGHT)
        self.api_client = api_client
        self.setup_ui()
    
    def setup_ui(self):
        """Setup customer management UI"""
        # Header
        header = tk.Frame(self, bg=COLOR_PRIMARY, height=50)
        header.pack(fill=tk.X)
        
        header_label = tk.Label(header, text="Customer Management", font=FONT_HEADING, bg=COLOR_PRIMARY, fg=COLOR_WHITE)
        header_label.pack(pady=10)
        
        # Controls
        controls = tk.Frame(self, bg=COLOR_LIGHT)
        controls.pack(fill=tk.X, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
        
        tk.Label(controls, text="Search:", bg=COLOR_LIGHT).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(controls, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        add_btn = tk.Button(controls, text="Add Customer", bg=COLOR_SUCCESS, fg=COLOR_WHITE, command=self.add_customer, cursor="hand2")
        add_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        edit_btn = tk.Button(controls, text="Edit", bg=COLOR_WARNING, fg=COLOR_WHITE, command=self.edit_customer, cursor="hand2")
        edit_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        delete_btn = tk.Button(controls, text="Delete", bg=COLOR_DANGER, fg=COLOR_WHITE, command=self.delete_customer, cursor="hand2")
        delete_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        # Customers tree
        self.customers_tree = ttk.Treeview(self, columns=("Name", "Phone", "Email", "Total_Sales"), height=TABLE_HEIGHT)
        self.customers_tree.heading("#0", text="ID")
        self.customers_tree.heading("Name", text="Name")
        self.customers_tree.heading("Phone", text="Phone")
        self.customers_tree.heading("Email", text="Email")
        self.customers_tree.heading("Total_Sales", text="Total Sales")
        self.customers_tree.pack(fill=tk.BOTH, expand=True, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
    
    def add_customer(self):
        """Add new customer"""
        show_success("Add Customer", "Feature coming soon!")
    
    def edit_customer(self):
        """Edit customer"""
        selection = self.customers_tree.selection()
        if not selection:
            show_error("Error", "Select a customer first")
            return
        show_success("Edit Customer", "Feature coming soon!")
    
    def delete_customer(self):
        """Delete customer"""
        selection = self.customers_tree.selection()
        if not selection:
            show_error("Error", "Select a customer first")
            return
        
        if show_confirmation("Confirm", "Delete this customer?"):
            show_success("Delete", "Customer deleted successfully!")
