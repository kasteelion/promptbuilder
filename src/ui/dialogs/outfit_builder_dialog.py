import flet as ft
import json
import os
import random
from pathlib import Path
from core.flet_theme_manager import ThemeManager


class OutfitBuilderDialog(ft.AlertDialog):
    """Character-aware Outfit Builder that integrates with the app's data pipeline.
    
    Modes:
        - Character Mode (default): Browse a specific character's outfits from outfits_categorized.
          Apply writes directly to char_data.
        - Custom Builder Mode: Ad-hoc outfit creation from attributes.json (legacy).
    """

    def __init__(self, app, character_index=None):
        super().__init__()
        self.app = app
        self.character_index = character_index
        self.title = ft.Text("Outfit Builder Studio", size=20, weight="bold")

        # Resolve character (None = global browse mode)
        self.char_data = None
        self.char_info = None
        self.char_name = None
        self.is_global_mode = (character_index is None)
        if character_index is not None and 0 <= character_index < len(app.state.state["selected_characters"]):
            self.char_data = app.state.state["selected_characters"][character_index]
            self.char_name = self.char_data["name"]
            self.char_info = app.state.ctx.characters.get(self.char_name, {})

        # Build the outfit catalogue
        self.catalogue = self._build_catalogue()

        # State
        self.selected_category = None
        self.selected_outfit = None
        self._init_defaults()

        # UI Components
        self.tree_view_container = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=2)
        self.detail_container = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=15)

        self.preview_text = ft.Text(
            "",
            size=13,
            selectable=True,
            font_family="Consolas",
            color=ThemeManager.colors["text_secondary"],
        )

        self.preview_container = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Prompt Preview", weight="bold", size=12, color=ThemeManager.colors["outline"]),
                    ft.IconButton(ft.Icons.COPY, tooltip="Copy to Clipboard", icon_size=18, on_click=self.handle_copy),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(height=10, color=ThemeManager.colors["outline"]),
                ft.Container(
                    content=self.preview_text,
                    padding=15,
                    border_radius=8,
                    bgcolor=ThemeManager.colors["active_item"],
                    border=ft.border.all(1, ThemeManager.colors["outline"]),
                    expand=True,
                ),
            ]),
            expand=True,
            padding=10,
        )

        # Header for character context
        if self.is_global_mode:
            header_text = "All Outfits (Global Browse)"
            header_icon = ft.Icons.PUBLIC
        else:
            header_text = f"Editing: {self.char_name}"
            header_icon = ft.Icons.PERSON
        header_bar = ft.Container(
            content=ft.Row([
                ft.Icon(header_icon, color=ThemeManager.colors["accent"], size=20),
                ft.Text(header_text, weight="bold", size=14),
            ], spacing=8),
            padding=ft.padding.only(bottom=5),
        )

        # Main Layout — flat Container with explicit height, matching working dialog patterns
        self.content = ft.Container(
            width=1200,
            height=750,
            bgcolor=ThemeManager.colors["surface"],
            content=ft.Row([
                # Left Pane: Tree View (Categories -> Outfits)
                ft.Container(
                    content=ft.Column([
                        header_bar,
                        ft.Text("Outfit Categories", weight="bold", size=14,
                                color=ThemeManager.colors["text_secondary"]),
                        ft.Divider(height=1, color=ThemeManager.colors["outline"]),
                        self.tree_view_container,
                    ]),
                    width=260,
                    padding=10,
                    border=ft.border.only(right=ft.BorderSide(1, ThemeManager.colors["outline"])),
                ),

                # Middle Pane: Detail View for Selected Outfit
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Outfit Details", weight="bold", size=16),
                            ft.IconButton(ft.Icons.SHUFFLE, tooltip="Random Outfit",
                                          on_click=lambda e: self.randomize_outfit()),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=1, color=ThemeManager.colors["outline"]),
                        self.detail_container,
                    ], scroll=ft.ScrollMode.AUTO),
                    expand=True,
                    padding=20,
                ),

                # Right Pane: Preview
                ft.Container(
                    width=350,
                    content=self.preview_container,
                    border=ft.border.only(left=ft.BorderSide(1, ThemeManager.colors["outline"])),
                    padding=10,
                ),
            ], spacing=0),
        )

        self.actions = [
            ft.TextButton("Close", on_click=self.handle_close),
            ft.FilledButton("Apply to Character", icon=ft.Icons.CHECK, on_click=self.handle_apply,
                            disabled=(self.char_data is None)),
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

        self.build_tree_view()
        self._safe_update_preview()

    def _build_catalogue(self):
        """Build the outfit catalogue based on mode.
        
        Character mode: uses the character's outfits_categorized.
        Global mode: aggregates all outfits across all characters.
        """
        if not self.is_global_mode and self.char_info:
            return self.char_info.get("outfits_categorized", {})

        # Global mode: merge all characters' outfits_categorized
        merged = {}
        for char_name, char_data in self.app.state.ctx.characters.items():
            for cat, outfits in char_data.get("outfits_categorized", {}).items():
                if cat not in merged:
                    merged[cat] = {}
                merged[cat].update(outfits)
        return merged

    def _init_defaults(self):
        """Set initial selection to the character's current outfit."""
        if self.char_data:
            self.selected_category = self.char_data.get("outfit_category")
            self.selected_outfit = self.char_data.get("outfit")

    # ──────────────────────────────────────────────
    # TREE VIEW
    # ──────────────────────────────────────────────

    def build_tree_view(self):
        """Builds the tree from the catalogue."""
        self.tree_view_container.controls.clear()

        if not self.catalogue:
            self.tree_view_container.controls.append(
                ft.Text("No outfits available.", italic=True, color=ThemeManager.colors["outline"])
            )
            return

        categorized = self.catalogue

        for category in sorted(categorized.keys()):
            outfits = categorized[category]
            is_expanded = (category == self.selected_category)

            # Category Header
            outfit_count = len(outfits)
            cat_tile = ft.Container(
                content=ft.Row([
                    ft.Icon(
                        ft.Icons.KEYBOARD_ARROW_DOWN if is_expanded else ft.Icons.KEYBOARD_ARROW_RIGHT,
                        size=18, color=ThemeManager.colors["text_secondary"],
                    ),
                    ft.Text(category, weight="bold" if is_expanded else "normal", size=13, expand=True),
                    ft.Container(
                        content=ft.Text(str(outfit_count), size=10, color=ThemeManager.colors["outline"]),
                        bgcolor=ThemeManager.colors["active_item"],
                        border_radius=10,
                        padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    ),
                ]),
                padding=ft.padding.symmetric(horizontal=5, vertical=8),
                border_radius=5,
                bgcolor=ThemeManager.colors["active_item"] if is_expanded else "transparent",
                on_click=self._create_category_click_handler(category),
            )
            self.tree_view_container.controls.append(cat_tile)

            # Outfit Items (only show if category is expanded)
            if is_expanded:
                for outfit_name in sorted(outfits.keys()):
                    is_selected = (outfit_name == self.selected_outfit)
                    is_current = (self.char_data and
                                  self.char_data.get("outfit") == outfit_name and
                                  self.char_data.get("outfit_category") == category)

                    slot_tile = ft.Container(
                        content=ft.Row([
                            ft.Icon(
                                ft.Icons.CHECK_CIRCLE if is_current else ft.Icons.CHECKROOM,
                                size=14,
                                color="green" if is_current else ThemeManager.colors["accent"],
                            ),
                            ft.Text(
                                outfit_name, size=12,
                                weight="bold" if is_selected else "normal",
                                color="green" if is_current else ThemeManager.colors["text_primary"],
                            ),
                        ]),
                        padding=ft.padding.only(left=28, top=5, bottom=5, right=5),
                        border_radius=5,
                        bgcolor=ThemeManager.colors["active_item"] if is_selected else "transparent",
                        on_click=self._create_outfit_click_handler(category, outfit_name),
                    )
                    self.tree_view_container.controls.append(slot_tile)

    def _create_category_click_handler(self, category):
        def handler(e):
            if self.selected_category == category:
                self.selected_category = None
            else:
                self.selected_category = category
            self.selected_outfit = None
            self.build_tree_view()
            self.build_detail_view()
            self._page_update()
        return handler

    def _create_outfit_click_handler(self, category, outfit_name):
        def handler(e):
            self.selected_category = category
            self.selected_outfit = outfit_name
            self.build_tree_view()
            self.build_detail_view()
            self._safe_update_preview()
            self._page_update()
        return handler

    # ──────────────────────────────────────────────
    # DETAIL VIEW
    # ──────────────────────────────────────────────

    def build_detail_view(self):
        """Renders the detail pane for the selected outfit."""
        self.detail_container.controls.clear()

        if not self.selected_category or not self.selected_outfit:
            self.detail_container.controls.append(
                ft.Container(
                    content=ft.Text(
                        "Select an outfit from the tree to see its details.",
                        color=ThemeManager.colors["outline"], italic=True,
                    ),
                    expand=True,
                )
            )
            return

        outfit_data = self.catalogue.get(self.selected_category, {}).get(self.selected_outfit, "")

        # Header breadcrumb
        is_current = (self.char_data and
                      self.char_data.get("outfit") == self.selected_outfit and
                      self.char_data.get("outfit_category") == self.selected_category)

        header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CHECKROOM, color=ThemeManager.colors["accent"]),
                ft.Text(f"{self.selected_category} > ", color=ThemeManager.colors["outline"], size=12),
                ft.Text(self.selected_outfit, weight="bold", size=18),
                ft.Container(
                    content=ft.Text("ACTIVE", size=10, color="white", weight="bold"),
                    bgcolor="green",
                    border_radius=4,
                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                    visible=is_current,
                ),
            ]),
            padding=ft.padding.only(bottom=10),
        )
        self.detail_container.controls.append(header)

        # Description Preview
        if isinstance(outfit_data, dict):
            desc = outfit_data.get("description", str(outfit_data))
            tags = outfit_data.get("tags", [])
            modifiers = outfit_data.get("modifiers", {})
        elif isinstance(outfit_data, str):
            desc = outfit_data
            tags = []
            modifiers = {}
        else:
            desc = str(outfit_data)
            tags = []
            modifiers = {}

        # Tags
        if tags:
            tag_chips = ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(t, size=10, color=ThemeManager.colors["text_secondary"]),
                        bgcolor=ThemeManager.colors["active_item"],
                        border_radius=4,
                        padding=ft.padding.symmetric(horizontal=8, vertical=3),
                    )
                    for t in tags
                ],
                wrap=True,
                spacing=5,
            )
            self.detail_container.controls.append(tag_chips)

        # Outfit Description (the actual markdown content)
        desc_label = ft.Text("Outfit Description", weight="bold", size=14,
                             color=ThemeManager.colors["text_secondary"])
        desc_display = ft.Container(
            content=ft.Text(
                desc if desc else "(No description)",
                size=13,
                selectable=True,
                font_family="Consolas",
                color=ThemeManager.colors["text_primary"],
            ),
            padding=15,
            border_radius=8,
            bgcolor=ThemeManager.colors["panel_bg"],
            border=ft.border.all(1, ThemeManager.colors["outline"]),
        )
        self.detail_container.controls.append(desc_label)
        self.detail_container.controls.append(desc_display)

        # Modifiers (if any)
        if modifiers:
            mod_label = ft.Text("Outfit Modifiers", weight="bold", size=14,
                                color=ThemeManager.colors["text_secondary"])
            self.detail_container.controls.append(mod_label)

            mod_chips = ft.Row(wrap=True, spacing=5)
            current_traits = self.char_data.get("outfit_traits", []) if self.char_data else []
            for mod_name, mod_desc in sorted(modifiers.items()):
                is_active = mod_name in current_traits
                chip = ft.Chip(
                    label=ft.Text(mod_name, size=11),
                    bgcolor=ThemeManager.colors["accent"] if is_active else ThemeManager.colors["active_item"],
                    on_click=self._create_modifier_toggle_handler(mod_name, not is_active),
                    padding=5,
                    shape=ft.RoundedRectangleBorder(radius=4),
                )
                mod_chips.controls.append(chip)

            self.detail_container.controls.append(mod_chips)

            # Show modifier descriptions
            for mod_name, mod_desc in sorted(modifiers.items()):
                is_active = mod_name in current_traits
                if is_active:
                    self.detail_container.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.AUTO_AWESOME, size=14, color="amber"),
                                ft.Text(f"{mod_name}: ", weight="bold", size=12),
                                ft.Text(mod_desc, size=12, color=ThemeManager.colors["text_secondary"]),
                            ]),
                            padding=ft.padding.only(left=10),
                        )
                    )

        # Quick Apply button within detail view
        self.detail_container.controls.append(ft.Divider(height=1, color=ThemeManager.colors["outline"]))
        if self.is_global_mode:
            apply_label = "Apply to All Rostered Characters"
        else:
            apply_label = f"Set as {self.char_name}'s Outfit" if self.char_name else "Apply"

        has_roster = len(self.app.state.state.get("selected_characters", [])) > 0
        apply_btn = ft.FilledButton(
            apply_label,
            icon=ft.Icons.CHECK if not self.is_global_mode else ft.Icons.DONE_ALL,
            on_click=self.handle_apply,
            disabled=(not has_roster or is_current) if not self.is_global_mode else (not has_roster),
            style=ft.ButtonStyle(
                bgcolor="green" if not is_current else ThemeManager.colors["active_item"],
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
        )
        self.detail_container.controls.append(apply_btn)

    def _create_modifier_toggle_handler(self, mod_name, new_state):
        def handler(e):
            if not self.char_data:
                return
            traits = self.char_data.get("outfit_traits", [])
            if new_state:
                if mod_name not in traits:
                    traits.append(mod_name)
            else:
                if mod_name in traits:
                    traits.remove(mod_name)
            self.char_data["outfit_traits"] = traits
            self.build_detail_view()
            self._safe_update_preview()
            self._page_update()
        return handler

    # ──────────────────────────────────────────────
    # PREVIEW
    # ──────────────────────────────────────────────

    def _safe_update_preview(self):
        """Update the prompt preview, catching errors during initialization."""
        if not self.char_data or not self.selected_outfit:
            text = "Select an outfit to preview."
        else:
            # Build a temporary config to get what the prompt would look like
            temp_char = dict(self.char_data)
            temp_char["outfit"] = self.selected_outfit
            temp_char["outfit_category"] = self.selected_category

            try:
                data = self.app.state.ctx.characters.get(temp_char["name"], {})
                outfit_raw = data.get("outfits", {}).get(self.selected_outfit, "")

                if isinstance(outfit_raw, dict):
                    desc = outfit_raw.get("description", "")
                else:
                    desc = str(outfit_raw) if outfit_raw else ""

                lines = [
                    f"Character: {temp_char['name']}",
                    f"Category: {self.selected_category}",
                    f"Outfit: {self.selected_outfit}",
                    "",
                    "--- Rendered Outfit ---",
                    desc if desc else "(No outfit description found)",
                ]
                text = "\n".join(lines)
            except Exception as ex:
                text = f"Preview error: {ex}"

        self.preview_text.value = text
        try:
            if self.preview_text.page:
                self.preview_text.update()
        except Exception:
            pass

    # ──────────────────────────────────────────────
    # ACTIONS
    # ──────────────────────────────────────────────

    def randomize_outfit(self):
        """Pick a random outfit from the catalogue."""
        if not self.catalogue:
            return
        all_outfits = []
        for cat, outfits in self.catalogue.items():
            for name in outfits:
                all_outfits.append((cat, name))

        if all_outfits:
            cat, name = random.choice(all_outfits)
            self.selected_category = cat
            self.selected_outfit = name
            self.build_tree_view()
            self.build_detail_view()
            self._safe_update_preview()
            self._page_update()

    def handle_apply(self, e=None):
        """Write the selected outfit back to char_data and refresh the roster."""
        if not self.selected_outfit or not self.selected_category:
            return

        chars = self.app.state.state.get("selected_characters", [])
        if not chars:
            return

        if self.is_global_mode:
            # Apply to ALL rostered characters
            count = 0
            for char in chars:
                char["outfit"] = self.selected_outfit
                char["outfit_category"] = self.selected_category
                char["outfit_traits"] = []
                count += 1
            self.app.show_toast(f"Applied '{self.selected_outfit}' to {count} characters!")
            self.app.roster.refresh()
        else:
            # Apply to specific character
            if not self.char_data:
                return
            self.char_data["outfit"] = self.selected_outfit
            self.char_data["outfit_category"] = self.selected_category
            self.char_data["outfit_traits"] = self.char_data.get("outfit_traits", [])
            self.app.roster.update_character_ui(self.character_index)
            self.app.show_toast(f"Applied '{self.selected_outfit}' to {self.char_name}!")

        self.app.update_preview()

        # Refresh the detail view to show the ACTIVE badge
        self.build_tree_view()
        self.build_detail_view()
        self._page_update()

    def handle_copy(self, e):
        try:
            self.app.page.set_clipboard(self.preview_text.value)
            self.app.show_toast("Copied to clipboard!")
        except Exception:
            self.app.show_toast("Clipboard not available.", color="red")

    def handle_close(self, e):
        self.app.close_dialog(self)

    def _page_update(self):
        try:
            if self.page:
                self.page.update()
        except Exception:
            pass
