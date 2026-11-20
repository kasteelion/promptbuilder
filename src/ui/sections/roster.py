import flet as ft
from core.flet_theme_manager import ThemeManager
from ui.components.roster_item import RosterItem


class RosterSection(ft.Container):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.expand = True
        self.padding = ThemeManager.styles["padding"]
        self.border = ft.Border.all(1, ThemeManager.colors["outline"])
        self.border_radius = ft.BorderRadius.all(ThemeManager.styles["radius"])

        # --- Bulk Editor Controls ---
        self.bulk_sig_toggle = ft.Switch(label="Sig Color", value=False, scale=0.8)

        # --- Main Layout ---
        self.roster_list = ft.Column(expand=True, spacing=8, scroll=ft.ScrollMode.AUTO)

        # Bulk Editor Panel (hidden when empty)
        self.bulk_panel = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Row([
                        ft.Icon(ft.Icons.FLASH_ON, size=14, color="#f59e0b"),
                        ft.Text("BULK EDITOR", size=11, weight=ft.FontWeight.W_700,
                                color="#f59e0b"),
                    ], spacing=5),
                ]),
                ft.Row([
                    ft.FilledButton(
                        "Global Outfit Editor...",
                        icon=ft.Icons.CHECKROOM,
                        on_click=lambda e: self.app.open_outfit_builder(character_index=None),
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=8),
                            bgcolor=ThemeManager.colors["surface_variant"],
                            color=ThemeManager.colors["text_primary"],
                        ),
                        expand=True,
                    ),
                ]),
                ft.Row([
                    self.bulk_sig_toggle,
                    ft.FilledButton(
                        "APPLY SIG COLOR",
                        icon=ft.Icons.COLORIZE,
                        on_click=self.handle_bulk_apply_sig,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=8),
                            bgcolor=ThemeManager.colors["accent"],
                        ),
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ], spacing=8),
            padding=12,
            bgcolor=ThemeManager.colors["panel_bg"],
            border_radius=10,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.3, "#f59e0b")),
            visible=False,
        )

        # Clear All button (hidden when empty)
        self.clear_btn = ft.TextButton(
            "Clear All",
            on_click=self.handle_clear_all,
            icon=ft.Icons.DELETE_SWEEP,
            style=ft.ButtonStyle(color="#ef4444"),
            visible=False,
        )

        # Roster count badge
        self._count_badge = ft.Container(
            content=ft.Text("0", size=10, weight=ft.FontWeight.W_700, color="#ffffff"),
            width=22, height=22, border_radius=11,
            bgcolor=ThemeManager.colors["accent"],
            alignment=ft.Alignment(0, 0),
            visible=False,
        )

        # Empty State Dashboard (shown when no characters selected)
        self.empty_state = ft.Container(
            content=None,
            alignment=ft.Alignment(0, 0),
            expand=True,
        )

        self.content = ft.Column([
            # Top Bar: Header + Actions
            ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.GROUPS, size=16, color=ThemeManager.colors["text_secondary"]),
                    ft.Text("ACTIVE ROSTER", weight=ft.FontWeight.W_600, size=13,
                            color=ThemeManager.colors["text_secondary"]),
                    self._count_badge,
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                self.clear_btn,
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

            self.bulk_panel,
            ft.Divider(height=1, color=ft.Colors.with_opacity(0.06, ThemeManager.colors["text_primary"])),

            # The List OR Empty State
            self.roster_list,
            self.empty_state,
        ], spacing=8, expand=True)

    def populate_data(self):
        """Legacy method for context population."""
        pass

    def build_dashboard_content(self):
        """Build statistics and actions dashboard when active roster is empty."""
        total_chars = len(self.app.state.ctx.characters_metadata)
        
        scenes_data = self.app.state.ctx.scenes
        total_scenes = sum(len(presets) for presets in scenes_data.values()) if scenes_data else 0
        
        interactions_data = self.app.state.ctx.interactions
        total_interactions = sum(len(presets) for presets in interactions_data.values()) if interactions_data else 0
        
        def make_stat_card(title, value, icon, color):
            return ft.Container(
                content=ft.Column([
                    ft.Icon(icon, size=24, color=color),
                    ft.Text(str(value), size=20, weight="bold", color=ThemeManager.colors["text_primary"]),
                    ft.Text(title, size=10, color=ThemeManager.colors["text_secondary"]),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                bgcolor=ThemeManager.colors["panel_bg"],
                border=ft.Border.all(1, ThemeManager.colors["outline"]),
                border_radius=8,
                padding=12,
                expand=True,
            )

        stats_row = ft.Row([
            make_stat_card("Characters", total_chars, ft.Icons.PEOPLE, ft.Colors.BLUE_400),
            make_stat_card("Scenes", total_scenes, ft.Icons.LANDSCAPE, ft.Colors.GREEN_400),
            make_stat_card("Interactions", total_interactions, ft.Icons.AUTO_AWESOME, ft.Colors.AMBER_400)
        ], spacing=10)

        quick_actions_header = ft.Text("QUICK TOOLS", size=10, weight=ft.FontWeight.W_700, color=ThemeManager.colors["text_secondary"])

        def make_action_button(label, icon, tooltip, on_click):
            return ft.Container(
                content=ft.Row([
                    ft.Icon(icon, size=16, color=ThemeManager.colors["accent"]),
                    ft.Text(label, size=12, weight="bold", color=ThemeManager.colors["text_primary"]),
                ], spacing=8),
                bgcolor=ThemeManager.colors["panel_bg"],
                border=ft.Border.all(1, ThemeManager.colors["outline"]),
                border_radius=8,
                padding=10,
                on_click=on_click,
                expand=True,
                tooltip=tooltip,
                ink=True
            )

        actions_row = ft.Row([
            make_action_button("Automation Studio", ft.Icons.ROCKET_LAUNCH, "Launch batch generator", lambda _: self.app.open_automation_dialog()),
            make_action_button("Output Gallery", ft.Icons.PHOTO_LIBRARY_OUTLINED, "View generated images", lambda _: self.app.open_output_gallery()),
        ], spacing=10)

        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.GROUP_ADD_OUTLINED, size=40, color=ft.Colors.with_opacity(0.3, ThemeManager.colors["accent"])),
                ft.Column([
                    ft.Text("Welcome to Prompt Builder Studio", size=15, weight="bold", color=ThemeManager.colors["text_primary"]),
                    ft.Text("Add characters from the gallery above to build your active roster.", size=11, color=ThemeManager.colors["text_secondary"]),
                ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                stats_row,
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                quick_actions_header,
                actions_row,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            padding=ft.Padding(20, 20, 20, 20),
            alignment=ft.Alignment(0, 0),
        )

    def refresh(self, update_ui=True):
        """Rebuild the active roster UI using RosterItem components."""
        self.populate_data()

        items = []
        for idx, char in enumerate(self.app.state.state["selected_characters"]):
            item = RosterItem(
                self.app,
                idx,
                char,
                on_update_callback=self.app.update_preview,
            )
            items.append(item)

        self.roster_list.controls = items

        # Toggle empty state vs populated state
        has_chars = len(items) > 0
        self.empty_state.visible = not has_chars
        if not has_chars:
            self.empty_state.content = self.build_dashboard_content()
            
        self.roster_list.visible = has_chars
        self.bulk_panel.visible = len(items) >= 2
        self.clear_btn.visible = has_chars
        self._count_badge.visible = has_chars
        self._count_badge.content.value = str(len(items))

        if update_ui:
            self.update()

    def update_character_ui(self, idx):
        """Surgical update alias for compatibility."""
        if idx < len(self.roster_list.controls):
            item = self.roster_list.controls[idx]
            if isinstance(item, RosterItem):
                item.surgical_update()

    # --- Handlers ---

    def handle_bulk_apply_sig(self, e):
        use_sig = self.bulk_sig_toggle.value

        selected_chars = self.app.state.state["selected_characters"]
        if not selected_chars:
            return

        for char in selected_chars:
            char.use_signature_color = use_sig

        self.app.show_toast("Updated signature color for all characters!")
        self.refresh()  # Full refresh needed for bulk
        self.app.update_preview()

    def handle_clear_all(self, e):
        self.app.clear_all_characters()

    def refresh_theme(self, update_ui=True):
        self.border = ft.Border.all(1, ThemeManager.colors["outline"])
        self.padding = ThemeManager.styles["padding"]
        self.bulk_panel.bgcolor = ThemeManager.colors["panel_bg"]
        self.bulk_panel.border = ft.Border.all(1, ft.Colors.with_opacity(0.3, "#f59e0b"))
        self._count_badge.bgcolor = ThemeManager.colors["accent"]
        if update_ui:
            self.update()
