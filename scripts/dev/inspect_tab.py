import flet as ft
import inspect

try:
    spec = inspect.getfullargspec(ft.Tabs.__init__)
    print(f"ft.Tabs args: {spec.args}")
except Exception as e:
    print(f"Error: {e}")
