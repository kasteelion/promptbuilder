import flet as ft
from core.flet_theme_manager import ThemeManager


class GallerySection(ft.Container):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.padding = ft.Padding.symmetric(horizontal=8, vertical=4)
        self.bgcolor = ThemeManager.colors["surface"]
        self.border = ft.Border(
            bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.06, ThemeManager.colors["text_primary"]))
        )

        # Search Components
        self.search_field = ft.TextField(
            hint_text="Search characters...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=self.handle_search,
            width=220, height=36, text_size=12, content_padding=6,
            border_color=ThemeManager.colors["outline"],
            focused_border_color=ThemeManager.colors["accent"],
            border_radius=8,
        )

        self.count_label = ft.Text("0", size=11, color=ThemeManager.colors["text_secondary"],
                                   italic=True)

        self.gallery_row = ft.Row(spacing=10, scroll=ft.ScrollMode.ALWAYS, height=220)

        self.refresh_btn = ft.IconButton(
            ft.Icons.REFRESH,
            tooltip="Refresh Gallery",
            on_click=lambda _: self.refresh(),
            icon_size=18,
            icon_color=ThemeManager.colors["text_secondary"],
        )

        self.is_collapsed = False
        self.collapse_btn = ft.IconButton(
            ft.Icons.KEYBOARD_ARROW_UP,
            tooltip="Collapse Gallery",
            icon_size=20,
            icon_color=ThemeManager.colors["text_secondary"],
            on_click=self.toggle_collapse,
        )

        self.gallery_container = ft.Container(
            content=self.gallery_row, 
            height=220, 
            bgcolor=ft.Colors.TRANSPARENT,
            animate_opacity=200,
        )

        self.content = ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Row([
                        self.collapse_btn,
                        ft.Icon(ft.Icons.PEOPLE_ALT_OUTLINED, size=16,
                                color=ThemeManager.colors["text_secondary"]),
                        ft.Text("CHARACTER GALLERY", weight=ft.FontWeight.W_600, size=13,
                                color=ThemeManager.colors["text_secondary"]),
                        self.count_label,
                        self.refresh_btn,
                    ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    self.search_field,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
                padding=ft.Padding.symmetric(horizontal=4, vertical=2),
            ),
            self.gallery_container,
        ], spacing=2)

    def toggle_collapse(self, e=None):
        self.is_collapsed = not self.is_collapsed
        self.gallery_container.visible = not self.is_collapsed
        self.collapse_btn.icon = ft.Icons.KEYBOARD_ARROW_DOWN if self.is_collapsed else ft.Icons.KEYBOARD_ARROW_UP
        self.collapse_btn.tooltip = "Expand Gallery" if self.is_collapsed else "Collapse Gallery"
        self.update()

    def refresh(self, search_term="", update_ui=True, append=False):
        from ui.components.character_card import create_character_card

        MAX_GALLERY_ITEMS = 40

        if not append:
            self.gallery_row.controls.clear()
            self._current_matches = []
            self._loaded_count = 0

            selected_names = {
                (char.name if hasattr(char, "name") else char["name"])
                for char in self.app.state.state["selected_characters"]
            }
            search_lower = (search_term or "").lower()

            # 1. Filter and build list of matches
            for name, meta in self.app.state.ctx.characters_metadata.items():
                tags_str = " ".join(meta.tags).lower()
                vibe_str = (meta.vibe or "").lower()
                bearing_str = (meta.bearing or "").lower()

                if search_lower and not (
                    search_lower in name.lower()
                    or search_lower in tags_str
                    or search_lower in vibe_str
                    or search_lower in bearing_str
                ):
                    continue

                self._current_matches.append((name, meta, name in selected_names))

            self.count_label.value = f"{len(self._current_matches)} available"

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
                is_web=getattr(self.app, "is_web", False),
            )
            self.gallery_row.controls.append(card)
            self._loaded_count += 1

        # Add "Load More" if there are more
        if self._loaded_count < len(self._current_matches):
            remaining = len(self._current_matches) - self._loaded_count
            load_more_btn = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, size=28,
                            color=ThemeManager.colors.get("accent", "blue")),
                    ft.Text(f"+{remaining} more", size=11, weight="bold",
                            color=ThemeManager.colors["text_secondary"]),
                ], alignment=ft.MainAxisAlignment.CENTER,
                   horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=ThemeManager.colors["surface"],
                border_radius=12,
                border=ft.Border.all(1, ThemeManager.colors["outline"]),
                on_click=lambda _: self.refresh(
                    search_term=self.search_field.value, update_ui=True, append=True
                ),
                alignment=ft.Alignment(0, 0),
                data="load_more",
                ink=True,
                height=200,
                width=160,
            )
            self.gallery_row.controls.append(load_more_btn)

        if update_ui:
            self.update()

    def handle_search(self, e):
        self.refresh(e.control.value, update_ui=True, append=False)

    def handle_character_click(self, name):
        # add_character in main handles roster refresh, gallery card state, and preview update
        self.app.add_character(name)

    def refresh_theme(self, update_ui=True):
        self.bgcolor = ThemeManager.colors["surface"]
        self.search_field.border_color = ThemeManager.colors["outline"]
        self.search_field.focused_border_color = ThemeManager.colors["accent"]
        self.search_field.bgcolor = ThemeManager.colors.get("input_bg")
        self.search_field.color = ThemeManager.colors["text_primary"]

        # Update header text
        self.collapse_btn.icon_color = ThemeManager.colors["text_secondary"]
        header_container = self.content.controls[0]
        header_row = header_container.content
        header_row.controls[0].controls[2].color = ThemeManager.colors["text_secondary"]
        self.count_label.color = ThemeManager.colors["text_secondary"]
        if update_ui:
            self.update()
