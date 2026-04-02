#!/usr/bin/env python3
"""
POS System - Desktop GUI Entry Point
"""
import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    import tkinter as tk
    from gui.main import POSApplication
except ImportError as e:
    print(f"Error: Missing required dependency - {e}")
    print("Please install dependencies: pip install -r requirements_gui.txt")
    sys.exit(1)

def main():
    """Main entry point for the POS application"""
    try:
        root = tk.Tk()
        app = POSApplication(root)
        root.mainloop()
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()