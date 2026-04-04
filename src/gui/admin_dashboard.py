"""
Admin Dashboard Screen
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from .config import *
from .utils.formatters import format_currency, format_date
from .utils.dialogs import show_error, show_success, show_confirmation, show_input_dialog
from .utils.api_client import APIError

class AdminDashboard(tk.Frame):
    """Admin dashboard with tabs for products, users, and reports"""
    
    def __init__(self, parent, api_client):
        super().__init__(parent, bg=COLOR_LIGHT)
        self.api_client = api_client
        self.categories = []
        self.setup_ui()

    @staticmethod
    def _extract_products(response):
        data = response.get("data") or {}
        return response.get("products") or data.get("products") or data.get("items") or []

    @staticmethod
    def _extract_users(response):
        data = response.get("data") or {}
        return response.get("users") or data.get("users") or data.get("items") or []

    @staticmethod
    def _extract_categories(response):
        data = response.get("data") or {}
        return response.get("categories") or data.get("categories") or data.get("items") or []

    def load_categories(self):
        """Load categories for comboboxes and category management."""
        response = self.api_client.get_categories()
        self.categories = self._extract_categories(response)
        if not self.categories:
            self.categories = [{"id": 0, "name": "General"}]

    def get_category_names(self):
        """Return sorted category names for combobox values."""
        names = sorted({(c.get("name") or "").strip() for c in self.categories if (c.get("name") or "").strip()})
        return names or ["General"]

    def manage_categories(self):
        """Open category management dialog for admin/manager roles."""
        try:
            self.load_categories()
        except APIError as e:
            show_error("Error", f"Failed to load categories: {str(e)}")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Manage Categories")
        dialog.geometry("420x380")
        dialog.resizable(False, False)

        tk.Label(dialog, text="Product Categories", font=FONT_HEADING).pack(pady=(10, 5))

        category_list = tk.Listbox(dialog, height=14)
        category_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        def refresh_listbox():
            category_list.delete(0, tk.END)
            for category in self.categories:
                category_list.insert(tk.END, category.get("name", ""))

        def get_selected_category():
            selection = category_list.curselection()
            if not selection:
                show_error("Error", "Select a category first")
                return None
            idx = selection[0]
            if idx >= len(self.categories):
                return None
            return self.categories[idx]

        def add_category():
            name = show_input_dialog("Add Category", "Category name:")
            if name is None:
                return
            name = name.strip()
            if not name:
                show_error("Error", "Category name is required")
                return
            try:
                self.api_client.create_category(name)
                self.load_categories()
                refresh_listbox()
                self.load_products()
                show_success("Success", "Category added successfully")
            except APIError as e:
                show_error("Error", f"Failed to add category: {str(e)}")

        def rename_category():
            category = get_selected_category()
            if not category:
                return
            new_name = show_input_dialog("Rename Category", "New category name:")
            if new_name is None:
                return
            new_name = new_name.strip()
            if not new_name:
                show_error("Error", "Category name is required")
                return
            try:
                self.api_client.update_category(category.get("id"), new_name)
                self.load_categories()
                refresh_listbox()
                self.load_products()
                show_success("Success", "Category renamed successfully")
            except APIError as e:
                show_error("Error", f"Failed to rename category: {str(e)}")

        def remove_category():
            category = get_selected_category()
            if not category:
                return
            category_name = category.get("name", "")
            if not show_confirmation("Confirm Delete", f"Delete category '{category_name}'?"):
                return
            try:
                self.api_client.delete_category(category.get("id"))
                self.load_categories()
                refresh_listbox()
                self.load_products()
                show_success("Success", "Category deleted successfully")
            except APIError as e:
                show_error("Error", f"Failed to delete category: {str(e)}")

        actions = tk.Frame(dialog, bg=COLOR_LIGHT)
        actions.pack(fill=tk.X, padx=10, pady=(0, 10))
        tk.Button(actions, text="Add", bg=COLOR_SUCCESS, fg=COLOR_WHITE, command=add_category, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(actions, text="Rename", bg=COLOR_WARNING, fg=COLOR_WHITE, command=rename_category, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(actions, text="Delete", bg=COLOR_DANGER, fg=COLOR_WHITE, command=remove_category, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(actions, text="Close", command=dialog.destroy, width=10).pack(side=tk.RIGHT, padx=5)

        refresh_listbox()
    
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
        self.product_search.bind("<KeyRelease>", lambda e: self.filter_products())
        
        add_btn = tk.Button(controls, text="Add Product", bg=COLOR_SUCCESS, fg=COLOR_WHITE, command=self.add_product, cursor="hand2")
        add_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        edit_btn = tk.Button(controls, text="Edit", bg=COLOR_WARNING, fg=COLOR_WHITE, command=self.edit_product, cursor="hand2")
        edit_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        delete_btn = tk.Button(controls, text="Delete", bg=COLOR_DANGER, fg=COLOR_WHITE, command=self.delete_product, cursor="hand2")
        delete_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        refresh_btn = tk.Button(controls, text="Refresh", bg=COLOR_PRIMARY, fg=COLOR_WHITE, command=self.load_products, cursor="hand2")
        refresh_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)

        categories_btn = tk.Button(controls, text="Categories", bg=COLOR_SECONDARY, fg=COLOR_WHITE, command=self.manage_categories, cursor="hand2")
        categories_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        # Products tree
        self.products_tree = ttk.Treeview(parent, columns=("Name", "Price", "Stock", "Category"), height=TABLE_HEIGHT)
        self.products_tree.heading("#0", text="ID")
        self.products_tree.heading("Name", text="Name")
        self.products_tree.heading("Price", text="Price")
        self.products_tree.heading("Stock", text="Stock")
        self.products_tree.heading("Category", text="Category")
        self.products_tree.column("#0", width=40)
        self.products_tree.column("Name", width=150)
        self.products_tree.column("Price", width=80)
        self.products_tree.column("Stock", width=80)
        self.products_tree.column("Category", width=100)
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
        self.users_tree.column("#0", width=40)
        self.users_tree.column("Username", width=120)
        self.users_tree.column("Email", width=150)
        self.users_tree.column("Role", width=80)
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
        
        export_btn = tk.Button(controls, text="Export", bg=COLOR_SUCCESS, fg=COLOR_WHITE, command=self.export_report, cursor="hand2")
        export_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        # Reports text area
        self.reports_text = tk.Text(parent, height=20, width=80, font=FONT_MONO)
        self.reports_text.pack(fill=tk.BOTH, expand=True, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
    
    def load_products(self):
        """Load and display products"""
        try:
            response = self.api_client.get_products()
            for item in self.products_tree.get_children():
                self.products_tree.delete(item)

            products = self._extract_products(response)
            for product in products:
                self.products_tree.insert("", tk.END, text=product.get("id", ""), values=(
                    product.get("name", ""),
                    format_currency(product.get("price", 0)),
                    product.get("quantity_in_stock", 0),
                    product.get("category", "N/A")
                ))
        except APIError as e:
            show_error("Error", f"Failed to load products: {str(e)}")
    
    def load_users(self):
        """Load and display users"""
        try:
            response = self.api_client.get_users()
            for item in self.users_tree.get_children():
                self.users_tree.delete(item)

            users = self._extract_users(response)
            for user in users:
                self.users_tree.insert("", tk.END, text=user.get("id", ""), values=(
                    user.get("username", ""),
                    user.get("email", ""),
                    user.get("role", "")
                ))
        except APIError as e:
            show_error("Error", f"Failed to load users: {str(e)}")
    
    def filter_products(self):
        """Filter products by search term"""
        search_term = self.product_search.get().lower()
        try:
            response = self.api_client.get_products()
            products = self._extract_products(response)
            filtered = [p for p in products if search_term in p.get("name", "").lower()]
            
            for item in self.products_tree.get_children():
                self.products_tree.delete(item)
            
            for product in filtered:
                self.products_tree.insert("", tk.END, text=product.get("id", ""), values=(
                    product.get("name", ""),
                    format_currency(product.get("price", 0)),
                    product.get("quantity_in_stock", 0),
                    product.get("category", "N/A")
                ))
        except APIError:
            pass
    
    def add_product(self):
        """Add new product dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Add Product")
        dialog.geometry("400x500")
        dialog.resizable(False, False)
        
        # Name
        tk.Label(dialog, text="Product Name:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        name_entry = tk.Entry(dialog, width=30)
        name_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # SKU (REQUIRED)
        tk.Label(dialog, text="SKU/Barcode:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        sku_entry = tk.Entry(dialog, width=30)
        sku_entry.grid(row=1, column=1, padx=10, pady=5)
        
        # Category
        tk.Label(dialog, text="Category:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        try:
            self.load_categories()
        except APIError as e:
            show_error("Error", f"Failed to load categories: {str(e)}")
            dialog.destroy()
            return
        category_var = tk.StringVar(value=(self.get_category_names()[0] if self.get_category_names() else "General"))
        category_combo = ttk.Combobox(dialog, width=27, textvariable=category_var, state="readonly", values=self.get_category_names())
        category_combo.grid(row=2, column=1, padx=10, pady=5)
        
        # Price
        tk.Label(dialog, text="Price:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        price_entry = tk.Entry(dialog, width=30)
        price_entry.grid(row=3, column=1, padx=10, pady=5)
        
        # Stock
        tk.Label(dialog, text="Initial Stock:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        stock_entry = tk.Entry(dialog, width=30)
        stock_entry.grid(row=4, column=1, padx=10, pady=5)
        
        def save():
            try:
                # Get values
                name = name_entry.get()
                sku = sku_entry.get()
                category = category_var.get() or "General"
                price_str = price_entry.get()
                stock_str = stock_entry.get()
                
                # Validate
                if not name:
                    show_error("Error", "Product name required")
                    return
                if not sku:
                    show_error("Error", "SKU required")
                    return
                
                # Convert to numbers
                price = float(price_str)
                quantity = int(stock_str)
                
                # Call API with correct parameter names
                response = self.api_client.create_product(
                    name=name,
                    sku=sku,
                    price=price,
                    category=category,
                    quantity_in_stock=quantity
                )
                
                show_success("Success", "Product added successfully!")
                self.load_products()
                dialog.destroy()
                
            except ValueError:
                show_error("Error", "Invalid price or stock quantity")
            except APIError as e:
                show_error("Error", f"Failed to add product: {str(e)}")
            except Exception as e:
                show_error("Error", f"Unexpected error: {str(e)}")
        
        tk.Button(dialog, text="Save", bg=COLOR_SUCCESS, fg=COLOR_WHITE, command=save, width=20).grid(row=5, column=0, columnspan=2, pady=20)
    
    def edit_product(self):
        """Edit product dialog"""
        selection = self.products_tree.selection()
        if not selection:
            show_error("Error", "Select a product first")
            return
        
        item = self.products_tree.item(selection[0])
        product_id = item["text"]
        product_name = item["values"][0]
        product_price = item["values"][1].replace("Ksh ", "").replace(",", "").strip()
        product_stock = item["values"][2]
        product_category = item["values"][3]
        
        dialog = tk.Toplevel(self)
        dialog.title(f"Edit Product: {product_name}")
        dialog.geometry("400x400")
        dialog.resizable(False, False)
        
        tk.Label(dialog, text="Product Name:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        name_entry = tk.Entry(dialog, width=30)
        name_entry.insert(0, product_name)
        name_entry.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(dialog, text="Category:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        try:
            self.load_categories()
        except APIError as e:
            show_error("Error", f"Failed to load categories: {str(e)}")
            dialog.destroy()
            return
        category_names = self.get_category_names()
        if product_category and product_category not in category_names:
            category_names = sorted(category_names + [product_category])
        category_var = tk.StringVar(value=(product_category or category_names[0]))
        category_combo = ttk.Combobox(dialog, width=27, textvariable=category_var, state="readonly", values=category_names)
        category_combo.grid(row=1, column=1, padx=10, pady=5)
        
        tk.Label(dialog, text="Price:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        price_entry = tk.Entry(dialog, width=30)
        price_entry.insert(0, product_price)
        price_entry.grid(row=2, column=1, padx=10, pady=5)
        
        tk.Label(dialog, text="Stock:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        stock_entry = tk.Entry(dialog, width=30)
        stock_entry.insert(0, str(product_stock))
        stock_entry.grid(row=3, column=1, padx=10, pady=5)
        
        def save():
            try:
                name = name_entry.get()
                category = category_var.get()
                price = float(price_entry.get())
                quantity = int(stock_entry.get())
                
                response = self.api_client.update_product(
                    product_id=product_id,
                    name=name,
                    category=category,
                    price=price,
                    quantity_in_stock=quantity
                )
                
                show_success("Success", "Product updated successfully!")
                self.load_products()
                dialog.destroy()
            except ValueError:
                show_error("Error", "Invalid price or stock quantity")
            except APIError as e:
                show_error("Error", f"Failed to update product: {str(e)}")
            except Exception as e:
                show_error("Error", f"Unexpected error: {str(e)}")
        
        tk.Button(dialog, text="Save Changes", bg=COLOR_SUCCESS, fg=COLOR_WHITE, command=save, width=20).grid(row=4, column=0, columnspan=2, pady=20)
    
    def delete_product(self):
        """Delete product"""
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
    
    def add_user(self):
        """Add new user"""
        dialog = tk.Toplevel(self)
        dialog.title("Add User")
        dialog.geometry("400x350")
        dialog.resizable(False, False)
        
        tk.Label(dialog, text="Username:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        username_entry = tk.Entry(dialog, width=30)
        username_entry.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(dialog, text="Email:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        email_entry = tk.Entry(dialog, width=30)
        email_entry.grid(row=1, column=1, padx=10, pady=5)
        
        tk.Label(dialog, text="Password:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        password_entry = tk.Entry(dialog, width=30, show="*")
        password_entry.grid(row=2, column=1, padx=10, pady=5)
        
        tk.Label(dialog, text="Role:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        role_var = tk.StringVar(value="Cashier")
        role_combo = ttk.Combobox(dialog, textvariable=role_var, values=["Cashier", "Manager", "Admin"], width=28, state="readonly")
        role_combo.grid(row=3, column=1, padx=10, pady=5)
        
        def save():
            try:
                username = username_entry.get()
                email = email_entry.get()
                password = password_entry.get()
                role = role_var.get()
                
                if not all([username, email, password]):
                    show_error("Error", "All fields required")
                    return
                
                response = self.api_client.create_user(
                    username=username,
                    email=email,
                    password=password,
                    role=role
                )
                
                show_success("Success", "User added successfully!")
                self.load_users()
                dialog.destroy()
            except APIError as e:
                show_error("Error", f"Failed to add user: {str(e)}")
            except Exception as e:
                show_error("Error", f"Unexpected error: {str(e)}")
        
        tk.Button(dialog, text="Save", bg=COLOR_SUCCESS, fg=COLOR_WHITE, command=save, width=20).grid(row=4, column=0, columnspan=2, pady=20)
    
    def edit_user(self):
        """Edit user"""
        selection = self.users_tree.selection()
        if not selection:
            show_error("Error", "Select a user first")
            return
        
        item = self.users_tree.item(selection[0])
        user_id = item["text"]
        username = item["values"][0]
        email = item["values"][1]
        role = item["values"][2]
        
        dialog = tk.Toplevel(self)
        dialog.title(f"Edit User: {username}")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        
        tk.Label(dialog, text="Email:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        email_entry = tk.Entry(dialog, width=30)
        email_entry.insert(0, email)
        email_entry.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(dialog, text="Role:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        role_var = tk.StringVar(value=role)
        role_combo = ttk.Combobox(dialog, textvariable=role_var, values=["cashier", "manager", "admin"], width=28, state="readonly")
        role_combo.grid(row=1, column=1, padx=10, pady=5)
        
        def save():
            try:
                new_email = email_entry.get()
                new_role = role_var.get()
                
                response = self.api_client.update_user(
                    user_id=user_id,
                    email=new_email,
                    role=new_role
                )
                
                show_success("Success", "User updated successfully!")
                self.load_users()
                dialog.destroy()
            except APIError as e:
                show_error("Error", f"Failed to update user: {str(e)}")
            except Exception as e:
                show_error("Error", f"Unexpected error: {str(e)}")
        
        tk.Button(dialog, text="Save Changes", bg=COLOR_SUCCESS, fg=COLOR_WHITE, command=save, width=20).grid(row=2, column=0, columnspan=2, pady=20)
    
    def delete_user(self):
        """Delete user"""
        selection = self.users_tree.selection()
        if not selection:
            show_error("Error", "Select a user first")
            return
        
        item = self.users_tree.item(selection[0])
        user_id = item["text"]
        username = item["values"][0]
        
        if show_confirmation("Confirm Delete", f"Delete user '{username}'?"):
            try:
                response = self.api_client.delete_user(user_id)
                show_success("Success", "User deleted successfully!")
                self.load_users()
            except APIError as e:
                show_error("Error", f"Failed to delete user: {str(e)}")
    
    def show_daily_report(self):
        """Show daily report"""
        try:
            response = self.api_client.get_daily_report()
            self.reports_text.config(state=tk.NORMAL)
            self.reports_text.delete(1.0, tk.END)
            
            report_data = response.get("report", {})
            report_text = f"""
DAILY SALES REPORT
{'='*60}
Date: {report_data.get('date', 'Today')}

Total Sales: ${report_data.get('total_sales', 0):.2f}
Total Transactions: {report_data.get('transaction_count', 0)}
Total Items Sold: {report_data.get('items_sold', 0)}
Total Tax: ${report_data.get('total_tax', 0):.2f}

{'='*60}
"""
            self.reports_text.insert(tk.END, report_text)
            self.reports_text.config(state=tk.DISABLED)
        except APIError as e:
            show_error("Error", f"Failed to load report: {str(e)}")
    
    def show_monthly_report(self):
        """Show monthly report"""
        try:
            response = self.api_client.get_monthly_report()
            self.reports_text.config(state=tk.NORMAL)
            self.reports_text.delete(1.0, tk.END)
            
            report_data = response.get("report", {})
            report_text = f"""
MONTHLY SALES REPORT
{'='*60}
Month: {report_data.get('month', 'Current Month')}

Total Sales: ${report_data.get('total_sales', 0):.2f}
Total Transactions: {report_data.get('transaction_count', 0)}
Total Items Sold: {report_data.get('items_sold', 0)}
Total Tax: ${report_data.get('total_tax', 0):.2f}
Average Transaction: ${report_data.get('avg_transaction', 0):.2f}

{'='*60}
"""
            self.reports_text.insert(tk.END, report_text)
            self.reports_text.config(state=tk.DISABLED)
        except APIError as e:
            show_error("Error", f"Failed to load report: {str(e)}")
    
    def export_report(self):
        """Export report to file"""
        try:
            report_content = self.reports_text.get(1.0, tk.END)
            if not report_content.strip():
                show_error("Error", "No report to export")
                return
            
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w') as f:
                f.write(report_content)
            
            show_success("Exported", f"Report saved to {filename}")
        except Exception as e:
            show_error("Error", f"Failed to export: {str(e)}")
