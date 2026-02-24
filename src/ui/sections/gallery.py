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
            ft.Container(content=self.gallery_row, height=220, bgcolor=ft.Colors.TRANSPARENT)
        ])

    def refresh(self, search_term="", update_ui=True, append=False):
        from ui.components.character_card import create_character_card
        
        MAX_GALLERY_ITEMS = 40
        
        if not append:
            self.gallery_row.controls.clear()
            self._current_matches = []
            self._loaded_count = 0
            
            selected_names = {(char.name if hasattr(char, "name") else char["name"]) for char in self.app.state.state["selected_characters"]}
            search_lower = (search_term or "").lower()
            
            # 1. Filter and build list of matches
            for name, meta in self.app.state.ctx.characters_metadata.items():
                tags_str = " ".join(meta.tags).lower()
                vibe_str = (meta.vibe or "").lower()
                bearing_str = (meta.bearing or "").lower()

                if search_lower and not (search_lower in name.lower() or
                                         search_lower in tags_str or
                                         search_lower in vibe_str or
                                         search_lower in bearing_str):
                    continue
                
                self._current_matches.append((name, meta, name in selected_names))
                
            self.count_label.value = f"({len(self._current_matches)})"

        # 2. Slice the next batch
        start_idx = self._loaded_count
        end_idx = start_idx + MAX_GALLERY_ITEMS
        batch = self._current_matches[start_idx:end_idx]
        
        if not batch and append:
            return

        # Check if button already exists, remove it
        if self.gallery_row.controls and getattr(self.gallery_row.controls[-1], "data", None) == "load_more":
            self.gallery_row.controls.pop()

        for name, meta, is_sel in batch:
            card = create_character_card(
                char_name=name,
                char_data=meta.dict(),
                on_click_callback=self.handle_character_click,
                is_selected=is_sel,
                is_web=getattr(self.app, 'is_web', False)
            )
            self.gallery_row.controls.append(card)
            self._loaded_count += 1
            
        # Add "Load More" if there are more
        if self._loaded_count < len(self._current_matches):
            load_more_btn = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, size=30, color=ThemeManager.colors.get("accent", "blue")),
                    ft.Text("Load More", size=12, weight="bold")
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=ThemeManager.colors["surface"],
                border_radius=12,
                border=ft.Border.all(1, ThemeManager.colors["outline"]),
                on_click=lambda _: self.refresh(search_term=self.search_field.value, update_ui=True, append=True),
                alignment=ft.Alignment(0, 0),
                data="load_more",
                ink=True,
                height=200, width=160
            )
            self.gallery_row.controls.append(load_more_btn)

        if update_ui:
            self.update()

    def handle_search(self, e):
        self.refresh(e.control.value, update_ui=True, append=False)

    def handle_character_click(self, name):
        self.app.add_character(name)
        # Surgical update for the clicked card to avoid re-rendering the whole gallery
        for control in self.gallery_row.controls:
            if getattr(control, "data", None) != "load_more":
                # The name is inside the Info Panel -> Row -> Text
                try:
                    card_name = control.content.controls[0].controls[1].content.controls[0].controls[0].value
                    if card_name == name:
                        # Need to recreate the entire card because of the Flet Stack structure and selection badge overlay
                        meta = self.app.state.ctx.characters_metadata[name]
                        selected_names = {(char.name if hasattr(char, "name") else char["name"]) for char in self.app.state.state["selected_characters"]}
                        is_sel = name in selected_names
                        
                        from ui.components.character_card import create_character_card
                        new_card = create_character_card(
                            char_name=name,
                            char_data=meta.dict(),
                            on_click_callback=self.handle_character_click,
                            is_selected=is_sel,
                            is_web=getattr(self.app, 'is_web', False)
                        )
                        # Replace control in place
                        idx = self.gallery_row.controls.index(control)
                        self.gallery_row.controls[idx] = new_card
                        break
                except Exception:
                    pass

        self.update()
        self.app.refresh_roster()
        self.app.update_preview()

    def refresh_theme(self, update_ui=True):
        self.bgcolor = ThemeManager.colors["surface"]
        # Update header text
        header_row = self.content.controls[0]
        header_row.controls[0].controls[0].color = ThemeManager.colors["text_secondary"]  # "CHARACTER GALLERY"
        self.count_label.color = ThemeManager.colors["text_secondary"]
        if update_ui:
            self.update()
