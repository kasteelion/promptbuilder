import os
import sys
import tkinter as tk
from tkinter import ttk

# Add project root to path
sys.path.append(os.getcwd())

from ui.themes.theme_manager import ThemeManager

def check_theme():
    root = tk.Tk()
    tm = ThemeManager(root, None)
    
    # Force load 'ONU Dark'
    if "ONU Dark" not in tm.themes:
        print("ERROR: 'ONU Dark' theme NOT found in ThemeManager!")
    else:
        theme = tm.themes["ONU Dark"]
        print(f"Theme: ONU Dark")
        print(f"bg: {theme.get('bg')}")
        print(f"panel_bg: {theme.get('panel_bg')}")
        print(f"text_bg: {theme.get('text_bg')}")
        print(f"TFrame matches panel_bg? {theme.get('panel_bg') == '#1a1a1a'}")

    root.destroy()

if __name__ == "__main__":
    check_theme()
