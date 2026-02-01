import flet as ft
import inspect

try:
    sig = inspect.signature(ft.Icon.__init__)
    print(f"ft.Icon signature: {sig}")
except Exception as e:
    print(f"Error inspecting signature: {e}")

try:
    # Try instantiation
    i = ft.Icon("settings")
    print("ft.Icon('settings') positional works.")
except Exception as e:
    print(f"ft.Icon('settings') failed: {e}")

try:
    i = ft.Icon(name="settings")
    print("ft.Icon(name='settings') works.")
except Exception as e:
    print(f"ft.Icon(name='settings') failed: {e}")
