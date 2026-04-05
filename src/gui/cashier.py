"""
Cashier Screen - Main POS Interface
"""
import re
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from .config import *
from . import config as gui_config
from .utils.formatters import format_currency, parse_currency
from .utils.dialogs import show_error, show_success, show_confirmation
from .utils.api_client import APIError

class CashierScreen(tk.Frame):
    """Main cashier POS interface"""
    
    def __init__(self, parent, api_client):
        super().__init__(parent, bg=COLOR_LIGHT)
        self.api_client = api_client
        self.cart_items = []
        self.products = []
        self.customers = []
        self.customer_id_map = {"Walk-in": None}
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
        self.subtotal_label = tk.Label(totals_frame, text=format_currency(0), font=FONT_NORMAL, bg=COLOR_LIGHT, fg=COLOR_SUCCESS)
        self.subtotal_label.grid(row=0, column=1, sticky="e")
        
        tk.Label(totals_frame, text="Discount:", font=FONT_NORMAL, bg=COLOR_LIGHT).grid(row=1, column=0, sticky="w")
        self.discount_entry = tk.Entry(totals_frame, width=15, font=FONT_NORMAL)
        self.discount_entry.insert(0, "0")
        self.discount_entry.grid(row=1, column=1, sticky="e", padx=5)
        self.discount_entry.bind("<KeyRelease>", lambda e: self.update_totals())
        
        self.tax_title_label = tk.Label(totals_frame, text=f"Tax ({gui_config.TAX_RATE*100:.0f}%):", font=FONT_NORMAL, bg=COLOR_LIGHT)
        self.tax_title_label.grid(row=2, column=0, sticky="w")
        self.tax_label = tk.Label(totals_frame, text=format_currency(0), font=FONT_NORMAL, bg=COLOR_LIGHT, fg=COLOR_WARNING)
        self.tax_label.grid(row=2, column=1, sticky="e")
        
        tk.Label(totals_frame, text="Total:", font=("Arial", 12, "bold"), bg=COLOR_LIGHT).grid(row=3, column=0, sticky="w")
        self.total_label = tk.Label(totals_frame, text=format_currency(0), font=("Arial", 12, "bold"), bg=COLOR_LIGHT, fg=COLOR_DANGER)
        self.total_label.grid(row=3, column=1, sticky="e")

        tk.Label(totals_frame, text="Customer:", font=FONT_NORMAL, bg=COLOR_LIGHT).grid(row=4, column=0, sticky="w")
        self.customer_var = tk.StringVar(value="Walk-in")
        self.customer_combo = ttk.Combobox(totals_frame, textvariable=self.customer_var, state="readonly", width=20)
        self.customer_combo.grid(row=4, column=1, sticky="e", padx=5, pady=(4, 0))
        
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
            for customer in self.customers:
                label = f"{customer.get('name', '')} ({customer.get('id', '')})"
                names.append(label)
                self.customer_id_map[label] = customer.get("id")

            self.customer_combo["values"] = names
            self.customer_var.set("Walk-in")
        except APIError:
            self.customer_combo["values"] = ["Walk-in"]
            self.customer_var.set("Walk-in")
    
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
            self.tax_label.config(text=format_currency(0))
            self.total_label.config(text=format_currency(0))
            self.tax_title_label.config(text=f"Tax ({gui_config.TAX_RATE*100:.0f}%):")
            return

        subtotal = sum(float(parse_currency(item.get('price', 0))) * int(item.get('qty', 0)) for item in self.cart_items)
        
        try:
            discount = float(self.discount_entry.get() or 0)
        except ValueError:
            discount = 0
            self.discount_entry.delete(0, tk.END)
            self.discount_entry.insert(0, "0")

        if discount < 0:
            discount = 0
        if discount > subtotal:
            discount = subtotal
        
        tax_rate = gui_config.TAX_RATE
        tax = (subtotal - discount) * tax_rate
        total = subtotal - discount + tax
        self.tax_title_label.config(text=f"Tax ({tax_rate*100:.0f}%):")
        
        self.subtotal_label.config(text=format_currency(subtotal))
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

    def _show_mobile_money_flow(self, sale_data, subtotal, discount, tax_rate, total):
        """Run a guided mobile money payment flow with success and failure states."""
        dialog = tk.Toplevel(self)
        dialog.title("Mobile Money Payment")
        dialog.geometry("520x360")
        dialog.resizable(False, False)

        state = {"after_id": None}
        phone_var = tk.StringVar()
        info_label = tk.Label(dialog, text="Enter buyer phone number to start the mobile money process.", wraplength=480, justify="left", font=FONT_NORMAL)
        info_label.pack(anchor="w", padx=16, pady=(16, 8))

        amount_label = tk.Label(dialog, text=f"Amount Due: {format_currency(total)}", font=FONT_HEADING)
        amount_label.pack(anchor="w", padx=16, pady=(0, 10))

        form = tk.Frame(dialog)
        form.pack(fill=tk.X, padx=16)
        tk.Label(form, text="Buyer Phone Number:").grid(row=0, column=0, sticky="w")
        phone_entry = tk.Entry(form, textvariable=phone_var, width=26)
        phone_entry.grid(row=0, column=1, sticky="w", padx=8)

        status_label = tk.Label(dialog, text="Status: Waiting for phone number", fg=COLOR_DARK, wraplength=480, justify="left")
        status_label.pack(anchor="w", padx=16, pady=(12, 8))

        actions = tk.Frame(dialog)
        actions.pack(fill=tk.X, padx=16, pady=8)

        request_btn = tk.Button(actions, text="Send Request", bg=COLOR_PRIMARY, fg=COLOR_WHITE, width=14)
        request_btn.pack(side=tk.LEFT, padx=(0, 8))

        accept_btn = tk.Button(actions, text="Buyer Accepted", bg=COLOR_SUCCESS, fg=COLOR_WHITE, width=14, state=tk.DISABLED)
        accept_btn.pack(side=tk.LEFT, padx=(0, 8))

        decline_btn = tk.Button(actions, text="Buyer Declined", bg=COLOR_DANGER, fg=COLOR_WHITE, width=14, state=tk.DISABLED)
        decline_btn.pack(side=tk.LEFT)

        verification_frame = tk.Frame(dialog)
        verification_frame.pack(fill=tk.X, padx=16, pady=(10, 0))
        verification_frame.pack_forget()

        verify_btn = tk.Button(verification_frame, text="Receipt Found", bg=COLOR_SUCCESS, fg=COLOR_WHITE, width=14, state=tk.DISABLED)
        verify_btn.pack(side=tk.LEFT, padx=(0, 8))

        missing_btn = tk.Button(verification_frame, text="Receipt Missing", bg=COLOR_WARNING, fg=COLOR_WHITE, width=14, state=tk.DISABLED)
        missing_btn.pack(side=tk.LEFT)

        retry_btn = tk.Button(dialog, text="Retry", width=12, state=tk.DISABLED)
        retry_btn.pack(anchor="e", padx=16, pady=(8, 0))

        def clear_after_job():
            if state["after_id"] is not None:
                try:
                    dialog.after_cancel(state["after_id"])
                except Exception:
                    pass
                state["after_id"] = None

        def reset_flow(message):
            clear_after_job()
            status_label.config(text=message, fg=COLOR_DANGER)
            request_btn.config(state=tk.NORMAL)
            accept_btn.config(state=tk.DISABLED)
            decline_btn.config(state=tk.DISABLED)
            verify_btn.config(state=tk.DISABLED)
            missing_btn.config(state=tk.DISABLED)
            verification_frame.pack_forget()
            retry_btn.config(state=tk.NORMAL)

        def close_dialog():
            clear_after_job()
            dialog.destroy()

        def on_retry():
            phone_var.set("")
            status_label.config(text="Status: Waiting for phone number", fg=COLOR_DARK)
            request_btn.config(state=tk.NORMAL)
            accept_btn.config(state=tk.DISABLED)
            decline_btn.config(state=tk.DISABLED)
            verify_btn.config(state=tk.DISABLED)
            missing_btn.config(state=tk.DISABLED)
            verification_frame.pack_forget()
            retry_btn.config(state=tk.DISABLED)
            phone_entry.focus()

        def send_request():
            phone_number = re.sub(r"\D", "", phone_var.get())
            if len(phone_number) < 9:
                show_error("Error", "Enter a valid buyer phone number")
                return

            request_btn.config(state=tk.DISABLED)
            status_label.config(text=f"Status: Request sent to {phone_number}. Waiting for buyer approval...", fg=COLOR_PRIMARY)
            accept_btn.config(state=tk.NORMAL)
            decline_btn.config(state=tk.NORMAL)
            retry_btn.config(state=tk.DISABLED)

        def buyer_declined():
            reset_flow("Transaction failed: buyer declined the payment request.")

        def buyer_accepted():
            clear_after_job()
            status_label.config(text="Status: Buyer accepted. System checking payment receipt...", fg=COLOR_PRIMARY)
            accept_btn.config(state=tk.DISABLED)
            decline_btn.config(state=tk.DISABLED)
            verification_frame.pack(fill=tk.X, padx=16, pady=(10, 0))
            verify_btn.config(state=tk.NORMAL)
            missing_btn.config(state=tk.NORMAL)
            retry_btn.config(state=tk.DISABLED)

        def receipt_found():
            clear_after_job()
            status_label.config(text="Status: Receipt verified. Finalizing sale...", fg=COLOR_SUCCESS)
            verify_btn.config(state=tk.DISABLED)
            missing_btn.config(state=tk.DISABLED)

            sale_data["payment_method"] = "mobile"
            sale_data["payment_reference"] = f"MobileMoney:{re.sub(r'\\D', '', phone_var.get())}"
            sale_data["amount_tendered"] = total

            def complete():
                try:
                    self._finalize_sale(sale_data, subtotal, discount, tax_rate, total, "mobile", "mobile money")
                    close_dialog()
                except APIError as error:
                    reset_flow(f"Transaction failed: {error}")
                except Exception as error:
                    reset_flow(f"Transaction failed: {error}")

            state["after_id"] = dialog.after(700, complete)

        def receipt_missing():
            reset_flow("Transaction failed: payment receipt was not found.")

        request_btn.config(command=send_request)
        accept_btn.config(command=buyer_accepted)
        decline_btn.config(command=buyer_declined)
        verify_btn.config(command=receipt_found)
        missing_btn.config(command=receipt_missing)
        retry_btn.config(command=on_retry)
        dialog.protocol("WM_DELETE_WINDOW", close_dialog)
        phone_entry.focus()

    def _prompt_split_payments(self, total_due: float):
        """Collect split payment amounts for cash/card/mobile."""
        dialog = tk.Toplevel(self)
        dialog.title("Split Payment")
        dialog.geometry("420x280")
        dialog.resizable(False, False)

        tk.Label(dialog, text=f"Total Due: {format_currency(total_due)}", font=FONT_HEADING).grid(row=0, column=0, columnspan=2, padx=10, pady=10)

        tk.Label(dialog, text="Cash:").grid(row=1, column=0, padx=10, pady=6, sticky="w")
        cash_entry = tk.Entry(dialog, width=22)
        cash_entry.insert(0, "0")
        cash_entry.grid(row=1, column=1, padx=10, pady=6)

        tk.Label(dialog, text="Card:").grid(row=2, column=0, padx=10, pady=6, sticky="w")
        card_entry = tk.Entry(dialog, width=22)
        card_entry.insert(0, "0")
        card_entry.grid(row=2, column=1, padx=10, pady=6)

        tk.Label(dialog, text="Mobile:").grid(row=3, column=0, padx=10, pady=6, sticky="w")
        mobile_entry = tk.Entry(dialog, width=22)
        mobile_entry.insert(0, "0")
        mobile_entry.grid(row=3, column=1, padx=10, pady=6)

        result = {"confirmed": False, "payments": []}

        def confirm_split():
            try:
                cash = float(cash_entry.get() or 0)
                card = float(card_entry.get() or 0)
                mobile = float(mobile_entry.get() or 0)
            except ValueError:
                show_error("Error", "Split amounts must be numeric")
                return

            payments = []
            if cash > 0:
                payments.append({"method": "cash", "amount": cash})
            if card > 0:
                payments.append({"method": "card", "amount": card})
            if mobile > 0:
                payments.append({"method": "mobile", "amount": mobile})

            if not payments:
                show_error("Error", "At least one split amount must be greater than zero")
                return

            total_paid = cash + card + mobile
            if total_paid < total_due:
                show_error("Error", "Split amounts are less than total due")
                return

            result["confirmed"] = True
            result["payments"] = payments
            dialog.destroy()

        tk.Button(dialog, text="Confirm", bg=COLOR_SUCCESS, fg=COLOR_WHITE, command=confirm_split, width=16).grid(row=4, column=0, padx=10, pady=20)
        tk.Button(dialog, text="Cancel", command=dialog.destroy, width=16).grid(row=4, column=1, padx=10, pady=20)

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
            discount = float(self.discount_entry.get() or 0)
            if discount < 0:
                discount = 0
            if discount > subtotal:
                discount = subtotal
            tax_rate = gui_config.TAX_RATE
            tax = (subtotal - discount) * tax_rate
            total = subtotal - discount + tax
            payment_method = self._normalize_payment_method(self.payment_var.get())
            customer_id = self._get_selected_customer_id()

            payments = None
            amount_tendered = None
            if payment_method == "mobile":
                sale_data = {
                    "items": [
                        {
                            "product_id": item['id'],
                            "quantity": item['qty'],
                        }
                        for item in self.cart_items
                    ],
                    "discount": discount,
                    "tax_rate": tax_rate,
                    "payment_method": "mobile",
                    "customer_id": customer_id,
                    "amount_tendered": total,
                }
                self._show_mobile_money_flow(sale_data, subtotal, discount, tax_rate, total)
                return
            if payment_method == "split":
                split_result = self._prompt_split_payments(total)
                if not split_result.get("confirmed"):
                    return
                payments = split_result.get("payments", [])
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
                "discount": discount,
                "tax_rate": tax_rate,
                "payment_method": payment_method,
                "customer_id": customer_id,
            }
            if payments:
                sale_data["payments"] = payments
            if amount_tendered is not None:
                sale_data["amount_tendered"] = amount_tendered
            
            self._finalize_sale(sale_data, subtotal, discount, tax_rate, total, payment_method)
        
        except ValueError as e:
            show_error("Error", "Invalid discount amount")
        except APIError as e:
            show_error("Error", f"Failed to process sale: {str(e)}")
        except Exception as e:
            show_error("Error", f"Unexpected error: {str(e)}")
