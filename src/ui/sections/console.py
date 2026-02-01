import flet as ft

class ConsoleSection(ft.Column):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.spacing = 0
        
        self.output_field = ft.TextField(
            multiline=True, read_only=True, min_lines=8, max_lines=15, text_size=13, 
            border_color=ft.Colors.BLUE_ACCENT, bgcolor=ft.Colors.BLACK12,
            expand=True
        )
        
        self.console_header = ft.Container(
             content=ft.Row([
                ft.Text("FINAL AI PROMPT", weight="bold", size=18, color=ft.Colors.WHITE),
                ft.Row([
                    ft.FilledButton(
                        content="Copy Prompt", icon=ft.Icons.COPY, on_click=lambda e: self.app.handle_copy(e), 
                        style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor="white10")
                    ),
                    ft.FilledButton(
                        content="Generate Image", icon=ft.Icons.AUTO_AWESOME, on_click=lambda _: self.app.handle_generate(), 
                        style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE_800)
                    ),
                ], spacing=10)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.Padding(15, 10, 15, 10),
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, 0),
                end=ft.Alignment(1, 0),
                colors=[ft.Colors.BLUE_GREY_900, ft.Colors.BLUE_GREY_800]
            ),
            border_radius=ft.BorderRadius.only(top_left=10, top_right=10)
        )
        
        self.controls = [
            self.console_header,
            ft.Container(
                content=self.output_field,
                border=ft.Border.all(1, ft.Colors.BLUE_GREY_700),
                border_radius=ft.BorderRadius.only(bottom_left=10, bottom_right=10),
                padding=0
            )
        ]

    def update_output(self, text: str):
        self.output_field.value = text
        self.output_field.update()
