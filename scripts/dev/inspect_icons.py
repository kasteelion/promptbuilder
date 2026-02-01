import flet as ft
import sys

def inspect_icons():
    print("Inspecting flet.icons...")
    try:
        # Get all attributes
        all_attrs = dir(ft.icons)
        # Filter for public constants (uppercase)
        icons = [a for a in all_attrs if a.isupper()]
        print(f"Found {len(icons)} icon constants.")
        
        # Print a sample
        print("Sample icons:", icons[:20])
        
        # Check specifically for SETTINGS and DASHBOARD
        if "SETTINGS" in icons:
            print(f"SETTINGS exists, value: {ft.icons.SETTINGS}")
        else:
            print("SETTINGS NOT COMPATIBLE")
            
        if "DASHBOARD" in icons:
            print(f"DASHBOARD exists, value: {ft.icons.DASHBOARD}")
        else:
            print("DASHBOARD NOT COMPATIBLE")

    except Exception as e:
        print(f"Error inspecting icons: {e}")

if __name__ == "__main__":
    inspect_icons()
