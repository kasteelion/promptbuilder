import flet as ft
import inspect
import pprint

try:
    spec = inspect.getfullargspec(ft.Tabs.__init__)
    print("ft.Tabs args:")
    pprint.pprint(spec.args)
    print("ft.Tabs annotations:")
    pprint.pprint(spec.annotations)
except Exception as e:
    print(f"Error: {e}")
