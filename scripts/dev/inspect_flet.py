import flet as ft
import inspect

with open("flet_inspection.txt", "w") as f:
    f.write(f"Flet Version: {ft.version}\n")
    f.write("-" * 20 + "\n")
    f.write("dir(ft.Dropdown):\n")
    f.write("\n".join(dir(ft.Dropdown)))
    f.write("\n" + "-" * 20 + "\n")
    f.write("inspect.signature(ft.Dropdown.__init__):\n")
    try:
        f.write(str(inspect.signature(ft.Dropdown.__init__)))
    except Exception as e:
        f.write(f"Error inspecting signature: {e}")
