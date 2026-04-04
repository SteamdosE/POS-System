"""Login Screen for POS System."""

import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageDraw, ImageTk

from .config import *
from .utils.validators import validate_email, validate_username, validate_password
from .utils.dialogs import show_error
from .utils.api_client import APIClient, APIError

class LoginScreen(tk.Frame):
    """Login interface for POS System"""
    
    def __init__(self, parent, on_login_success=None):
        super().__init__(parent, bg=COLOR_WHITE)
        self.parent = parent
        self.on_login_success = on_login_success
        self.api_client = APIClient()
        self.password_visible = False
        self.forgot_password_visible = False
        self.bg_image = None
        self.bg_canvas_image = None
        self.eye_open_icon = None
        self.eye_closed_icon = None
        self.is_loading_transition = False
        self.setup_ui()
    
    def setup_ui(self):
        """Setup login UI"""
        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0)
        self.canvas.pack(expand=True, fill=tk.BOTH)
        self.canvas.bind("<Configure>", self._on_resize)

        self.card = tk.Frame(self.canvas, bg=COLOR_WHITE)
        self.card_window = self.canvas.create_window(0, 0, window=self.card, anchor="center")

        header = tk.Frame(self.card, bg=COLOR_PRIMARY, height=95)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header,
            text="POS System",
            font=FONT_TITLE,
            bg=COLOR_PRIMARY,
            fg=COLOR_WHITE,
        ).pack(pady=(18, 4))
        tk.Label(
            header,
            text="Sign in to continue",
            font=FONT_SMALL,
            bg=COLOR_PRIMARY,
            fg=COLOR_WHITE,
        ).pack()

        self.page_container = tk.Frame(self.card, bg=COLOR_WHITE)
        self.page_container.pack(fill=tk.BOTH, expand=True, padx=28, pady=22)

        self.login_page = tk.Frame(self.page_container, bg=COLOR_WHITE)
        self.forgot_page = tk.Frame(self.page_container, bg=COLOR_WHITE)
        self.login_page.grid(row=0, column=0, sticky="nsew")
        self.forgot_page.grid(row=0, column=0, sticky="nsew")
        self.page_container.rowconfigure(0, weight=1)
        self.page_container.columnconfigure(0, weight=1)

        tk.Label(self.login_page, text="Username", font=FONT_NORMAL, bg=COLOR_WHITE, fg=COLOR_DARK).grid(
            row=0, column=0, sticky=tk.W, pady=(0, 6)
        )
        self.username_entry = tk.Entry(self.login_page, font=FONT_NORMAL, relief=tk.FLAT, bd=0)
        self.username_entry.grid(row=1, column=0, sticky="ew", ipady=8, pady=(0, PADDING_MEDIUM))

        tk.Label(self.login_page, text="Password", font=FONT_NORMAL, bg=COLOR_WHITE, fg=COLOR_DARK).grid(
            row=2, column=0, sticky=tk.W, pady=(0, 6)
        )
        self.password_container = tk.Frame(
            self.login_page,
            bg=COLOR_WHITE,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
            highlightcolor=COLOR_BORDER,
        )
        self.password_container.grid(row=3, column=0, sticky="ew", pady=(0, PADDING_MEDIUM))

        self.password_entry = tk.Entry(self.password_container, font=FONT_NORMAL, relief=tk.FLAT, bd=0, show="*")
        self.password_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipady=8, padx=(0, 2))

        self.eye_open_icon, self.eye_closed_icon = self._build_eye_icons()
        self.toggle_password_btn = tk.Button(
            self.password_container,
            image=self.eye_open_icon,
            text="",
            bg=COLOR_WHITE,
            activebackground=COLOR_LIGHT,
            relief=tk.FLAT,
            bd=0,
            width=26,
            cursor="hand2",
            command=self.toggle_password_visibility,
        )
        self.toggle_password_btn.pack(side=tk.RIGHT, padx=4, pady=4)

        self.error_label = tk.Label(self.login_page, text="", font=FONT_SMALL, fg=COLOR_DANGER, bg=COLOR_WHITE)
        self.error_label.grid(row=4, column=0, sticky=tk.W, pady=(0, 10))

        self.login_btn = tk.Button(
            self.login_page,
            text="Login",
            font=FONT_NORMAL,
            bg=COLOR_PRIMARY,
            fg=COLOR_WHITE,
            activebackground="#1F6B8C",
            activeforeground=COLOR_WHITE,
            padx=24,
            pady=10,
            relief=tk.FLAT,
            bd=0,
            command=self.login,
            cursor="hand2",
        )
        self.login_btn.grid(row=5, column=0, pady=(6, 8), ipadx=6)

        self.clear_btn = tk.Button(
            self.login_page,
            text="Clear",
            font=FONT_SMALL,
            bg=COLOR_LIGHT,
            fg=COLOR_DARK,
            activebackground=COLOR_BORDER,
            activeforeground=COLOR_DARK,
            padx=14,
            pady=7,
            relief=tk.FLAT,
            bd=0,
            command=self.clear_inputs,
            cursor="hand2",
        )
        self.clear_btn.grid(row=6, column=0, pady=(0, 12))

        self.forgot_toggle_label = tk.Label(
            self.login_page,
            text="Forgot password?",
            font=(FONT_SMALL[0], FONT_SMALL[1], "underline"),
            bg=COLOR_WHITE,
            fg=COLOR_PRIMARY,
            cursor="hand2",
        )
        self.forgot_toggle_label.grid(row=7, column=0, sticky=tk.W)
        self.forgot_toggle_label.bind("<Button-1>", lambda _event: self.show_forgot_page())

        self.loading_frame = tk.Frame(self.login_page, bg=COLOR_WHITE)
        self.loading_label = tk.Label(
            self.loading_frame,
            text="Login successful. Loading dashboard...",
            font=FONT_SMALL,
            bg=COLOR_WHITE,
            fg=COLOR_PRIMARY,
        )
        self.loading_label.pack(side=tk.LEFT)
        self.loading_bar = ttk.Progressbar(self.loading_frame, mode="indeterminate", length=110)
        self.loading_bar.pack(side=tk.LEFT, padx=(10, 0))

        tk.Label(self.forgot_page, text="Forgot Password", font=FONT_HEADING, bg=COLOR_WHITE, fg=COLOR_DARK).grid(
            row=0, column=0, sticky=tk.W, pady=(0, 8)
        )
        tk.Label(
            self.forgot_page,
            text="Verify your account and set a new password.",
            font=FONT_SMALL,
            bg=COLOR_WHITE,
            fg=COLOR_DARK,
        ).grid(row=1, column=0, sticky=tk.W, pady=(0, 12))

        tk.Label(self.forgot_page, text="Username", bg=COLOR_WHITE, fg=COLOR_DARK, font=FONT_SMALL).grid(
            row=2, column=0, sticky=tk.W
        )
        self.forgot_username_entry = tk.Entry(self.forgot_page, font=FONT_NORMAL, relief=tk.FLAT, bd=0)
        self.forgot_username_entry.grid(row=3, column=0, sticky="ew", ipady=7, pady=(2, 10))

        tk.Label(self.forgot_page, text="Email", bg=COLOR_WHITE, fg=COLOR_DARK, font=FONT_SMALL).grid(
            row=4, column=0, sticky=tk.W
        )
        self.forgot_email_entry = tk.Entry(self.forgot_page, font=FONT_NORMAL, relief=tk.FLAT, bd=0)
        self.forgot_email_entry.grid(row=5, column=0, sticky="ew", ipady=7, pady=(2, 10))

        tk.Label(self.forgot_page, text="New Password", bg=COLOR_WHITE, fg=COLOR_DARK, font=FONT_SMALL).grid(
            row=6, column=0, sticky=tk.W
        )
        self.forgot_new_password_entry = tk.Entry(self.forgot_page, font=FONT_NORMAL, relief=tk.FLAT, bd=0, show="*")
        self.forgot_new_password_entry.grid(row=7, column=0, sticky="ew", ipady=7, pady=(2, 10))

        self.forgot_feedback_label = tk.Label(self.forgot_page, text="", font=FONT_SMALL, bg=COLOR_WHITE, fg=COLOR_DANGER)
        self.forgot_feedback_label.grid(row=8, column=0, sticky=tk.W, pady=(0, 8))

        forgot_button_row = tk.Frame(self.forgot_page, bg=COLOR_WHITE)
        forgot_button_row.grid(row=9, column=0, sticky=tk.W)

        self.forgot_submit_btn = tk.Button(
            forgot_button_row,
            text="Reset",
            font=FONT_SMALL,
            bg=COLOR_PRIMARY,
            fg=COLOR_WHITE,
            activebackground="#1F6B8C",
            activeforeground=COLOR_WHITE,
            relief=tk.FLAT,
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
            command=self.submit_forgot_password,
        )
        self.forgot_submit_btn.pack(side=tk.LEFT)

        self.forgot_cancel_btn = tk.Button(
            forgot_button_row,
            text="Back to Login",
            font=FONT_SMALL,
            bg=COLOR_BORDER,
            fg=COLOR_DARK,
            activebackground="#BDBDBD",
            activeforeground=COLOR_DARK,
            relief=tk.FLAT,
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.show_login_page,
        )
        self.forgot_cancel_btn.pack(side=tk.LEFT, padx=(8, 0))

        self.login_page.columnconfigure(0, weight=1)
        self.forgot_page.columnconfigure(0, weight=1)

        self._set_focus_effect(self.username_entry)
        self._set_focus_effect(self.password_entry, container=self.password_container)
        self._set_focus_effect(self.forgot_username_entry)
        self._set_focus_effect(self.forgot_email_entry)
        self._set_focus_effect(self.forgot_new_password_entry)
        self._set_hover_effect(self.login_btn, COLOR_PRIMARY, "#1F6B8C")
        self._set_hover_effect(self.clear_btn, COLOR_LIGHT, COLOR_BORDER)
        self._set_hover_effect(self.forgot_submit_btn, COLOR_PRIMARY, "#1F6B8C")
        self._set_hover_effect(self.forgot_cancel_btn, COLOR_BORDER, "#BDBDBD")

        self.username_entry.bind("<Return>", lambda _event: self.password_entry.focus())
        self.password_entry.bind("<Return>", lambda _event: self.login())
        self.forgot_new_password_entry.bind("<Return>", lambda _event: self.submit_forgot_password())
        self.show_login_page()
        self.username_entry.focus()

    def _show_loading_indicator(self):
        """Show loading state after successful authentication."""
        self.is_loading_transition = True
        self.error_label.config(text="")
        self.login_btn.config(state=tk.DISABLED, text="Loading...")
        self.clear_btn.config(state=tk.DISABLED)
        self.loading_frame.grid(row=9, column=0, sticky=tk.W, pady=(10, 0))
        self.loading_bar.start(10)

    def _hide_loading_indicator(self):
        """Reset loading state if staying on login screen."""
        self.is_loading_transition = False
        self.loading_bar.stop()
        self.loading_frame.grid_forget()
        if self.login_btn.winfo_exists():
            self.login_btn.config(state=tk.NORMAL, text="Login")
        if self.clear_btn.winfo_exists():
            self.clear_btn.config(state=tk.NORMAL)

    def _build_eye_icons(self):
        """Create icon-only eye images for password toggle."""
        size = 14
        open_img = Image.new("RGBA", (size, size), (255, 255, 255, 0))
        open_draw = ImageDraw.Draw(open_img)
        open_draw.ellipse((1, 3, size - 2, size - 4), outline=(72, 72, 72, 255), width=1)
        open_draw.ellipse((5, 5, size - 6, size - 6), fill=(72, 72, 72, 255))

        closed_img = Image.new("RGBA", (size, size), (255, 255, 255, 0))
        closed_draw = ImageDraw.Draw(closed_img)
        closed_draw.ellipse((1, 3, size - 2, size - 4), outline=(72, 72, 72, 255), width=1)
        closed_draw.line((2, size - 3, size - 2, 2), fill=(72, 72, 72, 255), width=1)

        return ImageTk.PhotoImage(open_img), ImageTk.PhotoImage(closed_img)

    def _set_focus_effect(self, entry_widget: tk.Entry, container: tk.Widget = None):
        """Apply focus border effect to entries."""
        target = container or entry_widget

        def on_focus_in(_event):
            target.configure(highlightthickness=2, highlightbackground=COLOR_PRIMARY, highlightcolor=COLOR_PRIMARY)

        def on_focus_out(_event):
            target.configure(highlightthickness=1, highlightbackground=COLOR_BORDER, highlightcolor=COLOR_BORDER)

        target.configure(highlightthickness=1, highlightbackground=COLOR_BORDER, highlightcolor=COLOR_BORDER)
        entry_widget.bind("<FocusIn>", on_focus_in)
        entry_widget.bind("<FocusOut>", on_focus_out)

    def _set_hover_effect(self, widget: tk.Widget, base_color: str, hover_color: str):
        """Apply hover background transitions for controls."""
        widget.bind("<Enter>", lambda _event: widget.configure(bg=hover_color))
        widget.bind("<Leave>", lambda _event: widget.configure(bg=base_color))

    def _build_background(self, width: int, height: int):
        """Build background image used for auth page."""
        width = max(900, width)
        height = max(620, height)
        image = Image.new("RGB", (width, height), "#112437")
        draw = ImageDraw.Draw(image)

        for y in range(height):
            ratio = y / max(1, height - 1)
            red = int(17 + (48 - 17) * ratio)
            green = int(36 + (103 - 36) * ratio)
            blue = int(55 + (154 - 55) * ratio)
            draw.line([(0, y), (width, y)], fill=(red, green, blue))

        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        orb = max(170, width // 6)
        overlay_draw.ellipse([(width - orb - 40, 36), (width - 40, 36 + orb)], fill=(255, 255, 255, 38))
        overlay_draw.ellipse([(50, height - orb - 60), (50 + orb, height - 60)], fill=(255, 255, 255, 24))

        return ImageTk.PhotoImage(Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB"))

    def _on_resize(self, event):
        """Keep background and auth card responsive."""
        self.bg_image = self._build_background(event.width, event.height)
        if self.bg_canvas_image is None:
            self.bg_canvas_image = self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")
            self.canvas.tag_lower(self.bg_canvas_image)
        else:
            self.canvas.itemconfigure(self.bg_canvas_image, image=self.bg_image)
        self.canvas.coords(self.bg_canvas_image, 0, 0)

        card_width = min(600, max(470, int(event.width * 0.48)))
        self.card.configure(width=card_width)
        self.canvas.coords(self.card_window, event.width // 2, event.height // 2)
    
    def clear_inputs(self):
        """Clear input fields"""
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        self.error_label.config(text="")
        self.password_visible = False
        self.password_entry.config(show="*")
        self.toggle_password_btn.config(image=self.eye_open_icon)
        self.username_entry.focus()

    def toggle_password_visibility(self):
        """Toggle password visibility with icon-only control."""
        self.password_visible = not self.password_visible
        self.password_entry.config(show="" if self.password_visible else "*")
        self.toggle_password_btn.config(image=self.eye_closed_icon if self.password_visible else self.eye_open_icon)

    def show_forgot_page(self):
        """Navigate from login page to forgot-password page."""
        self.forgot_password_visible = True
        self.error_label.config(text="")
        self.forgot_feedback_label.config(text="", fg=COLOR_DANGER)
        self.forgot_page.tkraise()
        self.forgot_username_entry.focus()

    def show_login_page(self):
        """Navigate back to login page from forgot-password page."""
        self.forgot_password_visible = False
        self.forgot_feedback_label.config(text="", fg=COLOR_DANGER)
        self.login_page.tkraise()
        self.username_entry.focus()

    def submit_forgot_password(self):
        """Submit inline forgot-password request."""
        username = self.forgot_username_entry.get().strip()
        email = self.forgot_email_entry.get().strip()
        new_password = self.forgot_new_password_entry.get()

        is_valid, error = validate_username(username)
        if not is_valid:
            self.forgot_feedback_label.config(text=error, fg=COLOR_DANGER)
            return

        is_valid, error = validate_email(email)
        if not is_valid:
            self.forgot_feedback_label.config(text=error, fg=COLOR_DANGER)
            return

        is_valid, error = validate_password(new_password)
        if not is_valid:
            self.forgot_feedback_label.config(text=error, fg=COLOR_DANGER)
            return

        try:
            self.forgot_submit_btn.config(state=tk.DISABLED, text="Resetting...")
            self.update_idletasks()
            self.api_client.forgot_password(username, email, new_password)

            self.forgot_feedback_label.config(
                text="Password reset successful. Use your new password to sign in.",
                fg=COLOR_SUCCESS,
            )
            self.password_entry.delete(0, tk.END)
            self.password_entry.insert(0, new_password)
            self.username_entry.delete(0, tk.END)
            self.username_entry.insert(0, username)

            self.after(1200, self.show_login_page)
        except APIError as error:
            self.forgot_feedback_label.config(text=str(error), fg=COLOR_DANGER)
        except Exception as error:
            self.forgot_feedback_label.config(text=f"Reset failed: {error}", fg=COLOR_DANGER)
        finally:
            self.forgot_submit_btn.config(state=tk.NORMAL, text="Reset")
    
    def login(self):
        """Handle login"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        self.error_label.config(text="")
        self._hide_loading_indicator()
        
        is_valid, error = validate_username(username)
        if not is_valid:
            self.error_label.config(text=error)
            return
        
        is_valid, error = validate_password(password)
        if not is_valid:
            self.error_label.config(text=error)
            return
        
        try:
            self.login_btn.config(state=tk.DISABLED, text="Signing in...")
            self.update_idletasks()

            self.api_client.login(username, password)
            self._show_loading_indicator()
            
            if self.on_login_success:
                self.after(600, lambda: self.on_login_success(self.api_client))
            else:
                self.after(1500, self._hide_loading_indicator)
        
        except APIError as e:
            self.error_label.config(text=str(e))
        except Exception as e:
            if self.error_label.winfo_exists():
                self.error_label.config(text="Login failed: " + str(e))
            else:
                show_error("Error", "Login failed: " + str(e))
        finally:
            if self.login_btn.winfo_exists() and not self.is_loading_transition:
                self.login_btn.config(state=tk.NORMAL, text="Login")
