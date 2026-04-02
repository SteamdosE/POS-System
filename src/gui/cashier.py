"""
Cashier Screen - Main POS Interface
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from .config import *
from .utils.formatters import format_currency, parse_currency
from .utils.dialogs import show_error, show_success, show_confirmation
from .utils.api_client import APIError


class ReceiptDialog(tk.Toplevel):
    """Modal receipt preview dialog shown after a successful checkout."""

    def __init__(self, parent, receipt_data):
        super().__init__(parent)
        self.title("Receipt - POS System")
        self.configure(bg=COLOR_WHITE)
        self.resizable(False, False)
        self.grab_set()
        self._build(receipt_data)
        self.update_idletasks()
        # centre over parent window
        px = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")

    def _build(self, d):
        outer = tk.Frame(self, bg=COLOR_WHITE, padx=24, pady=16)
        outer.pack(fill=tk.BOTH, expand=True)

        def lbl(text, font=FONT_NORMAL, fg=COLOR_DARK, anchor="center"):
            tk.Label(outer, text=text, font=font, bg=COLOR_WHITE,
                     fg=fg, anchor=anchor).pack(fill=tk.X)

        def sep():
            ttk.Separator(outer, orient="horizontal").pack(fill=tk.X, pady=4)

        # ── header ────────────────────────────────────────────────────────────
        lbl("POS SYSTEM", font=FONT_TITLE, fg=COLOR_PRIMARY)
        lbl(d["datetime"], font=FONT_SMALL)
        lbl(f"Receipt #: {d['sale_id']}", font=FONT_SMALL)
        lbl(f"Cashier : {d['cashier']}", font=FONT_SMALL)
        customer_text = d.get("customer") or "Walk-in"
        lbl(f"Customer: {customer_text}", font=FONT_SMALL)
        sep()

        # ── items table ───────────────────────────────────────────────────────
        tbl = tk.Frame(outer, bg=COLOR_WHITE)
        tbl.pack(fill=tk.X)
        tbl.columnconfigure(0, weight=3)
        tbl.columnconfigure(1, weight=1)
        tbl.columnconfigure(2, weight=2)
        tbl.columnconfigure(3, weight=2)

        for col, heading in enumerate(("Item", "Qty", "Unit Price", "Line Total")):
            tk.Label(tbl, text=heading, font=FONT_SMALL, bg=COLOR_BORDER,
                     anchor="w" if col == 0 else "e",
                     relief="flat", padx=4).grid(row=0, column=col, sticky="ew", pady=1)

        for row_idx, item in enumerate(d["items"], start=1):
            bg = COLOR_WHITE if row_idx % 2 == 0 else "#FAFAFA"
            tk.Label(tbl, text=item["name"][:28], font=FONT_SMALL,
                     bg=bg, anchor="w", padx=4).grid(row=row_idx, column=0, sticky="ew")
            tk.Label(tbl, text=str(item["qty"]), font=FONT_SMALL,
                     bg=bg, anchor="e", padx=4).grid(row=row_idx, column=1, sticky="ew")
            tk.Label(tbl, text=format_currency(item["unit_price"]), font=FONT_SMALL,
                     bg=bg, anchor="e", padx=4).grid(row=row_idx, column=2, sticky="ew")
            tk.Label(tbl, text=format_currency(item["line_total"]), font=FONT_SMALL,
                     bg=bg, anchor="e", padx=4).grid(row=row_idx, column=3, sticky="ew")

        sep()

        # ── totals ────────────────────────────────────────────────────────────
        def total_row(label, value, bold=False):
            f = tk.Frame(outer, bg=COLOR_WHITE)
            f.pack(fill=tk.X, pady=1)
            font = FONT_HEADING if bold else FONT_NORMAL
            tk.Label(f, text=label, font=font, bg=COLOR_WHITE, anchor="w").pack(side=tk.LEFT)
            tk.Label(f, text=value, font=font, bg=COLOR_WHITE, anchor="e").pack(side=tk.RIGHT)

        total_row("Subtotal:", format_currency(d["subtotal"]))
        if d["discount"] > 0:
            total_row("Discount:", f"-{format_currency(d['discount'])}")
        total_row(f"Tax ({TAX_RATE * 100:.0f}%):", format_currency(d["tax"]))
        total_row("TOTAL:", format_currency(d["total"]), bold=True)
        total_row("Payment:", d["payment_method"].replace("_", " ").title())

        sep()
        tk.Button(outer, text="Close", command=self.destroy,
                  bg=COLOR_PRIMARY, fg=COLOR_WHITE, width=16,
                  cursor="hand2").pack(pady=4)


class CashierScreen(tk.Frame):
    """Main cashier/POS interface."""

    def __init__(self, parent, api_client):
        super().__init__(parent, bg=COLOR_LIGHT)
        self.api_client = api_client
        # cart: product_id (int) -> {"product": dict, "qty": int}
        self.cart = {}
        self.products = []
        self._setup_ui()
        self.load_products()

    # ── UI construction ───────────────────────────────────────────────────────

    def _setup_ui(self):
        """Build the full cashier UI layout."""
        # ── header bar ────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=COLOR_PRIMARY)
        header.pack(fill=tk.X)
        cashier_name = (self.api_client.user_data or {}).get("username", "Cashier")
        tk.Label(header, text=f"POS System  |  Cashier: {cashier_name}",
                 font=FONT_HEADING, bg=COLOR_PRIMARY, fg=COLOR_WHITE).pack(pady=8)

        # ── main 2-column area ────────────────────────────────────────────────
        content = tk.Frame(self, bg=COLOR_LIGHT)
        content.pack(fill=tk.BOTH, expand=True, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)

        self._build_product_panel(content)
        self._build_cart_panel(content)

    def _build_product_panel(self, parent):
        """Left panel: product search + treeview."""
        left = tk.LabelFrame(parent, text="Products", font=FONT_HEADING,
                             bg=COLOR_LIGHT, fg=COLOR_DARK)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, PADDING_MEDIUM))

        # ── search row ────────────────────────────────────────────────────────
        search_row = tk.Frame(left, bg=COLOR_LIGHT)
        search_row.pack(fill=tk.X, padx=PADDING_MEDIUM, pady=(PADDING_MEDIUM, PADDING_SMALL))

        tk.Label(search_row, text="Search:", bg=COLOR_LIGHT,
                 font=FONT_NORMAL).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._filter_products)
        tk.Entry(search_row, textvariable=self.search_var).pack(
            side=tk.LEFT, padx=PADDING_SMALL, fill=tk.X, expand=True)

        # ── SKU / barcode row ─────────────────────────────────────────────────
        sku_row = tk.Frame(left, bg=COLOR_LIGHT)
        sku_row.pack(fill=tk.X, padx=PADDING_MEDIUM, pady=(0, PADDING_SMALL))

        tk.Label(sku_row, text="SKU/Barcode:", bg=COLOR_LIGHT,
                 font=FONT_NORMAL).pack(side=tk.LEFT)
        self.sku_var = tk.StringVar()
        sku_entry = tk.Entry(sku_row, textvariable=self.sku_var, width=16)
        sku_entry.pack(side=tk.LEFT, padx=PADDING_SMALL)
        sku_entry.bind("<Return>", lambda _e: self._add_by_sku())
        tk.Button(sku_row, text="Add", bg=COLOR_PRIMARY, fg=COLOR_WHITE,
                  command=self._add_by_sku, cursor="hand2").pack(side=tk.LEFT)

        # ── products treeview ─────────────────────────────────────────────────
        cols = ("SKU", "Name", "Price", "Stock")
        self.products_tree = ttk.Treeview(left, columns=cols,
                                          show="headings", height=TABLE_HEIGHT)
        self.products_tree.heading("SKU", text="SKU")
        self.products_tree.heading("Name", text="Product")
        self.products_tree.heading("Price", text="Price")
        self.products_tree.heading("Stock", text="Stock")
        self.products_tree.column("SKU", width=70)
        self.products_tree.column("Name", width=160)
        self.products_tree.column("Price", width=80, anchor="e")
        self.products_tree.column("Stock", width=55, anchor="center")

        vsb = ttk.Scrollbar(left, orient="vertical",
                            command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=vsb.set)
        self.products_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                                padx=(PADDING_MEDIUM, 0), pady=PADDING_MEDIUM)
        vsb.pack(side=tk.LEFT, fill=tk.Y, pady=PADDING_MEDIUM)

        self.products_tree.bind("<Double-1>", self._add_to_cart_from_tree)

        hint = tk.Label(left, text="Double-click or enter SKU to add to cart",
                        font=FONT_SMALL, bg=COLOR_LIGHT, fg=COLOR_BORDER)
        hint.pack(pady=(0, PADDING_SMALL))

    def _build_cart_panel(self, parent):
        """Right panel: cart + customer + discount + totals + payment + checkout."""
        right = tk.LabelFrame(parent, text="Shopping Cart", font=FONT_HEADING,
                              bg=COLOR_LIGHT, fg=COLOR_DARK)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # ── cart treeview ─────────────────────────────────────────────────────
        cart_cols = ("Name", "Unit Price", "Qty", "Line Total")
        self.cart_tree = ttk.Treeview(right, columns=cart_cols,
                                      show="headings", height=10)
        self.cart_tree.heading("Name", text="Product")
        self.cart_tree.heading("Unit Price", text="Unit Price")
        self.cart_tree.heading("Qty", text="Qty")
        self.cart_tree.heading("Line Total", text="Line Total")
        self.cart_tree.column("Name", width=140)
        self.cart_tree.column("Unit Price", width=80, anchor="e")
        self.cart_tree.column("Qty", width=45, anchor="center")
        self.cart_tree.column("Line Total", width=90, anchor="e")
        self.cart_tree.pack(fill=tk.BOTH, expand=True,
                            padx=PADDING_MEDIUM, pady=(PADDING_MEDIUM, 0))

        # ── cart action buttons ───────────────────────────────────────────────
        cart_btns = tk.Frame(right, bg=COLOR_LIGHT)
        cart_btns.pack(fill=tk.X, padx=PADDING_MEDIUM, pady=PADDING_SMALL)

        tk.Button(cart_btns, text="+ Qty", width=7, bg=COLOR_SUCCESS, fg=COLOR_WHITE,
                  command=self._increase_qty, cursor="hand2").pack(side=tk.LEFT, padx=2)
        tk.Button(cart_btns, text="- Qty", width=7, bg=COLOR_WARNING, fg=COLOR_WHITE,
                  command=self._decrease_qty, cursor="hand2").pack(side=tk.LEFT, padx=2)
        tk.Button(cart_btns, text="Remove", width=7, bg=COLOR_DANGER, fg=COLOR_WHITE,
                  command=self._remove_item, cursor="hand2").pack(side=tk.LEFT, padx=2)

        ttk.Separator(right, orient="horizontal").pack(fill=tk.X, padx=PADDING_MEDIUM,
                                                       pady=PADDING_SMALL)

        # ── customer selection ────────────────────────────────────────────────
        cust_frame = tk.LabelFrame(right, text="Customer", font=FONT_NORMAL,
                                   bg=COLOR_LIGHT, fg=COLOR_DARK)
        cust_frame.pack(fill=tk.X, padx=PADDING_MEDIUM, pady=(0, PADDING_SMALL))

        self.customer_type = tk.StringVar(value="walkin")
        tk.Radiobutton(cust_frame, text="Walk-in", variable=self.customer_type,
                       value="walkin", bg=COLOR_LIGHT,
                       command=self._toggle_customer).pack(side=tk.LEFT, padx=PADDING_SMALL)
        tk.Radiobutton(cust_frame, text="Existing (ID):", variable=self.customer_type,
                       value="existing", bg=COLOR_LIGHT,
                       command=self._toggle_customer).pack(side=tk.LEFT)
        self.customer_id_var = tk.StringVar()
        self.customer_id_entry = tk.Entry(cust_frame, textvariable=self.customer_id_var,
                                          width=8, state="disabled")
        self.customer_id_entry.pack(side=tk.LEFT, padx=PADDING_SMALL)

        # ── discount row ──────────────────────────────────────────────────────
        disc_row = tk.Frame(right, bg=COLOR_LIGHT)
        disc_row.pack(fill=tk.X, padx=PADDING_MEDIUM, pady=(0, PADDING_SMALL))
        tk.Label(disc_row, text="Discount (Ksh):", font=FONT_NORMAL,
                 bg=COLOR_LIGHT).pack(side=tk.LEFT)
        self.discount_var = tk.StringVar(value="0")
        disc_entry = tk.Entry(disc_row, textvariable=self.discount_var, width=10)
        disc_entry.pack(side=tk.LEFT, padx=PADDING_SMALL)
        self.discount_var.trace("w", self._refresh_totals)

        # ── totals summary ────────────────────────────────────────────────────
        totals_frame = tk.Frame(right, bg=COLOR_LIGHT)
        totals_frame.pack(fill=tk.X, padx=PADDING_MEDIUM)
        totals_frame.columnconfigure(1, weight=1)

        def total_lbl(row, label, attr, fg=COLOR_DARK, bold=False):
            font = FONT_HEADING if bold else FONT_NORMAL
            tk.Label(totals_frame, text=label, font=font, bg=COLOR_LIGHT,
                     fg=fg, anchor="w").grid(row=row, column=0, sticky="w", pady=1)
            var = tk.Label(totals_frame, text=format_currency(0), font=font,
                           bg=COLOR_LIGHT, fg=fg, anchor="e")
            var.grid(row=row, column=1, sticky="e", pady=1)
            setattr(self, attr, var)

        total_lbl(0, "Subtotal:", "subtotal_label", fg=COLOR_DARK)
        total_lbl(1, "Discount:", "discount_label", fg=COLOR_WARNING)
        total_lbl(2, f"Tax ({TAX_RATE * 100:.0f}%):", "tax_label", fg=COLOR_WARNING)
        total_lbl(3, "TOTAL:", "total_label", fg=COLOR_DANGER, bold=True)

        ttk.Separator(right, orient="horizontal").pack(fill=tk.X, padx=PADDING_MEDIUM,
                                                       pady=PADDING_SMALL)

        # ── payment method ────────────────────────────────────────────────────
        pay_frame = tk.LabelFrame(right, text="Payment Method", font=FONT_NORMAL,
                                  bg=COLOR_LIGHT, fg=COLOR_DARK)
        pay_frame.pack(fill=tk.X, padx=PADDING_MEDIUM, pady=(0, PADDING_SMALL))

        self.payment_var = tk.StringVar(value="cash")
        for value, label in (("cash", "Cash"), ("card", "Card"),
                              ("mobile", "Mobile Money")):
            tk.Radiobutton(pay_frame, text=label, variable=self.payment_var,
                           value=value, bg=COLOR_LIGHT).pack(side=tk.LEFT,
                                                             padx=PADDING_SMALL)

        # ── cash tendered (shown when cash selected) ──────────────────────────
        self.cash_frame = tk.Frame(right, bg=COLOR_LIGHT)
        self.cash_frame.pack(fill=tk.X, padx=PADDING_MEDIUM,
                             pady=(0, PADDING_SMALL))
        tk.Label(self.cash_frame, text="Amount Tendered:", font=FONT_NORMAL,
                 bg=COLOR_LIGHT).pack(side=tk.LEFT)
        self.tendered_var = tk.StringVar(value="")
        self.tendered_entry = tk.Entry(self.cash_frame,
                                       textvariable=self.tendered_var, width=10)
        self.tendered_entry.pack(side=tk.LEFT, padx=PADDING_SMALL)
        self.change_label = tk.Label(self.cash_frame, text="Change: —",
                                     font=FONT_NORMAL, bg=COLOR_LIGHT,
                                     fg=COLOR_SUCCESS)
        self.change_label.pack(side=tk.LEFT, padx=PADDING_SMALL)
        self.tendered_var.trace("w", self._update_change)
        self.payment_var.trace("w", self._on_payment_change)

        # ── action buttons ────────────────────────────────────────────────────
        action_row = tk.Frame(right, bg=COLOR_LIGHT)
        action_row.pack(fill=tk.X, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)

        tk.Button(action_row, text="✔  Checkout", font=FONT_HEADING,
                  bg=COLOR_SUCCESS, fg=COLOR_WHITE, command=self._checkout,
                  cursor="hand2", padx=10, pady=6).pack(side=tk.LEFT, padx=4)
        tk.Button(action_row, text="✖  Clear Cart", font=FONT_NORMAL,
                  bg=COLOR_WARNING, fg=COLOR_WHITE, command=self._clear_cart,
                  cursor="hand2", padx=10, pady=6).pack(side=tk.LEFT, padx=4)

    # ── product loading & filtering ───────────────────────────────────────────

    def load_products(self):
        """Load products from the backend API."""
        try:
            response = self.api_client.get_products(per_page=100)
            data = response.get("data") or {}
            self.products = data.get("items") or []
            self._display_products(self.products)
        except APIError as e:
            show_error("Error", f"Failed to load products: {e}")

    def _display_products(self, products):
        """Populate the products treeview."""
        for row in self.products_tree.get_children():
            self.products_tree.delete(row)
        for p in products:
            self.products_tree.insert("", tk.END, iid=str(p["id"]), values=(
                p.get("sku", ""),
                p.get("name", ""),
                format_currency(float(p.get("price", 0))),
                p.get("quantity_in_stock", 0),
            ))

    def _filter_products(self, *_args):
        """Filter products treeview by the search field."""
        term = self.search_var.get().lower()
        filtered = [
            p for p in self.products
            if term in p.get("name", "").lower()
            or term in p.get("sku", "").lower()
            or term in p.get("category", "").lower()
        ]
        self._display_products(filtered)

    # ── adding items to cart ──────────────────────────────────────────────────

    def _product_by_id(self, product_id):
        """Return the product dict for *product_id* (int) or None."""
        for p in self.products:
            if p.get("id") == product_id:
                return p
        return None

    def _add_to_cart_from_tree(self, _event=None):
        """Double-click handler: add selected product row to cart."""
        selection = self.products_tree.selection()
        if not selection:
            return
        product_id = int(selection[0])
        product = self._product_by_id(product_id)
        if product:
            self._add_product_to_cart(product)

    def _add_by_sku(self):
        """Add product matching the SKU/barcode entry to cart."""
        sku = self.sku_var.get().strip()
        if not sku:
            return
        match = next(
            (p for p in self.products
             if p.get("sku", "").lower() == sku.lower()),
            None,
        )
        if match is None:
            show_error("Not Found", f"No product found with SKU: {sku}")
            return
        self._add_product_to_cart(match)
        self.sku_var.set("")

    def _add_product_to_cart(self, product):
        """Add *product* to the in-memory cart (or increment qty)."""
        pid = product["id"]
        stock = product.get("quantity_in_stock", 0)
        current_qty = self.cart.get(pid, {}).get("qty", 0)
        if current_qty >= stock:
            show_error("Out of Stock",
                       f"Only {stock} unit(s) of '{product['name']}' available.")
            return
        if pid in self.cart:
            self.cart[pid]["qty"] += 1
        else:
            self.cart[pid] = {"product": product, "qty": 1}
        self._refresh_cart_display()

    # ── cart quantity controls ────────────────────────────────────────────────

    def _selected_cart_pid(self):
        """Return the product_id (int) for the selected cart row, or None."""
        sel = self.cart_tree.selection()
        if not sel:
            return None
        return int(sel[0])

    def _increase_qty(self):
        pid = self._selected_cart_pid()
        if pid is None:
            show_error("No Selection", "Select a cart item first.")
            return
        entry = self.cart.get(pid)
        if not entry:
            return
        stock = entry["product"].get("quantity_in_stock", 0)
        if entry["qty"] >= stock:
            show_error("Stock Limit",
                       f"Maximum available stock ({stock}) already in cart.")
            return
        entry["qty"] += 1
        self._refresh_cart_display()

    def _decrease_qty(self):
        pid = self._selected_cart_pid()
        if pid is None:
            show_error("No Selection", "Select a cart item first.")
            return
        entry = self.cart.get(pid)
        if not entry:
            return
        if entry["qty"] > 1:
            entry["qty"] -= 1
        else:
            del self.cart[pid]
        self._refresh_cart_display()

    def _remove_item(self):
        pid = self._selected_cart_pid()
        if pid is None:
            show_error("No Selection", "Select a cart item first.")
            return
        if show_confirmation("Remove Item",
                             f"Remove '{self.cart[pid]['product']['name']}' from cart?"):
            del self.cart[pid]
            self._refresh_cart_display()

    # ── cart display & totals ─────────────────────────────────────────────────

    def _refresh_cart_display(self):
        """Rebuild the cart treeview and recalculate totals."""
        for row in self.cart_tree.get_children():
            self.cart_tree.delete(row)

        subtotal = 0.0
        for pid, entry in self.cart.items():
            p = entry["product"]
            line = float(p["price"]) * entry["qty"]
            subtotal += line
            self.cart_tree.insert("", tk.END, iid=str(pid), values=(
                p.get("name", ""),
                format_currency(float(p["price"])),
                entry["qty"],
                format_currency(line),
            ))

        self._compute_totals(subtotal)

    def _compute_totals(self, subtotal=None):
        """Recompute subtotal/discount/tax/total from current cart."""
        if subtotal is None:
            subtotal = sum(
                float(e["product"]["price"]) * e["qty"]
                for e in self.cart.values()
            )
        discount = self._get_discount()
        taxable = max(0.0, subtotal - discount)
        tax = taxable * TAX_RATE
        total = taxable + tax

        self.subtotal_label.config(text=format_currency(subtotal))
        self.discount_label.config(text=f"-{format_currency(discount)}" if discount else format_currency(0))
        self.tax_label.config(text=format_currency(tax))
        self.total_label.config(text=format_currency(total))
        self._update_change()

    def _get_discount(self):
        """Return the validated discount amount (float ≥ 0)."""
        try:
            val = float(self.discount_var.get())
            return max(0.0, val)
        except (ValueError, TypeError):
            return 0.0

    def _refresh_totals(self, *_args):
        """Called when discount field changes."""
        self._compute_totals()

    # ── payment helpers ───────────────────────────────────────────────────────

    def _on_payment_change(self, *_args):
        """Clear change display when payment method changes."""
        self._update_change()

    def _update_change(self, *_args):
        """Compute and display change for cash payments."""
        if self.payment_var.get() != "cash":
            self.change_label.config(text="")
            return
        try:
            tendered = float(self.tendered_var.get())
        except (ValueError, TypeError):
            self.change_label.config(text="Change: —")
            return
        subtotal = sum(
            float(e["product"]["price"]) * e["qty"] for e in self.cart.values()
        )
        discount = self._get_discount()
        taxable = max(0.0, subtotal - discount)
        total = taxable + (taxable * TAX_RATE)
        change = tendered - total
        if change >= 0:
            self.change_label.config(
                text=f"Change: {format_currency(change)}", fg=COLOR_SUCCESS)
        else:
            self.change_label.config(
                text=f"Short: {format_currency(-change)}", fg=COLOR_DANGER)

    # ── customer helpers ──────────────────────────────────────────────────────

    def _toggle_customer(self):
        """Enable/disable the customer ID entry."""
        if self.customer_type.get() == "existing":
            self.customer_id_entry.config(state="normal")
        else:
            self.customer_id_var.set("")
            self.customer_id_entry.config(state="disabled")

    def _get_customer_id(self):
        """Return int customer_id or None for walk-in. Raises ValueError on bad input."""
        if self.customer_type.get() == "walkin":
            return None
        raw = self.customer_id_var.get().strip()
        if not raw:
            raise ValueError("Please enter a customer ID or select Walk-in.")
        try:
            cid = int(raw)
            if cid <= 0:
                raise ValueError
            return cid
        except (ValueError, TypeError):
            raise ValueError(f"Invalid customer ID: '{raw}'. Must be a positive integer.")

    # ── checkout ──────────────────────────────────────────────────────────────

    def _checkout(self):
        """Validate cart, call API, show receipt."""
        if not self.cart:
            show_error("Empty Cart", "Please add items to the cart before checkout.")
            return

        # validate discount
        discount = 0.0
        try:
            discount = self._get_discount()
        except Exception:
            show_error("Invalid Discount", "Discount must be a non-negative number.")
            return

        # validate customer id
        try:
            customer_id = self._get_customer_id()
        except ValueError as exc:
            show_error("Customer Error", str(exc))
            return

        payment_method = self.payment_var.get()

        # build items payload
        items = [
            {"product_id": pid, "quantity": entry["qty"]}
            for pid, entry in self.cart.items()
        ]

        # compute totals for receipt
        subtotal = sum(
            float(e["product"]["price"]) * e["qty"] for e in self.cart.values()
        )
        taxable = max(0.0, subtotal - discount)
        tax = taxable * TAX_RATE
        total = taxable + tax

        try:
            response = self.api_client.create_sale(
                items, discount, payment_method, customer_id
            )
            sale_data = response.get("data") or {}
            sale_id = sale_data.get("id", "N/A")
            created_at = sale_data.get("created_at", "")
            try:
                dt = datetime.fromisoformat(created_at)
                receipt_dt = dt.strftime("%d %b %Y  %H:%M")
            except Exception:
                receipt_dt = datetime.now().strftime("%d %b %Y  %H:%M")

            cashier_name = (self.api_client.user_data or {}).get("username", "Cashier")
            customer_label = str(customer_id) if customer_id else None

            receipt_data = {
                "sale_id": sale_id,
                "datetime": receipt_dt,
                "cashier": cashier_name,
                "customer": customer_label,
                "items": [
                    {
                        "name": entry["product"].get("name", ""),
                        "qty": entry["qty"],
                        "unit_price": float(entry["product"]["price"]),
                        "line_total": float(entry["product"]["price"]) * entry["qty"],
                    }
                    for entry in self.cart.values()
                ],
                "subtotal": subtotal,
                "discount": discount,
                "tax": tax,
                "total": total,
                "payment_method": payment_method,
            }

            # clear cart before opening receipt so UI is clean on close
            self.cart = {}
            self._refresh_cart_display()
            self.discount_var.set("0")
            self.customer_type.set("walkin")
            self.customer_id_var.set("")
            self.customer_id_entry.config(state="disabled")
            self.tendered_var.set("")

            ReceiptDialog(self.winfo_toplevel(), receipt_data)

        except APIError as e:
            show_error("Checkout Failed", str(e))

    def _clear_cart(self):
        """Prompt and clear entire cart."""
        if not self.cart:
            return
        if show_confirmation("Clear Cart", "Remove all items from the cart?"):
            self.cart = {}
            self._refresh_cart_display()
            self.discount_var.set("0")
