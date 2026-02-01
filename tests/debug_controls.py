import sys
import os
import traceback

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import flet as ft
    
    print("Testing Chip...")
    try:
        c = ft.Chip(label=ft.Text("Test"))
        print("Chip OK.")
    except AttributeError:
        print("Chip MISSING.")
    except Exception as e:
        print(f"Chip Error: {e}")

except Exception:
    traceback.print_exc()
