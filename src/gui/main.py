"""
Main POS Application Controller
"""
import tkinter as tk
from .login import LoginScreen
from .cashier import CashierScreen
from .admin_dashboard import AdminDashboard
from .manager_dashboard import ManagerDashboard
from .customer_management import CustomerManagement
from .config import *

class POSApplication:
    """Main POS Application"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("POS System")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.api_client = None
        self.current_frame = None
        self.current_screen = None
        
        self.show_login()
    
    def show_login(self):
        """Show login screen"""
        self.clear_frame()
        self.current_frame = LoginScreen(self.root, self.on_login_success)
        self.current_frame.pack(fill=tk.BOTH, expand=True)
    
    def on_login_success(self, api_client):
        """Handle successful login"""
        self.api_client = api_client
        user_role = api_client.user_data.get("role", "cashier")
        
        if user_role == "admin":
            self.show_admin_dashboard()
        elif user_role == "manager":
            self.show_manager_dashboard()
        else:
            self.show_cashier()
    
    def show_cashier(self):
        """Show cashier screen"""
        self.clear_frame()
        self.current_frame = tk.Frame(self.root, bg=COLOR_LIGHT)
        self.current_frame.pack(fill=tk.BOTH, expand=True)
        
        # Toolbar
        toolbar = tk.Frame(self.current_frame, bg=COLOR_DARK)
        toolbar.pack(fill=tk.X)
        
        logout_btn = tk.Button(toolbar, text="Logout", bg=COLOR_DANGER, fg=COLOR_WHITE, command=self.logout, cursor="hand2")
        logout_btn.pack(side=tk.RIGHT, padx=PADDING_MEDIUM, pady=PADDING_SMALL)
        
        # Cashier screen
        self.current_screen = CashierScreen(self.current_frame, self.api_client)
        self.current_screen.pack(fill=tk.BOTH, expand=True)
    
    def show_admin_dashboard(self):
        """Show admin dashboard"""
        self.clear_frame()
        self.current_frame = tk.Frame(self.root, bg=COLOR_LIGHT)
        self.current_frame.pack(fill=tk.BOTH, expand=True)
        
        # Toolbar
        toolbar = tk.Frame(self.current_frame, bg=COLOR_DARK)
        toolbar.pack(fill=tk.X)
        
        logout_btn = tk.Button(toolbar, text="Logout", bg=COLOR_DANGER, fg=COLOR_WHITE, command=self.logout, cursor="hand2")
        logout_btn.pack(side=tk.RIGHT, padx=PADDING_MEDIUM, pady=PADDING_SMALL)
        
        # Admin dashboard
        self.current_screen = AdminDashboard(self.current_frame, self.api_client)
        self.current_screen.pack(fill=tk.BOTH, expand=True)
    
    def show_manager_dashboard(self):
        """Show manager dashboard"""
        self.clear_frame()
        self.current_frame = tk.Frame(self.root, bg=COLOR_LIGHT)
        self.current_frame.pack(fill=tk.BOTH, expand=True)
        
        # Toolbar
        toolbar = tk.Frame(self.current_frame, bg=COLOR_DARK)
        toolbar.pack(fill=tk.X)
        
        logout_btn = tk.Button(toolbar, text="Logout", bg=COLOR_DANGER, fg=COLOR_WHITE, command=self.logout, cursor="hand2")
        logout_btn.pack(side=tk.RIGHT, padx=PADDING_MEDIUM, pady=PADDING_SMALL)
        
        # Manager dashboard
        self.current_screen = ManagerDashboard(self.current_frame, self.api_client)
        self.current_screen.pack(fill=tk.BOTH, expand=True)
    
    def logout(self):
        """Logout user"""
        self.api_client = None
        self.show_login()
    
    def clear_frame(self):
        """Clear current frame"""
        if self.current_frame:
            self.current_frame.pack_forget()
            self.current_frame.destroy()
            self.current_frame = None


def main():
    """Main entry point for the POS application"""
    root = tk.Tk()
    app = POSApplication(root)
    root.mainloop()


if __name__ == "__main__":
    main()
