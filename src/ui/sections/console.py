import flet as ft
from core.flet_theme_manager import ThemeManager

class ConsoleSection(ft.Column):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.spacing = 0
        
        self.output_field = ft.TextField(
            multiline=True, read_only=True, min_lines=8, max_lines=15, text_size=13, 
            border_color=ThemeManager.colors["accent"], bgcolor=ThemeManager.colors["surface"],
            expand=True
        )
        
        self.console_header = ft.Container(
             content=ft.Row([
                ft.Text("FINAL AI PROMPT", weight="bold", size=18, color=ThemeManager.colors["text_primary"]),
                ft.Row([
                    ft.FilledButton(
                        "Copy Prompt", icon=ft.Icons.COPY, on_click=lambda e: self.app.handle_copy(e), 
                        style=ft.ButtonStyle(color=ThemeManager.colors["text_primary"], bgcolor="white10")
                    ),
                    ft.FilledButton(
                        "Generate Image", icon=ft.Icons.AUTO_AWESOME, on_click=lambda _: self.app.handle_generate(), 
                        style=ft.ButtonStyle(color=ThemeManager.colors["text_primary"], bgcolor=ThemeManager.colors["accent"])
                    ),
                ], spacing=10)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.Padding(15, 10, 15, 10),
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, 0),
                end=ft.Alignment(1, 0),
                colors=[ThemeManager.colors["panel_bg"], ThemeManager.colors["active_item"]]
            ),
            border_radius=ft.BorderRadius.only(top_left=10, top_right=10)
        )
        
        self.controls = [
            self.console_header,
            ft.Container(
                content=self.output_field,
                border=ft.Border.all(1, ThemeManager.colors["outline"]),
                border_radius=ft.BorderRadius.only(bottom_left=10, bottom_right=10),
                padding=0
            )
        ]

    def update_output(self, text: str):
        self.output_field.value = text
        self.output_field.update()

    def refresh_theme(self, update_ui=True):
        self.output_field.border_color = ThemeManager.colors["accent"]
        self.output_field.bgcolor = ThemeManager.colors["surface"]
        self.console_header.gradient.colors = [ThemeManager.colors["panel_bg"], ThemeManager.colors["active_item"]]
        self.controls[1].border = ft.Border.all(1, ThemeManager.colors["outline"])
        if update_ui:
            self.update()
