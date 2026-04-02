"""
Manager Dashboard Screen
"""
import tkinter as tk
from tkinter import ttk
from .config import *
from .utils.formatters import format_currency, format_datetime
from .utils.dialogs import show_error, show_success
from .utils.api_client import APIError

class ManagerDashboard(tk.Frame):
    """Manager dashboard with sales and analytics"""
    
    def __init__(self, parent, api_client):
        super().__init__(parent, bg=COLOR_LIGHT)
        self.api_client = api_client
        self.setup_ui()
    
    def setup_ui(self):
        """Setup manager dashboard UI"""
        # Header
        header = tk.Frame(self, bg=COLOR_PRIMARY, height=50)
        header.pack(fill=tk.X)
        
        header_label = tk.Label(header, text="Manager Dashboard", font=FONT_HEADING, bg=COLOR_PRIMARY, fg=COLOR_WHITE)
        header_label.pack(pady=10)
        
        # Content area
        content = tk.Frame(self, bg=COLOR_LIGHT)
        content.pack(fill=tk.BOTH, expand=True, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
        
        # Top stats
        stats_frame = tk.Frame(content, bg=COLOR_LIGHT)
        stats_frame.pack(fill=tk.X, pady=PADDING_MEDIUM)
        
        tk.Label(stats_frame, text="Today's Sales:", font=FONT_HEADING, bg=COLOR_LIGHT).pack(side=tk.LEFT, padx=PADDING_MEDIUM)
        self.today_sales_label = tk.Label(stats_frame, text=format_currency(0), font=FONT_TITLE, bg=COLOR_LIGHT, fg=COLOR_SUCCESS)
        self.today_sales_label.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        tk.Label(stats_frame, text="Transactions:", font=FONT_HEADING, bg=COLOR_LIGHT).pack(side=tk.LEFT, padx=PADDING_MEDIUM)
        self.transaction_label = tk.Label(stats_frame, text="0", font=FONT_TITLE, bg=COLOR_LIGHT, fg=COLOR_PRIMARY)
        self.transaction_label.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        # Sales list
        sales_label_frame = tk.LabelFrame(content, text="Recent Sales", font=FONT_HEADING, bg=COLOR_LIGHT)
        sales_label_frame.pack(fill=tk.BOTH, expand=True, pady=PADDING_MEDIUM)
        
        self.sales_tree = ttk.Treeview(sales_label_frame, columns=("Date", "Amount", "Items", "Payment"), height=TABLE_HEIGHT)
        self.sales_tree.heading("#0", text="ID")
        self.sales_tree.heading("Date", text="Date")
        self.sales_tree.heading("Amount", text="Amount")
        self.sales_tree.heading("Items", text="Items")
        self.sales_tree.heading("Payment", text="Payment")
        self.sales_tree.pack(fill=tk.BOTH, expand=True, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
        
        # Controls
        controls = tk.Frame(content, bg=COLOR_LIGHT)
        controls.pack(fill=tk.X, pady=PADDING_MEDIUM)
        
        refresh_btn = tk.Button(controls, text="Refresh", bg=COLOR_PRIMARY, fg=COLOR_WHITE, command=self.load_sales, cursor="hand2")
        refresh_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        self.load_sales()
    
    def load_sales(self):
        """Load recent sales"""
        try:
            response = self.api_client.get_sales()
            for item in self.sales_tree.get_children():
                self.sales_tree.delete(item)
            
            total_sales = 0
            for sale in response.get("sales", []):
                total_sales += sale.get("total", 0)
                self.sales_tree.insert("", tk.END, text=sale.get("id", ""), values=(
                    format_datetime(sale.get("date", "")),
                    format_currency(sale.get("total", 0)),
                    len(sale.get("items", [])),
                    sale.get("payment_method", "")
                ))
            
            self.today_sales_label.config(text=format_currency(total_sales))
            self.transaction_label.config(text=str(len(response.get("sales", []))))
        except APIError as e:
            show_error("Error", f"Failed to load sales: {str(e)}")
