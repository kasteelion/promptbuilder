import flet as ft
import inspect

def main(page: ft.Page):
    print("Inspecting IconButton...")
    try:
        sig = inspect.signature(ft.IconButton.__init__)
        print(f"Signature: {sig}")
    except Exception as e:
        print(f"Sig check failed: {e}")

    print("Testing Container Fallback...")
    try:
        btn = ft.Container(
            content=ft.Icon("settings", color="white"),
            on_click=lambda e: print("Click"),
            padding=10,
            border_radius=50
        )
        page.add(btn)
        print("Container fallback added successfully.")
    except Exception as e:
        print(f"Container fallback failed: {e}")

if __name__ == "__main__":
    ft.app(target=main)
