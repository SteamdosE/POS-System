"""
Dialog Helper Functions for POS System GUI
"""
from tkinter import messagebox, simpledialog
from typing import Optional

def show_error(title: str, message: str) -> None:
    """Show error dialog"""
    messagebox.showerror(title, message)

def show_success(title: str, message: str) -> None:
    """Show success dialog"""
    messagebox.showinfo(title, message)

def show_info(title: str, message: str) -> None:
    """Show info dialog"""
    messagebox.showinfo(title, message)

def show_warning(title: str, message: str) -> None:
    """Show warning dialog"""
    messagebox.showwarning(title, message)

def show_confirmation(title: str, message: str) -> bool:
    """Show confirmation dialog, return True if confirmed"""
    return messagebox.askyesno(title, message)

def show_input_dialog(title: str, label: str, parent=None) -> Optional[str]:
    """Show input dialog, return user input or None"""
    return simpledialog.askstring(title, label, parent=parent)

def show_float_input_dialog(title: str, label: str, parent=None) -> Optional[float]:
    """Show input dialog for float value"""
    result = simpledialog.askfloat(title, label, parent=parent)
    return result

def show_int_input_dialog(title: str, label: str, parent=None) -> Optional[int]:
    """Show input dialog for integer value"""
    result = simpledialog.askinteger(title, label, parent=parent)
    return result