"""
Login Screen for POS System
"""
import tkinter as tk
from tkinter import ttk
from .config import *
from .utils.validators import validate_username, validate_password
from .utils.dialogs import show_error, show_success
from .utils.api_client import APIClient, APIError

class LoginScreen(tk.Frame):
    """Login interface for POS System"""
    
    def __init__(self, parent, on_login_success=None):
        super().__init__(parent, bg=COLOR_WHITE)
        self.parent = parent
        self.on_login_success = on_login_success
        self.api_client = APIClient()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup login UI"""
        main_frame = tk.Frame(self, bg=COLOR_WHITE)
        main_frame.pack(expand=True, fill=tk.BOTH)
        
        title_frame = tk.Frame(main_frame, bg=COLOR_PRIMARY, height=100)
        title_frame.pack(fill=tk.X)
        
        title_label = tk.Label(
            title_frame,
            text="POS System",
            font=FONT_TITLE,
            bg=COLOR_PRIMARY,
            fg=COLOR_WHITE
        )
        title_label.pack(pady=20)
        
        form_frame = tk.Frame(main_frame, bg=COLOR_WHITE)
        form_frame.pack(expand=True, padx=PADDING_XL, pady=PADDING_XL)
        
        tk.Label(form_frame, text="Username:", font=FONT_NORMAL, bg=COLOR_WHITE).grid(row=0, column=0, sticky=tk.W, pady=PADDING_MEDIUM)
        self.username_entry = tk.Entry(form_frame, font=FONT_NORMAL, width=30)
        self.username_entry.grid(row=0, column=1, pady=PADDING_MEDIUM, padx=PADDING_MEDIUM)
        
        tk.Label(form_frame, text="Password:", font=FONT_NORMAL, bg=COLOR_WHITE).grid(row=1, column=0, sticky=tk.W, pady=PADDING_MEDIUM)
        self.password_entry = tk.Entry(form_frame, font=FONT_NORMAL, width=30, show="*")
        self.password_entry.grid(row=1, column=1, pady=PADDING_MEDIUM, padx=PADDING_MEDIUM)
        
        self.error_label = tk.Label(form_frame, text="", font=FONT_SMALL, fg=COLOR_DANGER, bg=COLOR_WHITE)
        self.error_label.grid(row=2, column=0, columnspan=2, pady=PADDING_MEDIUM)
        
        button_frame = tk.Frame(form_frame, bg=COLOR_WHITE)
        button_frame.grid(row=3, column=0, columnspan=2, pady=PADDING_XL)
        
        login_btn = tk.Button(
            button_frame,
            text="Login",
            font=FONT_NORMAL,
            bg=COLOR_PRIMARY,
            fg=COLOR_WHITE,
            padx=PADDING_XL,
            pady=PADDING_MEDIUM,
            command=self.login,
            cursor="hand2"
        )
        login_btn.pack(side=tk.LEFT, padx=PADDING_MEDIUM)
        
        clear_btn = tk.Button(
            button_frame,
            text="Clear",
            font=FONT_NORMAL,
            bg=COLOR_LIGHT,
            fg=COLOR_DARK,
            padx=PADDING_XL,
            pady=PADDING_MEDIUM,
            command=self.clear_inputs,
            cursor="hand2"
        )
        clear_btn.pack(side=tk.LEFT, padx=PADDING_MEDIUM)
        
        self.password_entry.bind("<Return>", lambda e: self.login())
        self.username_entry.focus()
    
    def clear_inputs(self):
        """Clear input fields"""
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        self.error_label.config(text="")
        self.username_entry.focus()
    
    def login(self):
        """Handle login"""
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        is_valid, error = validate_username(username)
        if not is_valid:
            self.error_label.config(text=error)
            return
        
        is_valid, error = validate_password(password)
        if not is_valid:
            self.error_label.config(text=error)
            return
        
        try:
            response = self.api_client.login(username, password)
            show_success("Success", MSG_LOGIN_SUCCESS)
            self.clear_inputs()
            
            if self.on_login_success:
                self.on_login_success(self.api_client)
        
        except APIError as e:
            self.error_label.config(text=str(e))
        except Exception as e:
            self.error_label.config(text="Login failed: " + str(e))
