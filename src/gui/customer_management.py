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
        self.customers = []
        self.setup_ui()
        self.load_customers()

    @staticmethod
    def _extract_customers(response):
        data = response.get("data") or {}
        return response.get("customers") or data.get("customers") or data.get("items") or []
    
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
        search_entry.bind("<KeyRelease>", lambda e: self.load_customers(self.search_var.get().strip()))

        refresh_btn = tk.Button(controls, text="Refresh", bg=COLOR_PRIMARY, fg=COLOR_WHITE, command=self.load_customers, cursor="hand2")
        refresh_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        add_btn = tk.Button(controls, text="Add Customer", bg=COLOR_SUCCESS, fg=COLOR_WHITE, command=self.add_customer, cursor="hand2")
        add_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        edit_btn = tk.Button(controls, text="Edit", bg=COLOR_WARNING, fg=COLOR_WHITE, command=self.edit_customer, cursor="hand2")
        edit_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        delete_btn = tk.Button(controls, text="Delete", bg=COLOR_DANGER, fg=COLOR_WHITE, command=self.delete_customer, cursor="hand2")
        delete_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)

        history_btn = tk.Button(controls, text="History", bg=COLOR_SECONDARY, fg=COLOR_WHITE, command=self.view_history, cursor="hand2")
        history_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        # Customers tree
        self.customers_tree = ttk.Treeview(self, columns=("Name", "Phone", "Email", "Address", "Points"), height=TABLE_HEIGHT)
        self.customers_tree.heading("#0", text="ID", anchor=tk.W)
        self.customers_tree.heading("Name", text="Name", anchor=tk.W)
        self.customers_tree.heading("Phone", text="Phone", anchor=tk.W)
        self.customers_tree.heading("Email", text="Email", anchor=tk.W)
        self.customers_tree.heading("Address", text="Address", anchor=tk.W)
        self.customers_tree.heading("Points", text="Loyalty Points", anchor=tk.W)
        self.customers_tree.column("#0", anchor=tk.W)
        self.customers_tree.column("Name", anchor=tk.W)
        self.customers_tree.column("Phone", anchor=tk.W)
        self.customers_tree.column("Email", anchor=tk.W)
        self.customers_tree.column("Address", anchor=tk.W)
        self.customers_tree.column("Points", anchor=tk.W)
        self.customers_tree.pack(fill=tk.BOTH, expand=True, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)

    def load_customers(self, search_term: str = ""):
        """Load customers from API and refresh tree."""
        try:
            response = self.api_client.get_customers(search=search_term)
            self.customers = self._extract_customers(response)

            for item in self.customers_tree.get_children():
                self.customers_tree.delete(item)

            for customer in self.customers:
                self.customers_tree.insert(
                    "",
                    tk.END,
                    text=customer.get("id", ""),
                    values=(
                        customer.get("name", ""),
                        customer.get("phone_number", ""),
                        customer.get("email", ""),
                        customer.get("address", ""),
                        customer.get("loyalty_points", 0),
                    ),
                )
        except APIError as e:
            show_error("Error", f"Failed to load customers: {str(e)}")

    def _get_selected_customer(self):
        selection = self.customers_tree.selection()
        if not selection:
            show_error("Error", "Select a customer first")
            return None
        item = self.customers_tree.item(selection[0])
        customer_id = int(item["text"])
        return next((c for c in self.customers if c.get("id") == customer_id), None)

    def _customer_form(self, title: str, customer=None):
        """Open customer form and return created widgets."""
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.geometry("420x310")
        dialog.resizable(False, False)

        tk.Label(dialog, text="Name:").grid(row=0, column=0, padx=10, pady=8, sticky="w")
        name_entry = tk.Entry(dialog, width=34)
        name_entry.grid(row=0, column=1, padx=10, pady=8)

        tk.Label(dialog, text="Phone:").grid(row=1, column=0, padx=10, pady=8, sticky="w")
        phone_entry = tk.Entry(dialog, width=34)
        phone_entry.grid(row=1, column=1, padx=10, pady=8)

        tk.Label(dialog, text="Email:").grid(row=2, column=0, padx=10, pady=8, sticky="w")
        email_entry = tk.Entry(dialog, width=34)
        email_entry.grid(row=2, column=1, padx=10, pady=8)

        tk.Label(dialog, text="Address:").grid(row=3, column=0, padx=10, pady=8, sticky="w")
        address_entry = tk.Entry(dialog, width=34)
        address_entry.grid(row=3, column=1, padx=10, pady=8)

        if customer:
            name_entry.insert(0, customer.get("name", ""))
            phone_entry.insert(0, customer.get("phone_number", ""))
            email_entry.insert(0, customer.get("email", ""))
            address_entry.insert(0, customer.get("address", ""))

        return dialog, name_entry, phone_entry, email_entry, address_entry
    
    def add_customer(self):
        """Add new customer"""
        dialog, name_entry, phone_entry, email_entry, address_entry = self._customer_form("Add Customer")

        def save():
            name = name_entry.get().strip()
            if not name:
                show_error("Error", "Customer name is required")
                return
            try:
                self.api_client.create_customer(
                    name=name,
                    phone_number=phone_entry.get().strip(),
                    email=email_entry.get().strip(),
                    address=address_entry.get().strip(),
                )
                show_success("Success", "Customer added successfully")
                dialog.destroy()
                self.load_customers(self.search_var.get().strip())
            except APIError as e:
                show_error("Error", f"Failed to add customer: {str(e)}")

        tk.Button(dialog, text="Save", bg=COLOR_SUCCESS, fg=COLOR_WHITE, command=save, width=18).grid(row=4, column=0, columnspan=2, pady=20)
    
    def edit_customer(self):
        """Edit customer"""
        customer = self._get_selected_customer()
        if not customer:
            return

        dialog, name_entry, phone_entry, email_entry, address_entry = self._customer_form("Edit Customer", customer)

        def save():
            name = name_entry.get().strip()
            if not name:
                show_error("Error", "Customer name is required")
                return
            try:
                self.api_client.update_customer(
                    customer_id=customer["id"],
                    name=name,
                    phone_number=phone_entry.get().strip(),
                    email=email_entry.get().strip(),
                    address=address_entry.get().strip(),
                )
                show_success("Success", "Customer updated successfully")
                dialog.destroy()
                self.load_customers(self.search_var.get().strip())
            except APIError as e:
                show_error("Error", f"Failed to update customer: {str(e)}")

        tk.Button(dialog, text="Save Changes", bg=COLOR_SUCCESS, fg=COLOR_WHITE, command=save, width=18).grid(row=4, column=0, columnspan=2, pady=20)
    
    def delete_customer(self):
        """Delete customer"""
        customer = self._get_selected_customer()
        if not customer:
            return
        
        if show_confirmation("Confirm", f"Delete customer '{customer.get('name', '')}'?"):
            try:
                self.api_client.delete_customer(customer["id"])
                show_success("Delete", "Customer deleted successfully!")
                self.load_customers(self.search_var.get().strip())
            except APIError as e:
                show_error("Error", f"Failed to delete customer: {str(e)}")

    def view_history(self):
        """Display selected customer's purchase history."""
        customer = self._get_selected_customer()
        if not customer:
            return
        try:
            response = self.api_client.get_customer_history(customer["id"])
            data = response.get("data") or {}
            summary = data.get("summary") or {}
            purchases = data.get("purchase_history") or []

            dialog = tk.Toplevel(self)
            dialog.title(f"Purchase History - {customer.get('name', '')}")
            dialog.geometry("650x420")

            summary_text = (
                f"Orders: {summary.get('total_orders', 0)}    "
                f"Total Spent: {summary.get('total_spent', 0):.2f}    "
                f"Loyalty Points: {summary.get('loyalty_points', 0)}"
            )
            tk.Label(dialog, text=summary_text, font=FONT_NORMAL, bg=COLOR_LIGHT).pack(fill=tk.X, padx=10, pady=8)

            tree = ttk.Treeview(dialog, columns=("Date", "Total", "Items", "Payment"), height=14)
            tree.heading("#0", text="Sale ID", anchor=tk.W)
            tree.heading("Date", text="Date", anchor=tk.W)
            tree.heading("Total", text="Total", anchor=tk.W)
            tree.heading("Items", text="Items", anchor=tk.W)
            tree.heading("Payment", text="Payment", anchor=tk.W)
            tree.column("#0", anchor=tk.W)
            tree.column("Date", anchor=tk.W)
            tree.column("Total", anchor=tk.W)
            tree.column("Items", anchor=tk.W)
            tree.column("Payment", anchor=tk.W)
            tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            for sale in purchases:
                tree.insert(
                    "",
                    tk.END,
                    text=sale.get("id", ""),
                    values=(
                        sale.get("created_at", ""),
                        sale.get("total_amount", 0),
                        sale.get("items_count", 0),
                        sale.get("payment_method", ""),
                    ),
                )
        except APIError as e:
            show_error("Error", f"Failed to load customer history: {str(e)}")
