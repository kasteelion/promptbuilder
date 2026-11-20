import flet as ft
from ui.components.icon_button import SafeIconButton
from core.flet_theme_manager import ThemeManager

class ToolbarSection(ft.Container):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.height = 58
        self.padding = ft.Padding.symmetric(vertical=12, horizontal=16)
        self.bgcolor = ft.Colors.with_opacity(0.85, ThemeManager.colors["surface"])
        self.border = ft.Border.only(bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.08, ThemeManager.colors["text_primary"])))
        self.margin = ft.Padding.only(bottom=6)
        self.shadow = ft.BoxShadow(
            spread_radius=0,
            blur_radius=20,
            color=ft.Colors.with_opacity(0.25, ft.Colors.BLACK),
            offset=ft.Offset(0, 3),
        )
        self.blur = ft.Blur(12, 12, ft.BlurTileMode.MIRROR)
        
        # Build Theme Menu Items
        theme_items = [
            ft.PopupMenuItem(
                content=ft.Row([
                    ft.Container(width=12, height=12, border_radius=6, bgcolor=ThemeManager.get_theme_accent(name)),
                    ft.Text(name, size=13)
                ], spacing=10), 
                on_click=lambda e, n=name: self.app.set_theme(n)
            ) for name in ThemeManager.get_available_themes()
        ]

        self.theme_btn = ft.PopupMenuButton(
            icon=ft.Icons.PALETTE,
            icon_color=ThemeManager.colors["header_fg"],
            tooltip="Select Theme",
            items=theme_items
        )

        # --- App Title with gradient accent ---
        title_row = ft.Row([
            ft.PopupMenuButton(
                icon=ft.Icons.MENU,
                icon_color=ThemeManager.colors["header_fg"],
                items=[
                    ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.DASHBOARD, size=18), ft.Text("Dashboard", size=13)], spacing=10), on_click=self.app.show_dashboard),
                    ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.ACCOUNT_TREE, size=18), ft.Text("Context Studio (Scenes/Interactions)", size=13)], spacing=10), on_click=lambda _: self.app.open_context_studio()),
                    ft.PopupMenuItem(),
                    ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.FILE_UPLOAD, size=18), ft.Text("Import from Text", size=13)], spacing=10), on_click=self.app.open_import_from_text),
                    ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.PSYCHOLOGY, size=18), ft.Text("Export for LLM", size=13)], spacing=10), on_click=self.app.open_llm_export),
                    ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.AUTO_FIX_HIGH, size=18), ft.Text("Asset Studio (AI)", size=13)], spacing=10), on_click=self.app.open_asset_studio),
                    ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.CHECKROOM, size=18), ft.Text("Outfit Builder", size=13)], spacing=10), on_click=self.app.open_outfit_builder),
                    ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.PERSON_ADD_ALT_1, size=18), ft.Text("AI Character Creator", size=13)], spacing=10), on_click=self.app.open_ai_character_creator),
                    ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.EDIT_ATTRIBUTES, size=18), ft.Text("Asset Editor", size=13)], spacing=10), on_click=self.app.open_asset_editor),
                    ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.SETTINGS, size=18), ft.Text("Settings", size=13)], spacing=10), on_click=self.app.open_settings),
                    ft.PopupMenuItem(),
                    ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.DELETE_SWEEP, size=18, color="#ef4444"), ft.Text("Clear All Characters", size=13)], spacing=10), on_click=lambda _: self.app.clear_all_characters()),
                    ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.RESTART_ALT, size=18), ft.Text("Reset All Outfits", size=13)], spacing=10), on_click=lambda _: self.app.reset_all_outfits()),
                ],
                tooltip="Menu"
            ),
            ft.Container(
                content=ft.Text("PROMPT BUILDER", size=20, weight=ft.FontWeight.W_900, 
                               color=ThemeManager.colors["header_fg"]),
            ),
        ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        # --- Tool Groups with separators ---
        def _sep():
            return ft.VerticalDivider(width=1, color=ft.Colors.with_opacity(0.12, ThemeManager.colors["outline"]))

        tool_row = ft.Row([
            # Quick Actions
            SafeIconButton(ft.Icons.CASINO, icon_color="#f59e0b", tooltip="Smart Randomize", on_click=self.app.handle_randomize, scale=0.9),
            SafeIconButton(ft.Icons.ACCOUNT_TREE_OUTLINED, icon_color=ThemeManager.colors["header_fg"], tooltip="Context Studio (Tree View)", on_click=lambda _: self.app.open_context_studio(), scale=0.9),
            _sep(),
            # AI Tools
            SafeIconButton(ft.Icons.ROCKET_LAUNCH, icon_color=ThemeManager.colors["header_fg"], tooltip="Automation Studio", on_click=self.app.open_automation_dialog, scale=0.9),
            _sep(),
            # File Ops
            SafeIconButton(ft.Icons.SAVE_OUTLINED, icon_color=ThemeManager.colors["header_fg"], tooltip="Save Preset", on_click=self.app.save_preset, scale=0.9),
            SafeIconButton(ft.Icons.FOLDER_OPEN_OUTLINED, icon_color=ThemeManager.colors["header_fg"], tooltip="Load Preset", on_click=self.app.load_preset, scale=0.9),
            _sep(),
            # View
            SafeIconButton(ft.Icons.PHOTO_LIBRARY_OUTLINED, icon_color=ThemeManager.colors["header_fg"], tooltip="Output Gallery", on_click=self.app.open_output_gallery, scale=0.9),
            _sep(),
            # System
            self.theme_btn,
            SafeIconButton(ft.Icons.REFRESH, icon_color=ThemeManager.colors["header_fg"], tooltip="Refresh Assets", on_click=self.app.refresh_assets, scale=0.9),
            SafeIconButton(ft.Icons.SETTINGS_OUTLINED, icon_color=ThemeManager.colors["header_fg"], tooltip="Settings", on_click=self.app.open_settings, scale=0.9),
        ], spacing=4)

        self.content = ft.Row([
            title_row,
            tool_row,
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    def refresh_theme(self, update_ui=True):
        self.bgcolor = ft.Colors.with_opacity(0.85, ThemeManager.colors["header_bg"])

        # Title row: controls[0] = menu popup, controls[1] = title container
        title_row = self.content.controls[0]
        title_row.controls[0].icon_color = ThemeManager.colors["header_fg"]  # Menu
        title_row.controls[1].content.color = ThemeManager.colors["header_fg"]  # Title text

        # Tool row
        tool_row = self.content.controls[1]
        for btn in tool_row.controls:
            if hasattr(btn, "icon_color"):
                btn.icon_color = ThemeManager.colors["header_fg"]
            elif isinstance(btn, ft.PopupMenuButton):
                btn.icon_color = ThemeManager.colors["header_fg"]

        if update_ui:
            self.update()

