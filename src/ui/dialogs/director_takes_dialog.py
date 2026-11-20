import flet as ft
from core.flet_theme_manager import ThemeManager


class DirectorTakesDialog:
    """Dialog displaying 3 AI Director takes / variations for a scene prompt."""

    def __init__(self, app, takes: list, on_apply):
        self.app = app
        self.takes = takes
        self.on_apply = on_apply
        self.dialog = None

    def build(self) -> ft.AlertDialog:
        cards = []
        for i, take in enumerate(self.takes):
            title = take.get("title", f"Take {i+1}")
            style_notes = take.get("style_notes", "")
            prompt = take.get("prompt", "")

            cards.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Row([
                                ft.Icon(ft.Icons.VIDEOCAM, color=ThemeManager.colors["accent"], size=18),
                                ft.Text(title, weight=ft.FontWeight.W_700, size=13, color=ThemeManager.colors["text_primary"]),
                            ], spacing=6),
                            ft.FilledButton(
                                "Apply Take",
                                icon=ft.Icons.CHECK,
                                on_click=lambda _, p=prompt, t=title: self._apply(p, t),
                                style=ft.ButtonStyle(
                                    bgcolor=ThemeManager.colors["accent"],
                                    color="#ffffff",
                                    shape=ft.RoundedRectangleBorder(radius=6),
                                ),
                            ),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Text(f"🎬 {style_notes}" if style_notes else "", size=11, italic=True, color=ThemeManager.colors["text_secondary"]),
                        ft.TextField(
                            value=prompt,
                            multiline=True,
                            read_only=True,
                            min_lines=2,
                            max_lines=5,
                            text_size=12,
                            border_color=ThemeManager.colors["outline"],
                            bgcolor=ft.Colors.with_opacity(0.3, ThemeManager.colors["surface"]),
                            color=ThemeManager.colors["text_primary"],
                        ),
                    ], spacing=6),
                    padding=10,
                    border=ft.Border.all(1, ThemeManager.colors["outline"]),
                    border_radius=8,
                    bgcolor=ft.Colors.with_opacity(0.2, ThemeManager.colors["surface"]),
                )
            )

        content = ft.Container(
            content=ft.Column(cards, spacing=10, scroll=ft.ScrollMode.AUTO),
            width=680,
            height=460,
        )

        self.dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.THEATERS, color=ThemeManager.colors["accent"], size=22),
                ft.Text("Director's Takes (3 Variations)", weight=ft.FontWeight.W_700, size=16, color=ThemeManager.colors["text_primary"]),
            ], spacing=10),
            content=content,
            actions=[
                ft.TextButton("Close", on_click=lambda _: self._close()),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        return self.dialog

    def show(self):
        if not self.dialog:
            self.build()
        if self.app.page:
            self.dialog.open = True
            if self.dialog not in self.app.page.overlay:
                self.app.page.overlay.append(self.dialog)
            self.app.page.update()

    def _apply(self, prompt: str, title: str):
        self.on_apply(prompt)
        self.app.show_toast(f"Applied: {title}!", color="green")
        self._close()

    def _close(self):
        if self.dialog and self.app.page:
            self.dialog.open = False
            self.app.page.update()
