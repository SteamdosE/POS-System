"""
Receipt Display Dialog
"""
import tkinter as tk
from tkinter import ttk
from ..config import *

class ReceiptDialog(tk.Toplevel):
    """Display and manage receipt dialog"""
    
    def __init__(self, parent, receipt_text, receipt_html=None):
        super().__init__(parent)
        self.title("Receipt Preview")
        self.geometry("600x700")
        
        self.receipt_text = receipt_text
        self.receipt_html = receipt_html
        
        self.setup_ui()
        self.display_receipt()
    
    def setup_ui(self):
        """Setup dialog UI"""
        # Toolbar
        toolbar = tk.Frame(self, bg=COLOR_DARK)
        toolbar.pack(fill=tk.X)
        
        print_btn = tk.Button(toolbar, text="🖨️ Print", bg=COLOR_PRIMARY, fg=COLOR_WHITE, command=self.print_receipt, cursor="hand2")
        print_btn.pack(side=tk.LEFT, padx=PADDING_SMALL, pady=PADDING_SMALL)
        
        save_btn = tk.Button(toolbar, text="💾 Save", bg=COLOR_SUCCESS, fg=COLOR_WHITE, command=self.save_receipt, cursor="hand2")
        save_btn.pack(side=tk.LEFT, padx=PADDING_SMALL, pady=PADDING_SMALL)
        
        close_btn = tk.Button(toolbar, text="✕ Close", bg=COLOR_DANGER, fg=COLOR_WHITE, command=self.destroy, cursor="hand2")
        close_btn.pack(side=tk.RIGHT, padx=PADDING_SMALL, pady=PADDING_SMALL)
        
        # Receipt display
        self.receipt_text_widget = tk.Text(self, font=("Courier", 10), bg=COLOR_WHITE)
        self.receipt_text_widget.pack(fill=tk.BOTH, expand=True, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
        self.receipt_text_widget.config(state=tk.DISABLED)
    
    def display_receipt(self):
        """Display receipt in text widget"""
        self.receipt_text_widget.config(state=tk.NORMAL)
        self.receipt_text_widget.delete(1.0, tk.END)
        self.receipt_text_widget.insert(1.0, self.receipt_text)
        self.receipt_text_widget.config(state=tk.DISABLED)
    
    def print_receipt(self):
        """Print receipt (simulated)"""
        # In a real system, this would integrate with printer hardware
        from ..utils.dialogs import show_success
        show_success("Print", "Receipt sent to printer!\n(Note: Hardware integration required)")
    
    def save_receipt(self):
        """Save receipt to file"""
        import os
        from datetime import datetime
        
        # Create receipts directory
        if not os.path.exists("receipts"):
            os.makedirs("receipts")
        
        # Save as text file
        filename = f"receipts/receipt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w') as f:
            f.write(self.receipt_text)
        
        from ..utils.dialogs import show_success
        show_success("Saved", f"Receipt saved to {filename}")
