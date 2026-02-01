import flet as ft
from ui.components.icon_button import SafeIconButton
from core.flet_theme_manager import ThemeManager

class ToolbarSection(ft.Container):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.height = 60
        self.padding = ft.Padding(20, 10, 20, 10)
        self.gradient = ft.LinearGradient(
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
            colors=[ThemeManager.colors["accent"], ThemeManager.colors["accent_hover"]]
        )
        self.border_radius = ft.BorderRadius.all(10)
        self.margin = ft.Padding(0, 0, 0, 5)
        
        # Build Theme Menu Items
        theme_items = [
            ft.PopupMenuItem(
                content=ft.Text(name), 
                on_click=lambda e, n=name: self.app.set_theme(n)
            ) for name in ThemeManager.get_available_themes()
        ]

        self.theme_btn = ft.PopupMenuButton(
            icon=ft.Icons.PALETTE,
            icon_color="white",
            tooltip="Select Theme",
            items=theme_items
        )

        self.content = ft.Row([
            ft.PopupMenuButton(
                icon=ft.Icons.MENU,
                items=[
                    ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.DASHBOARD), ft.Text("Dashboard")], spacing=10), on_click=self.app.show_dashboard),
                    ft.PopupMenuItem(),
                    ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.FILE_UPLOAD), ft.Text("Import from Text")], spacing=10), on_click=self.app.open_import_from_text),
                    ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.PSYCHOLOGY), ft.Text("Export for LLM")], spacing=10), on_click=self.app.open_llm_export),
                    ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.LIBRARY_BOOKS), ft.Text("Content Guide")], spacing=10), on_click=self.app.open_llm_content_guide),
                    ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.EDIT_ATTRIBUTES), ft.Text("Asset Editor")], spacing=10), on_click=self.app.open_asset_editor),
                    ft.PopupMenuItem(),
                    ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.DELETE_SWEEP), ft.Text("Clear All Characters")], spacing=10), on_click=lambda _: self.app.clear_all_characters()),
                    ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.CHECKROOM), ft.Text("Reset All Outfits")], spacing=10), on_click=lambda _: self.app.reset_all_outfits()),
                ],
                tooltip="Menu"
            ),
            ft.Text("PROMPT BUILDER", size=22, weight="bold", color=ThemeManager.colors["text_primary"]),
            ft.VerticalDivider(color=ThemeManager.colors["outline"]),
            ft.Row([
                self.theme_btn,
                SafeIconButton(ft.Icons.AUTO_FIX_HIGH, icon_color="white", tooltip="Automation", on_click=self.app.open_automation_dialog),
                SafeIconButton(ft.Icons.SAVE, icon_color="white", tooltip="Save Preset", on_click=self.app.save_preset),
                SafeIconButton(ft.Icons.FOLDER_OPEN, icon_color="white", tooltip="Load Preset", on_click=self.app.load_preset),
                SafeIconButton(ft.Icons.IMAGE_OUTLINED, icon_color="white", tooltip="Output Gallery", on_click=self.app.open_output_gallery),
                SafeIconButton(ft.Icons.REFRESH, icon_color="white", tooltip="Refresh Assets", on_click=self.app.refresh_assets),
                SafeIconButton(ft.Icons.SETTINGS, icon_color="white", tooltip="Settings", on_click=self.app.open_settings),
            ], spacing=0)
        ], alignment=ft.MainAxisAlignment.START)

    def refresh_theme(self):
        self.gradient.colors = [ThemeManager.colors["accent"], ThemeManager.colors["accent_hover"] or ThemeManager.colors["accent"]]
        self.update()
