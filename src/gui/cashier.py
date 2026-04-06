"""
Cashier Screen - Main POS Interface
"""
import re
import tkinter as tk
import webbrowser
from tkinter import ttk
from datetime import datetime
from .config import *
from . import config as gui_config
from .utils.formatters import format_currency, parse_currency
from .utils.dialogs import show_error, show_success, show_confirmation, show_int_input_dialog
from .utils.api_client import APIError

DEFAULT_PAYSTACK_EMAIL = "donniecarey79564@suffermail.com"
LOYALTY_POINTS_THRESHOLD = 1000
LOYALTY_DISCOUNT_RATE = 0.05

class CashierScreen(tk.Frame):
    """Main cashier POS interface"""
    
    def __init__(self, parent, api_client):
        super().__init__(parent, bg=COLOR_LIGHT)
        self.api_client = api_client
        self.cart_items = []
        self.products = []
        self.customers = []
        self.customer_id_map = {"Walk-in": None}
        self.customer_points_map = {"Walk-in": 0}
        self.setup_ui()
        self.load_customers()
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
        self.cart_tree.heading("#0", text="ID", anchor=tk.W)
        self.cart_tree.heading("Name", text="Name", anchor=tk.W)
        self.cart_tree.heading("Qty", text="Qty", anchor=tk.W)
        self.cart_tree.heading("Price", text="Unit Price", anchor=tk.W)
        self.cart_tree.heading("Total", text="Total", anchor=tk.W)
        self.cart_tree.column("#0", width=30, anchor=tk.W)
        self.cart_tree.column("Name", width=100, anchor=tk.W)
        self.cart_tree.column("Qty", width=50, anchor=tk.W)
        self.cart_tree.column("Price", width=70, anchor=tk.W)
        self.cart_tree.column("Total", width=70, anchor=tk.W)
        self.cart_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.cart_tree.bind("<Double-Button-1>", lambda e: self.edit_cart_quantity())
        
        # Cart controls
        cart_controls = tk.Frame(cart_frame, bg=COLOR_WHITE)
        cart_controls.pack(fill=tk.X, padx=5, pady=5)
        
        edit_qty_btn = tk.Button(cart_controls, text="Edit Qty", bg=COLOR_PRIMARY, fg=COLOR_WHITE, command=self.edit_cart_quantity, cursor="hand2")
        edit_qty_btn.pack(side=tk.LEFT, padx=2)

        remove_btn = tk.Button(cart_controls, text="Remove", bg=COLOR_DANGER, fg=COLOR_WHITE, command=self.remove_from_cart, cursor="hand2")
        remove_btn.pack(side=tk.LEFT, padx=2)
        
        clear_btn = tk.Button(cart_controls, text="Clear Cart", bg=COLOR_WARNING, fg=COLOR_WHITE, command=self.clear_cart, cursor="hand2")
        clear_btn.pack(side=tk.LEFT, padx=2)
        
        # Totals section
        totals_frame = tk.Frame(cart_frame, bg=COLOR_LIGHT)
        totals_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(totals_frame, text="Subtotal:", font=FONT_NORMAL, bg=COLOR_LIGHT).grid(row=0, column=0, sticky="w")
        self.subtotal_label = tk.Label(totals_frame, text=format_currency(0), font=FONT_NORMAL, bg=COLOR_LIGHT, fg=COLOR_SUCCESS)
        self.subtotal_label.grid(row=0, column=1, sticky="e")
        
        tk.Label(totals_frame, text="Manual Discount:", font=FONT_NORMAL, bg=COLOR_LIGHT).grid(row=1, column=0, sticky="w")
        self.discount_entry = tk.Entry(totals_frame, width=15, font=FONT_NORMAL)
        self.discount_entry.insert(0, "0")
        self.discount_entry.grid(row=1, column=1, sticky="e", padx=5)
        self.discount_entry.bind("<KeyRelease>", lambda e: self.update_totals())
        
        tk.Label(totals_frame, text="Loyalty Reward:", font=FONT_NORMAL, bg=COLOR_LIGHT).grid(row=2, column=0, sticky="w")
        self.loyalty_discount_label = tk.Label(totals_frame, text=format_currency(0), font=FONT_NORMAL, bg=COLOR_LIGHT, fg=COLOR_SECONDARY)
        self.loyalty_discount_label.grid(row=2, column=1, sticky="e")

        self.tax_title_label = tk.Label(totals_frame, text=f"Tax ({gui_config.TAX_RATE*100:.0f}%):", font=FONT_NORMAL, bg=COLOR_LIGHT)
        self.tax_title_label.grid(row=3, column=0, sticky="w")
        self.tax_label = tk.Label(totals_frame, text=format_currency(0), font=FONT_NORMAL, bg=COLOR_LIGHT, fg=COLOR_WARNING)
        self.tax_label.grid(row=3, column=1, sticky="e")
        
        tk.Label(totals_frame, text="Total:", font=("Arial", 12, "bold"), bg=COLOR_LIGHT).grid(row=4, column=0, sticky="w")
        self.total_label = tk.Label(totals_frame, text=format_currency(0), font=("Arial", 12, "bold"), bg=COLOR_LIGHT, fg=COLOR_DANGER)
        self.total_label.grid(row=4, column=1, sticky="e")

        tk.Label(totals_frame, text="Customer:", font=FONT_NORMAL, bg=COLOR_LIGHT).grid(row=5, column=0, sticky="w")
        self.customer_var = tk.StringVar(value="Walk-in")
        self.customer_combo = ttk.Combobox(totals_frame, textvariable=self.customer_var, state="readonly", width=20)
        self.customer_combo.grid(row=5, column=1, sticky="e", padx=5, pady=(4, 0))
        self.customer_combo.bind("<<ComboboxSelected>>", lambda e: self.update_totals())
        
        # Checkout section
        checkout_frame = tk.Frame(cart_frame, bg=COLOR_LIGHT)
        checkout_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(checkout_frame, text="Payment Method:", bg=COLOR_LIGHT).pack(side=tk.LEFT)
        self.payment_var = tk.StringVar(value="Cash")
        payment_combo = ttk.Combobox(checkout_frame, textvariable=self.payment_var, values=["Cash", "Card", "Mobile Money", "Split"], state="readonly", width=15)
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

    def load_customers(self):
        """Load customers for checkout assignment."""
        try:
            response = self.api_client.get_customers(per_page=200)
            data = response.get("data") or {}
            self.customers = response.get("customers") or data.get("items") or []

            names = ["Walk-in"]
            self.customer_id_map = {"Walk-in": None}
            self.customer_points_map = {"Walk-in": 0}
            for customer in self.customers:
                label = f"{customer.get('name', '')} ({customer.get('id', '')})"
                names.append(label)
                self.customer_id_map[label] = customer.get("id")
                self.customer_points_map[label] = int(customer.get("loyalty_points", 0) or 0)

            self.customer_combo["values"] = names
            self.customer_var.set("Walk-in")
            self.update_totals()
        except APIError:
            self.customer_combo["values"] = ["Walk-in"]
            self.customer_var.set("Walk-in")

    def _get_selected_customer_points(self):
        selected = self.customer_var.get() or "Walk-in"
        return int(self.customer_points_map.get(selected, 0) or 0)

    def _calculate_discount_breakdown(self, subtotal: float):
        manual_discount = 0.0
        try:
            manual_discount = float(self.discount_entry.get() or 0)
        except ValueError:
            manual_discount = 0.0
            self.discount_entry.delete(0, tk.END)
            self.discount_entry.insert(0, "0")

        if manual_discount < 0:
            manual_discount = 0.0

        loyalty_discount = 0.0
        customer_id = self._get_selected_customer_id()
        customer_points = self._get_selected_customer_points() if customer_id is not None else 0
        if customer_id is not None and customer_points >= LOYALTY_POINTS_THRESHOLD:
            loyalty_discount = round(subtotal * LOYALTY_DISCOUNT_RATE, 2)

        total_discount = manual_discount + loyalty_discount
        if total_discount > subtotal:
            total_discount = subtotal

        return manual_discount, loyalty_discount, total_discount
    
    def display_products(self):
        """Display products in listbox"""
        self.products_listbox.delete(0, tk.END)
        for product in self.products:
            display_text = f"{product.get('name', '')} - {format_currency(product.get('price', 0))} (Stock: {product.get('quantity_in_stock', 0)})"
            self.products_listbox.insert(tk.END, display_text)
    
    def filter_products(self):
        """Filter products by search term"""
        search_term = self.search_var.get().lower()
        self.products_listbox.delete(0, tk.END)
        
        for product in self.products:
            if search_term in product.get('name', '').lower():
                display_text = f"{product.get('name', '')} - {format_currency(product.get('price', 0))} (Stock: {product.get('quantity_in_stock', 0)})"
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

        stock = int(product.get("quantity_in_stock", 0))
        if stock <= 0:
            show_error("Error", "This product is out of stock")
            return
        
        # Check if product already in cart
        cart_item = next((item for item in self.cart_items if item['id'] == product['id']), None)
        if cart_item:
            if cart_item['qty'] >= stock:
                show_error("Error", "Cannot add more than available stock")
                return
            cart_item['qty'] += 1
        else:
            unit_price = float(parse_currency(product.get('price', 0)))
            self.cart_items.append({
                'id': product['id'],
                'name': product['name'],
                'price': unit_price,
                'qty': 1,
                'stock': stock,
            })
        
        self.update_cart_display()
        self.update_totals()

    def edit_cart_quantity(self):
        """Edit the quantity of the selected cart item."""
        selection = self.cart_tree.selection()
        if not selection:
            show_error("Error", "Select an item to edit")
            return

        item = self.cart_tree.item(selection[0])
        product_id = int(item["text"])
        cart_item = next((entry for entry in self.cart_items if entry['id'] == product_id), None)
        if not cart_item:
            show_error("Error", "Cart item not found")
            return

        current_qty = int(cart_item.get('qty', 1))
        stock = int(cart_item.get('stock', 0))
        if stock <= 0:
            show_error("Error", "Available stock is not set for this item")
            return

        result = show_int_input_dialog(
            "Edit Quantity",
            f"Enter quantity for {cart_item.get('name', '')} (1 - {stock}):",
            parent=self,
        )
        if result is None:
            return

        new_qty = int(result)
        if new_qty <= 0:
            self.cart_items = [entry for entry in self.cart_items if entry['id'] != product_id]
            self.update_cart_display()
            self.update_totals()
            return

        if new_qty > stock:
            show_error("Error", f"Quantity cannot exceed available stock ({stock})")
            return

        if new_qty == current_qty:
            return

        cart_item['qty'] = new_qty
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
            unit_price = float(parse_currency(item.get('price', 0)))
            total = unit_price * int(item.get('qty', 0))
            self.cart_tree.insert("", tk.END, text=item['id'], values=(
                item['name'],
                item['qty'],
                format_currency(unit_price),
                format_currency(total)
            ))
    
    def update_totals(self):
        """Update total calculations"""
        if not self.cart_items:
            self.subtotal_label.config(text=format_currency(0))
            self.loyalty_discount_label.config(text=format_currency(0))
            self.tax_label.config(text=format_currency(0))
            self.total_label.config(text=format_currency(0))
            self.tax_title_label.config(text=f"Tax ({gui_config.TAX_RATE*100:.0f}%):")
            return

        subtotal = sum(float(parse_currency(item.get('price', 0))) * int(item.get('qty', 0)) for item in self.cart_items)
        _, loyalty_discount, discount = self._calculate_discount_breakdown(subtotal)
        
        tax_rate = gui_config.TAX_RATE
        tax = (subtotal - discount) * tax_rate
        total = subtotal - discount + tax
        self.tax_title_label.config(text=f"Tax ({tax_rate*100:.0f}%):")
        
        self.subtotal_label.config(text=format_currency(subtotal))
        self.loyalty_discount_label.config(text=format_currency(loyalty_discount))
        self.tax_label.config(text=format_currency(tax))
        self.total_label.config(text=format_currency(total))

    def _get_selected_customer_id(self):
        selected = self.customer_var.get() or "Walk-in"
        return self.customer_id_map.get(selected)

    @staticmethod
    def _normalize_payment_method(value: str) -> str:
        """Map UI labels to backend payment method values."""
        normalized = (value or "").strip().lower()
        if normalized in {"cash", "card", "split", "mobile"}:
            return normalized
        if normalized == "mobile money":
            return "mobile"
        return "cash"

    def _finalize_sale(self, sale_data, subtotal, discount, tax_rate, total, payment_method, receipt_display_method=None):
        """Send checkout to the API, render receipt, and refresh the UI."""
        response = self.api_client.create_sale(sale_data)
        payload = response.get("data") or response
        sale_id = payload.get("id", "N/A")
        financials = payload.get("financials") or {}
        receipt_tax = financials.get("tax_amount", (subtotal - discount) * tax_rate)
        receipt_total = financials.get("grand_total", total)
        receipt_change = financials.get("change_amount", 0)
        payments_info = payload.get("payments") or []

        from ..utils.receipt import Receipt
        display_method = receipt_display_method or payment_method
        if payment_method == "split" and payments_info:
            display_method = "split"

        receipt = Receipt(
            sale_id,
            self.cart_items,
            subtotal,
            receipt_tax,
            receipt_total,
            discount,
            display_method,
            tax_rate,
        )
        receipt_text = receipt.generate_text_receipt()
        if receipt_change:
            receipt_text += f"\nChange: {format_currency(receipt_change)}\n"

        from ..utils.receipt_dialog import ReceiptDialog
        ReceiptDialog(self.master, receipt_text)

        self.cart_items = []
        self.update_cart_display()
        self.update_totals()
        self.discount_entry.delete(0, tk.END)
        self.discount_entry.insert(0, "0")

        self.load_products()
        self.load_customers()

        show_success("Success", f"Sale completed! Receipt ID: {sale_id}")

    def _run_paystack_payment_flow(self, method: str, amount: float):
        """Initialize and verify a single Paystack payment flow."""
        dialog = tk.Toplevel(self)
        method_label = "Mobile Money" if method == "mobile" else "Card"
        dialog.title(f"{method_label} Payment")
        dialog.geometry("560x360")
        dialog.resizable(False, False)

        result = {"confirmed": False, "reference": None}

        selected_customer = (self.customer_var.get() or "Walk-in").strip()
        default_customer_name = selected_customer.split("(", 1)[0].strip() or "Walk-in Customer"
        customer_name_var = tk.StringVar(value=default_customer_name)
        email_var = tk.StringVar(value=DEFAULT_PAYSTACK_EMAIL)
        phone_var = tk.StringVar()
        status_var = tk.StringVar(value="Enter customer details and initialize payment.")
        reference_var = tk.StringVar()

        tk.Label(
            dialog,
            text=f"{method_label} payment via Paystack",
            font=FONT_HEADING,
        ).pack(anchor="w", padx=16, pady=(14, 4))

        amount_label = tk.Label(dialog, text=f"Amount Due: {format_currency(amount)}", font=FONT_NORMAL)
        amount_label.pack(anchor="w", padx=16, pady=(0, 10))

        form = tk.Frame(dialog)
        form.pack(fill=tk.X, padx=16)
        tk.Label(form, text="Customer Name:").grid(row=0, column=0, sticky="w")
        customer_name_entry = tk.Entry(form, textvariable=customer_name_var, width=32)
        customer_name_entry.grid(row=0, column=1, sticky="w", padx=8, pady=4)

        tk.Label(form, text="Email (optional):").grid(row=1, column=0, sticky="w")
        email_entry = tk.Entry(form, textvariable=email_var, width=32)
        email_entry.grid(row=1, column=1, sticky="w", padx=8, pady=4)

        tk.Label(form, text="Phone (optional):").grid(row=2, column=0, sticky="w")
        phone_entry = tk.Entry(form, textvariable=phone_var, width=26)
        phone_entry.grid(row=2, column=1, sticky="w", padx=8, pady=4)

        status_label = tk.Label(dialog, textvariable=status_var, fg=COLOR_DARK, wraplength=520, justify="left")
        status_label.pack(anchor="w", padx=16, pady=(12, 8))

        actions = tk.Frame(dialog)
        actions.pack(fill=tk.X, padx=16, pady=8)

        init_btn = tk.Button(actions, text="Initialize", bg=COLOR_PRIMARY, fg=COLOR_WHITE, width=14)
        init_btn.pack(side=tk.LEFT, padx=(0, 8))

        verify_btn = tk.Button(actions, text="Verify Payment", bg=COLOR_SUCCESS, fg=COLOR_WHITE, width=14, state=tk.DISABLED)
        verify_btn.pack(side=tk.LEFT, padx=(0, 8))

        cancel_btn = tk.Button(actions, text="Cancel", bg=COLOR_DANGER, fg=COLOR_WHITE, width=14)
        cancel_btn.pack(side=tk.LEFT)

        def close_dialog():
            dialog.destroy()

        def initialize_payment():
            customer_name = (customer_name_var.get() or "").strip()
            if not customer_name:
                show_error("Error", "Customer name is required")
                return
            email = (email_var.get() or "").strip()
            if email and "@" not in email:
                show_error("Error", "Enter a valid email or leave it empty")
                return
            phone_number = re.sub(r"\D", "", phone_var.get())

            payload = {
                "method": method,
                "channel": method,
                "source": "cashier_gui",
            }
            try:
                response = self.api_client.initialize_paystack_payment(
                    amount=amount,
                    customer_name=customer_name,
                    email=email,
                    method=method,
                    phone=phone_number,
                    metadata=payload,
                )
                data = response.get("data") or {}
                checkout_url = data.get("checkout_url") or data.get("authorization_url")
                reference = data.get("reference")
                if not reference:
                    raise APIError("No Paystack reference returned")
                reference_var.set(reference)
                status_var.set("Payment initialized. Complete it in the browser, then click Verify Payment.")
                status_label.config(fg=COLOR_SUCCESS)
                verify_btn.config(state=tk.NORMAL)
                init_btn.config(state=tk.DISABLED)

                if checkout_url:
                    webbrowser.open(checkout_url)
            except APIError as error:
                status_var.set(f"Initialize failed: {error}")
                status_label.config(fg=COLOR_DANGER)

        def verify_payment():
            reference = reference_var.get()
            if not reference:
                show_error("Error", "Initialize payment first")
                return

            try:
                response = self.api_client.verify_paystack_payment(reference)
                data = response.get("data") or {}
                paid = bool(data.get("paid"))
                paid_amount = float(data.get("amount") or 0)
                if not paid:
                    status_var.set("Verification failed: Paystack transaction is not successful yet.")
                    status_label.config(fg=COLOR_DANGER)
                    return
                if paid_amount + 0.01 < amount:
                    status_var.set("Verification failed: paid amount is below expected amount.")
                    status_label.config(fg=COLOR_DANGER)
                    return

                result["confirmed"] = True
                result["reference"] = reference
                close_dialog()
            except APIError as error:
                status_var.set(f"Verification failed: {error}")
                status_label.config(fg=COLOR_DANGER)

        init_btn.config(command=initialize_payment)
        verify_btn.config(command=verify_payment)
        cancel_btn.config(command=close_dialog)
        dialog.protocol("WM_DELETE_WINDOW", close_dialog)
        customer_name_entry.focus()

        dialog.transient(self)
        dialog.grab_set()
        self.wait_window(dialog)
        return result

    def _attach_paystack_references_for_split(self, payments):
        """Collect and attach Paystack references for split non-cash payments."""
        updated = []
        for payment in payments:
            method = payment.get("method")
            amount = float(payment.get("amount") or 0)
            entry = dict(payment)
            if method in {"card", "mobile", "paystack"}:
                flow_result = self._run_paystack_payment_flow(method, amount)
                if not flow_result.get("confirmed"):
                    return None
                entry["reference"] = flow_result.get("reference")
            updated.append(entry)
        return updated

    def _prompt_split_payments(self, total_due: float):
        """Collect split payment as cash plus one digital method."""
        dialog = tk.Toplevel(self)
        dialog.title("Split Payment")
        dialog.geometry("440x300")
        dialog.resizable(False, False)
        dialog.grid_columnconfigure(0, minsize=140)
        dialog.grid_columnconfigure(1, minsize=240, weight=1)

        tk.Label(dialog, text=f"Total Due: {format_currency(total_due)}", font=FONT_HEADING).grid(
            row=0,
            column=0,
            columnspan=2,
            padx=16,
            pady=10,
            sticky="w",
        )

        tk.Label(dialog, text="Cash:").grid(row=1, column=0, padx=(16, 8), pady=6, sticky="e")
        cash_entry = tk.Entry(dialog, width=24)
        cash_entry.insert(0, "0")
        cash_entry.grid(row=1, column=1, padx=(8, 16), pady=6, sticky="ew")

        tk.Label(dialog, text="Digital Method:").grid(row=2, column=0, padx=(16, 8), pady=6, sticky="e")
        digital_method_var = tk.StringVar(value="Card")
        digital_method_combo = ttk.Combobox(
            dialog,
            textvariable=digital_method_var,
            values=["Card", "Mobile Money"],
            state="readonly",
        )
        digital_method_combo.grid(row=2, column=1, padx=(8, 16), pady=6, sticky="ew")

        tk.Label(dialog, text="Digital Amount:").grid(row=3, column=0, padx=(16, 8), pady=6, sticky="e")
        digital_amount_var = tk.StringVar(value=f"{total_due:.2f}")
        digital_amount_entry = tk.Entry(dialog, textvariable=digital_amount_var, width=24, state="readonly")
        digital_amount_entry.grid(row=3, column=1, padx=(8, 16), pady=6, sticky="ew")

        hint_var = tk.StringVar(value="Enter cash received. Remaining amount is calculated automatically.")
        tk.Label(dialog, textvariable=hint_var, fg=COLOR_DARK, wraplength=400, justify="left").grid(
            row=4,
            column=0,
            columnspan=2,
            padx=16,
            pady=(2, 8),
            sticky="w",
        )

        result = {"confirmed": False, "payments": []}

        def calculate_remaining() -> tuple[float, float] | tuple[None, None]:
            raw_value = (cash_entry.get() or "").strip()
            if not raw_value:
                raw_value = "0"
            try:
                cash_value = float(raw_value)
            except ValueError:
                digital_amount_var.set("-")
                hint_var.set("Cash must be numeric.")
                return None, None

            if cash_value < 0:
                digital_amount_var.set("-")
                hint_var.set("Cash cannot be negative.")
                return None, None

            remaining = round(total_due - cash_value, 2)
            if remaining <= 0:
                digital_amount_var.set("0.00")
                hint_var.set("Cash covers the total. Reduce cash value to keep this as a split payment.")
                return cash_value, 0.0

            digital_amount_var.set(f"{remaining:.2f}")
            hint_var.set("Remaining amount has been assigned to the selected digital method.")
            return cash_value, remaining

        cash_entry.bind("<KeyRelease>", lambda _e: calculate_remaining())
        cash_entry.bind("<FocusOut>", lambda _e: calculate_remaining())
        calculate_remaining()

        def confirm_split():
            cash, remaining = calculate_remaining()
            if cash is None or remaining is None:
                show_error("Error", "Cash amount must be numeric and non-negative")
                return

            if cash <= 0:
                show_error("Error", "Enter a cash amount greater than zero for split payment")
                return

            if remaining <= 0:
                show_error("Error", "Cash covers the full total. Use Cash payment or reduce cash amount.")
                return

            selected_digital = (digital_method_var.get() or "Card").strip().lower()
            digital_method = "mobile" if selected_digital == "mobile money" else "card"

            payments = [
                {"method": "cash", "amount": round(cash, 2)},
                {"method": digital_method, "amount": round(remaining, 2)},
            ]

            result["confirmed"] = True
            result["payments"] = payments
            dialog.destroy()

        tk.Button(dialog, text="Confirm", bg=COLOR_SUCCESS, fg=COLOR_WHITE, command=confirm_split, width=16).grid(row=6, column=0, padx=10, pady=20)
        tk.Button(dialog, text="Cancel", command=dialog.destroy, width=16).grid(row=6, column=1, padx=10, pady=20)

        dialog.transient(self)
        dialog.grab_set()
        self.wait_window(dialog)
        return result
    
    def checkout(self):
        """Process checkout and create sale"""
        if not self.cart_items:
            show_error("Error", "Cart is empty")
            return
        
        try:
            # Calculate totals
            subtotal = sum(float(parse_currency(item.get('price', 0))) * int(item.get('qty', 0)) for item in self.cart_items)
            manual_discount, loyalty_discount, discount = self._calculate_discount_breakdown(subtotal)
            tax_rate = gui_config.TAX_RATE
            tax = (subtotal - discount) * tax_rate
            total = subtotal - discount + tax
            payment_method = self._normalize_payment_method(self.payment_var.get())
            customer_id = self._get_selected_customer_id()

            payments = None
            amount_tendered = None
            if payment_method == "mobile":
                flow_result = self._run_paystack_payment_flow("mobile", total)
                if not flow_result.get("confirmed"):
                    return
                sale_data = {
                    "items": [
                        {
                            "product_id": item['id'],
                            "quantity": item['qty'],
                        }
                        for item in self.cart_items
                    ],
                    "discount": manual_discount,
                    "loyalty_discount": loyalty_discount,
                    "tax_rate": tax_rate,
                    "payment_method": "mobile",
                    "customer_id": customer_id,
                    "amount_tendered": total,
                    "payment_reference": flow_result.get("reference"),
                }
                self._finalize_sale(sale_data, subtotal, discount, tax_rate, total, "mobile", "mobile money")
                return
            if payment_method == "card":
                flow_result = self._run_paystack_payment_flow("card", total)
                if not flow_result.get("confirmed"):
                    return
            if payment_method == "split":
                split_result = self._prompt_split_payments(total)
                if not split_result.get("confirmed"):
                    return
                payments = split_result.get("payments", [])
                payments = self._attach_paystack_references_for_split(payments)
                if payments is None:
                    return
            elif payment_method == "cash":
                amount_tendered = total
            
            # Prepare sale data
            sale_data = {
                "items": [
                    {
                        "product_id": item['id'],
                        "quantity": item['qty'],
                    }
                    for item in self.cart_items
                ],
                "discount": manual_discount,
                "loyalty_discount": loyalty_discount,
                "tax_rate": tax_rate,
                "payment_method": payment_method,
                "customer_id": customer_id,
            }
            if payments:
                sale_data["payments"] = payments
            if payment_method == "card":
                sale_data["payment_reference"] = flow_result.get("reference")
            if amount_tendered is not None:
                sale_data["amount_tendered"] = amount_tendered
            
            self._finalize_sale(sale_data, subtotal, discount, tax_rate, total, payment_method)
        
        except ValueError as e:
            show_error("Error", "Invalid discount amount")
        except APIError as e:
            show_error("Error", f"Failed to process sale: {str(e)}")
        except Exception as e:
            show_error("Error", f"Unexpected error: {str(e)}")
