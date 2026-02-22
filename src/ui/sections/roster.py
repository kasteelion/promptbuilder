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
        self.bulk_cat_dd = ft.Dropdown(
            label="Category", 
            expand=True,
            text_size=12, height=40, content_padding=10
        )
        self.bulk_cat_dd.on_select = self.handle_bulk_cat_change
        self.bulk_outfit_dd = ft.Dropdown(
            label="Outfit", 
            expand=True,
            disabled=True,
            text_size=12, height=40, content_padding=10
        )
        self.bulk_sig_toggle = ft.Switch(label="Sig Color", value=False, scale=0.8)
        
        # --- Main Layout ---
        self.roster_list = ft.Column(expand=True, spacing=10, scroll=ft.ScrollMode.AUTO)
        
        self.content = ft.Column([
            # Top Bar: Header + Actions
            ft.Row([
                ft.Text("ACTIVE ROSTER", weight="bold", size=14, color=ThemeManager.colors["text_secondary"]),
                ft.TextButton("Clear All", on_click=self.handle_clear_all, icon=ft.Icons.DELETE_SWEEP, 
                              style=ft.ButtonStyle(color=ThemeManager.colors["error"]))
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            # Bulk Editor Panel
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.FLASH_ON, size=16, color="amber"),
                        ft.Text("BULK EDITOR", size=12, weight="bold", color="amber"),
                    ], spacing=5),
                    ft.Row([
                        self.bulk_cat_dd,
                        self.bulk_outfit_dd,
                    ], spacing=10),
                    ft.Row([
                        self.bulk_sig_toggle,
                        ft.FilledButton(
                            "APPLY TO ALL", 
                            icon=ft.Icons.DONE_ALL, 
                            on_click=self.handle_bulk_apply,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=5),
                                bgcolor=ThemeManager.colors["accent"]
                            )
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ], spacing=8),
                padding=10,
                bgcolor=ThemeManager.colors["panel_bg"],
                border_radius=8,
                border=ft.Border.all(1, ThemeManager.colors["outline"])
            ),
            
            ft.Divider(height=1, color=ThemeManager.colors["outline"]),
            
            # The List
            self.roster_list
        ], spacing=10)

    def populate_data(self):
        """Populate bulk dropdowns from context."""
        ctx = self.app.state.ctx
        cats = sorted(list(set(
            cat 
            for char in ctx.characters.values() 
            for cat in char.get("outfits_categorized", {}).keys()
        )))
        self.bulk_cat_dd.options = [ft.dropdown.Option(c) for c in cats]

    def refresh(self, update_ui=True):
        """Rebuild the active roster UI using RosterItem components."""
        # print("DEBUG_EVENT: Roster - Performing Full Refresh") # Reduced noise
        self.populate_data()
        
        items = []
        for idx, char in enumerate(self.app.state.state["selected_characters"]):
            # Pass callback to update preview when item changes
            item = RosterItem(
                self.app, 
                idx, 
                char, 
                on_update_callback=self.app.update_preview
            )
            items.append(item)
            
        self.roster_list.controls = items
        if update_ui:
            self.update()

    def update_character_ui(self, idx):
        """Surgical update alias for compatibility."""
        if idx < len(self.roster_list.controls):
            item = self.roster_list.controls[idx]
            if isinstance(item, RosterItem):
                item.surgical_update()

    # --- Handlers ---

    def handle_bulk_cat_change(self, e):
        cat = e.control.value
        if not cat: return
        
        ctx = self.app.state.ctx
        outfits = set()
        for char in ctx.characters.values():
            if cat in char.get("outfits_categorized", {}):
                outfits.update(char["outfits_categorized"][cat].keys())
        
        self.bulk_outfit_dd.options = [ft.dropdown.Option(o) for o in sorted(list(outfits))]
        self.bulk_outfit_dd.disabled = False
        self.bulk_outfit_dd.value = None
        self.bulk_outfit_dd.update()

    def handle_bulk_apply(self, e):
        cat = self.bulk_cat_dd.value
        outfit = self.bulk_outfit_dd.value
        use_sig = self.bulk_sig_toggle.value
        
        if not self.app.state.state["selected_characters"]: return
        
        count = 0
        for char in self.app.state.state["selected_characters"]:
            if cat and outfit:
                char["outfit_category"] = cat
                char["outfit"] = outfit
                char["outfit_traits"] = []
            
            char["use_signature_color"] = use_sig
            count += 1
            
        self.app.show_toast(f"Updated {count} characters!")
        self.refresh() # Full refresh needed for bulk
        self.app.update_preview()

    def handle_clear_all(self, e):
        self.app.clear_all_characters()

    def refresh_theme(self):
        # Refresh container styles
        self.border = ft.Border.all(1, ThemeManager.colors["outline"])
        self.padding = ThemeManager.styles["padding"]
        # Refresh bulk panel (index 1 of content)
        # We need a reference or we reconstruct. 
        # For now, simplistic rebuild might be safer but refresh_roster calls populate_data and reconstructs list
        # We just need to update the static parts
        bulk_panel = self.content.controls[1]
        bulk_panel.bgcolor = ThemeManager.colors["panel_bg"]
        bulk_panel.border = ft.Border.all(1, ThemeManager.colors["outline"])
        self.content.controls[2].color = ThemeManager.colors["outline"] # Divider
        self.content.controls[0].controls[0].color = ThemeManager.colors["text_secondary"] # Header
        self.update()
