import flet as ft
from core.flet_theme_manager import ThemeManager

class GallerySection(ft.Container):
    def __init__(self, app):
        super().__init__()
        self.app = app # This will be the App instance
        self.height = 240
        self.padding = 5
        self.bgcolor = ThemeManager.colors["surface"]
        self.border = ft.Border(bottom=ft.BorderSide(1, "outlinevariant"))
        
        # Search Components
        self.search_field = ft.TextField(
            hint_text="Filter Characters...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=self.handle_search,
            width=220, height=35, text_size=12, content_padding=5
        )
        
        self.count_label = ft.Text("0", size=12, color="grey")
        
        self.gallery_row = ft.Row(spacing=10, scroll=ft.ScrollMode.ALWAYS, height=160)
        
        self.refresh_btn = ft.IconButton(
            ft.Icons.REFRESH, 
            tooltip="Refresh Gallery", 
            on_click=lambda _: self.refresh(),
            icon_size=20
        )

        self.content = ft.Column([
            ft.Row([
                ft.Row([
                    ft.Text("CHARACTER GALLERY", weight="bold", size=14, color=ThemeManager.colors["text_secondary"]), 
                    self.count_label,
                    self.refresh_btn
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                self.search_field
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(content=self.gallery_row, height=180, bgcolor=ft.Colors.TRANSPARENT)
        ])

    def refresh(self, search_term=""):
        from ui.components.character_card import create_character_card
        
        selected_names = {char["name"] for char in self.app.state.state["selected_characters"]}
        chars = sorted(self.app.state.ctx.characters.keys())
        search_lower = (search_term or "").lower()
        
        new_controls = []
        visible_count = 0
        
        for name in chars:
            char_data = self.app.state.ctx.characters[name]
            tags_str = str(char_data.get("tags", "")).lower()
            
            if search_lower in name.lower() or search_lower in tags_str:
                is_sel = (name in selected_names)
                
                card = create_character_card(
                    char_name=name,
                    char_data=char_data,
                    on_click_callback=self.handle_character_click,
                    is_selected=is_sel
                )
                new_controls.append(card)
                visible_count += 1
                
        self.gallery_row.controls = new_controls
        self.count_label.value = f"({visible_count})"
        self.update()

    def handle_search(self, e):
        self.refresh(e.control.value)

    def handle_character_click(self, name):
        self.app.state.add_character(name)
        self.refresh(self.search_field.value)
        self.app.refresh_roster()
        self.app.update_preview()

    def refresh_theme(self):
        self.bgcolor = ThemeManager.colors["surface"]
        # Update text if needed, requires ref
        # For minimal impact, we just update container bg
        self.update()
