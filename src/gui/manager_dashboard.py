"""
Manager Dashboard Screen
"""
import tkinter as tk
from tkinter import ttk
from .config import *
from .utils.formatters import format_currency, format_datetime
from .utils.dialogs import show_error, show_success, show_confirmation, show_input_dialog
from .utils.api_client import APIError

class ManagerDashboard(tk.Frame):
    """Manager dashboard with sales and analytics"""
    
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
    def _extract_categories(response):
        data = response.get("data") or {}
        return response.get("categories") or data.get("categories") or data.get("items") or []

    def load_categories(self):
        response = self.api_client.get_categories()
        self.categories = self._extract_categories(response)
        if not self.categories:
            self.categories = [{"id": 0, "name": "General"}]

    def get_category_names(self):
        names = sorted({(c.get("name") or "").strip() for c in self.categories if (c.get("name") or "").strip()})
        return names or ["General"]
    
    def setup_ui(self):
        """Setup manager dashboard UI"""
        # Header
        header = tk.Frame(self, bg=COLOR_PRIMARY, height=50)
        header.pack(fill=tk.X)

        header_label = tk.Label(header, text="Manager Dashboard", font=FONT_HEADING, bg=COLOR_PRIMARY, fg=COLOR_WHITE)
        header_label.pack(pady=10)

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)

        sales_frame = tk.Frame(notebook, bg=COLOR_LIGHT)
        notebook.add(sales_frame, text="Sales")
        self.setup_sales_tab(sales_frame)

        products_frame = tk.Frame(notebook, bg=COLOR_LIGHT)
        notebook.add(products_frame, text="Products")
        self.setup_products_tab(products_frame)

    def setup_sales_tab(self, content):
        """Setup sales tab UI."""
        stats_frame = tk.Frame(content, bg=COLOR_LIGHT)
        stats_frame.pack(fill=tk.X, pady=PADDING_MEDIUM)

        tk.Label(stats_frame, text="Today's Sales:", font=FONT_HEADING, bg=COLOR_LIGHT).pack(side=tk.LEFT, padx=PADDING_MEDIUM)
        self.today_sales_label = tk.Label(stats_frame, text=format_currency(0), font=FONT_TITLE, bg=COLOR_LIGHT, fg=COLOR_SUCCESS)
        self.today_sales_label.pack(side=tk.LEFT, padx=PADDING_SMALL)

        tk.Label(stats_frame, text="Transactions:", font=FONT_HEADING, bg=COLOR_LIGHT).pack(side=tk.LEFT, padx=PADDING_MEDIUM)
        self.transaction_label = tk.Label(stats_frame, text="0", font=FONT_TITLE, bg=COLOR_LIGHT, fg=COLOR_PRIMARY)
        self.transaction_label.pack(side=tk.LEFT, padx=PADDING_SMALL)

        sales_label_frame = tk.LabelFrame(content, text="Recent Sales", font=FONT_HEADING, bg=COLOR_LIGHT)
        sales_label_frame.pack(fill=tk.BOTH, expand=True, pady=PADDING_MEDIUM)

        self.sales_tree = ttk.Treeview(sales_label_frame, columns=("Date", "Amount", "Items", "Payment"), height=TABLE_HEIGHT)
        self.sales_tree.heading("#0", text="ID")
        self.sales_tree.heading("Date", text="Date")
        self.sales_tree.heading("Amount", text="Amount")
        self.sales_tree.heading("Items", text="Items")
        self.sales_tree.heading("Payment", text="Payment")
        self.sales_tree.pack(fill=tk.BOTH, expand=True, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)

        controls = tk.Frame(content, bg=COLOR_LIGHT)
        controls.pack(fill=tk.X, pady=PADDING_MEDIUM)

        refresh_btn = tk.Button(controls, text="Refresh", bg=COLOR_PRIMARY, fg=COLOR_WHITE, command=self.load_sales, cursor="hand2")
        refresh_btn.pack(side=tk.LEFT, padx=PADDING_SMALL)

        self.load_sales()

    def setup_products_tab(self, parent):
        """Setup products tab for managers."""
        controls = tk.Frame(parent, bg=COLOR_LIGHT)
        controls.pack(fill=tk.X, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)

        tk.Label(controls, text="Search:", bg=COLOR_LIGHT).pack(side=tk.LEFT)
        self.product_search = tk.Entry(controls, width=30)
        self.product_search.pack(side=tk.LEFT, padx=PADDING_SMALL)
        self.product_search.bind("<KeyRelease>", lambda e: self.filter_products())

        tk.Button(controls, text="Add Product", bg=COLOR_SUCCESS, fg=COLOR_WHITE, command=self.add_product, cursor="hand2").pack(side=tk.LEFT, padx=PADDING_SMALL)
        tk.Button(controls, text="Edit", bg=COLOR_WARNING, fg=COLOR_WHITE, command=self.edit_product, cursor="hand2").pack(side=tk.LEFT, padx=PADDING_SMALL)
        tk.Button(controls, text="Delete", bg=COLOR_DANGER, fg=COLOR_WHITE, command=self.delete_product, cursor="hand2").pack(side=tk.LEFT, padx=PADDING_SMALL)
        tk.Button(controls, text="Refresh", bg=COLOR_PRIMARY, fg=COLOR_WHITE, command=self.load_products, cursor="hand2").pack(side=tk.LEFT, padx=PADDING_SMALL)
        tk.Button(controls, text="Categories", bg=COLOR_SECONDARY, fg=COLOR_WHITE, command=self.manage_categories, cursor="hand2").pack(side=tk.LEFT, padx=PADDING_SMALL)

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

    def load_products(self):
        """Load and display products."""
        try:
            response = self.api_client.get_products()
            for item in self.products_tree.get_children():
                self.products_tree.delete(item)

            for product in self._extract_products(response):
                self.products_tree.insert("", tk.END, text=product.get("id", ""), values=(
                    product.get("name", ""),
                    format_currency(product.get("price", 0)),
                    product.get("quantity_in_stock", 0),
                    product.get("category", "N/A"),
                ))
        except APIError as e:
            show_error("Error", f"Failed to load products: {str(e)}")

    def filter_products(self):
        """Filter products by search term."""
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
                    product.get("category", "N/A"),
                ))
        except APIError:
            pass

    def manage_categories(self):
        """Open category management dialog for manager role."""
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

    def add_product(self):
        """Add new product dialog."""
        dialog = tk.Toplevel(self)
        dialog.title("Add Product")
        dialog.geometry("400x500")
        dialog.resizable(False, False)

        tk.Label(dialog, text="Product Name:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        name_entry = tk.Entry(dialog, width=30)
        name_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(dialog, text="SKU/Barcode:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        sku_entry = tk.Entry(dialog, width=30)
        sku_entry.grid(row=1, column=1, padx=10, pady=5)

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

        tk.Label(dialog, text="Price:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        price_entry = tk.Entry(dialog, width=30)
        price_entry.grid(row=3, column=1, padx=10, pady=5)

        tk.Label(dialog, text="Initial Stock:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        stock_entry = tk.Entry(dialog, width=30)
        stock_entry.grid(row=4, column=1, padx=10, pady=5)

        def save():
            try:
                name = name_entry.get()
                sku = sku_entry.get()
                category = category_var.get() or "General"
                price = float(price_entry.get())
                quantity = int(stock_entry.get())

                if not name:
                    show_error("Error", "Product name required")
                    return
                if not sku:
                    show_error("Error", "SKU required")
                    return

                self.api_client.create_product(
                    name=name,
                    sku=sku,
                    price=price,
                    category=category,
                    quantity_in_stock=quantity,
                )
                show_success("Success", "Product added successfully!")
                self.load_products()
                dialog.destroy()
            except ValueError:
                show_error("Error", "Invalid price or stock quantity")
            except APIError as e:
                show_error("Error", f"Failed to add product: {str(e)}")

        tk.Button(dialog, text="Save", bg=COLOR_SUCCESS, fg=COLOR_WHITE, command=save, width=20).grid(row=5, column=0, columnspan=2, pady=20)

    def edit_product(self):
        """Edit product dialog."""
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
                self.api_client.update_product(
                    product_id=product_id,
                    name=name_entry.get(),
                    category=category_var.get(),
                    price=float(price_entry.get()),
                    quantity_in_stock=int(stock_entry.get()),
                )
                show_success("Success", "Product updated successfully!")
                self.load_products()
                dialog.destroy()
            except ValueError:
                show_error("Error", "Invalid price or stock quantity")
            except APIError as e:
                show_error("Error", f"Failed to update product: {str(e)}")

        tk.Button(dialog, text="Save Changes", bg=COLOR_SUCCESS, fg=COLOR_WHITE, command=save, width=20).grid(row=4, column=0, columnspan=2, pady=20)

    def delete_product(self):
        """Delete product."""
        selection = self.products_tree.selection()
        if not selection:
            show_error("Error", "Select a product first")
            return

        item = self.products_tree.item(selection[0])
        product_id = item["text"]
        product_name = item["values"][0]

        if show_confirmation("Confirm Delete", f"Delete product '{product_name}'?"):
            try:
                self.api_client.delete_product(product_id)
                show_success("Success", "Product deleted successfully!")
                self.load_products()
            except APIError as e:
                show_error("Error", f"Failed to delete product: {str(e)}")
    
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
