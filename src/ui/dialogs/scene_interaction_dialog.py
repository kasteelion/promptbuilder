import flet as ft
from core.flet_theme_manager import ThemeManager

class SceneInteractionDialog(ft.AlertDialog):
    """
    Tree + Detail selector for Scene Presets and Interaction Templates.
    Follows the Outfits Summary layout (Tree on Left, Detail & Preview on Right).
    """

    def __init__(self, app, initial_tab="scenes"):
        super().__init__()
        self.app = app
        self.active_tab = initial_tab  # "scenes" or "interactions"
        self.selected_category = None
        self.selected_preset_name = None
        self.search_filter = ""

        # UI Containers
        self.tree_container = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=4)
        self.detail_container = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=12)

        self.tab_selector = ft.SegmentedButton(
            selected=[self.active_tab],
            allow_multiple_selection=False,
            on_change=self.handle_tab_change,
            segments=[
                ft.Segment(
                    value="scenes",
                    label=ft.Text("Scenes", size=12, weight=ft.FontWeight.W_600),
                    icon=ft.Icon(ft.Icons.LANDSCAPE, size=15),
                ),
                ft.Segment(
                    value="interactions",
                    label=ft.Text("Interactions", size=12, weight=ft.FontWeight.W_600),
                    icon=ft.Icon(ft.Icons.PEOPLE_ALT, size=15),
                ),
            ],
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )

        self.search_field = ft.TextField(
            hint_text="Filter presets...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=self.handle_search,
            text_size=12,
            height=38,
            content_padding=8,
            border_radius=8,
            border_color=ThemeManager.colors["outline"],
            focused_border_color=ThemeManager.colors["accent"],
        )

        # Header
        header = ft.Row([
            ft.Row([
                ft.Icon(ft.Icons.ACCOUNT_TREE, color=ThemeManager.colors["accent"], size=22),
                ft.Text("Context Studio", size=18, weight=ft.FontWeight.BOLD),
            ], spacing=8),
            self.tab_selector,
            ft.IconButton(ft.Icons.CLOSE, on_click=lambda _: self.app.close_dialog(self)),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # Main Layout
        self.content = ft.Container(
            width=950,
            height=620,
            bgcolor=ft.Colors.with_opacity(0.95, ThemeManager.colors["surface"]),
            border_radius=14,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.15, ThemeManager.colors["outline"])),
            padding=16,
            content=ft.Column([
                header,
                ft.Divider(height=1, color=ft.Colors.with_opacity(0.12, ThemeManager.colors["outline"])),
                ft.Row([
                    # Left: Tree Categories
                    ft.Container(
                        width=280,
                        padding=ft.Padding.only(right=12),
                        border=ft.Border.only(right=ft.BorderSide(1, ft.Colors.with_opacity(0.1, ThemeManager.colors["outline"]))),
                        content=ft.Column([
                            self.search_field,
                            ft.Container(height=4),
                            self.tree_container,
                        ], expand=True, spacing=6),
                    ),
                    # Right: Detail & Preview Pane
                    ft.Container(
                        expand=True,
                        padding=ft.Padding.only(left=16),
                        content=self.detail_container,
                    )
                ], expand=True, spacing=0),
            ], expand=True, spacing=10),
        )

        self._init_defaults()
        self.build_tree()
        self.build_detail()

    def _init_defaults(self):
        ctx = getattr(self.app.state, "ctx", None)
        if not ctx:
            return

        if self.active_tab == "scenes":
            scenes = getattr(ctx, "scenes", {})
            cats = list(scenes.keys())
            if cats:
                current_cat = self.app.state.state.get("scene_category")
                self.selected_category = current_cat if current_cat in scenes else cats[0]
                presets = list(scenes[self.selected_category].keys())
                current_preset = self.app.state.state.get("scene_preset")
                self.selected_preset_name = current_preset if current_preset in presets else (presets[0] if presets else None)
        else:
            interactions = getattr(ctx, "interactions", {})
            cats = list(interactions.keys())
            if cats:
                current_cat = self.app.state.state.get("interaction_category")
                self.selected_category = current_cat if current_cat in interactions else cats[0]
                presets = list(interactions[self.selected_category].keys())
                current_preset = self.app.state.state.get("interaction_preset")
                self.selected_preset_name = current_preset if current_preset in presets else (presets[0] if presets else None)

    def handle_tab_change(self, e):
        selected = list(e.control.selected)
        if selected:
            self.active_tab = selected[0]
            self.search_filter = ""
            self.search_field.value = ""
            self._init_defaults()
            self.build_tree()
            self.build_detail()
            self.update()

    def handle_search(self, e):
        self.search_filter = (e.control.value or "").strip().lower()
        self.build_tree()
        self.update()

    def build_tree(self):
        self.tree_container.controls.clear()
        ctx = getattr(self.app.state, "ctx", None)
        if not ctx:
            return

        source = ctx.scenes if self.active_tab == "scenes" else ctx.interactions

        for cat_name, presets in sorted(source.items()):
            # Filter presets if search is active
            if self.search_filter:
                matching_presets = {
                    k: v for k, v in presets.items()
                    if self.search_filter in k.lower() or (
                        isinstance(v, dict) and self.search_filter in str(v.get("description", "")).lower()
                    ) or self.search_filter in cat_name.lower()
                }
                if not matching_presets and self.search_filter not in cat_name.lower():
                    continue
                display_presets = matching_presets
            else:
                display_presets = presets

            is_active_cat = (cat_name == self.selected_category)
            count = len(display_presets)

            # Category Header Tile
            cat_header = ft.Container(
                content=ft.Row([
                    ft.Row([
                        ft.Icon(
                            ft.Icons.FOLDER_OPEN if is_active_cat else ft.Icons.FOLDER,
                            size=16,
                            color=ThemeManager.colors["accent"] if is_active_cat else ThemeManager.colors["text_secondary"]
                        ),
                        ft.Text(
                            cat_name,
                            size=12,
                            weight=ft.FontWeight.W_600 if is_active_cat else ft.FontWeight.W_400,
                            color=ThemeManager.colors["text_primary"] if is_active_cat else ThemeManager.colors["text_secondary"],
                            no_wrap=True,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ], spacing=6, expand=True),
                    ft.Container(
                        content=ft.Text(str(count), size=10, weight=ft.FontWeight.BOLD, color=ThemeManager.colors["text_secondary"]),
                        padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                        bgcolor=ft.Colors.with_opacity(0.1, ThemeManager.colors["text_primary"]),
                        border_radius=8,
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.Padding.symmetric(horizontal=8, vertical=6),
                border_radius=6,
                bgcolor=ThemeManager.colors["active_item"] if is_active_cat else ft.Colors.TRANSPARENT,
                ink=True,
                on_click=lambda _, c=cat_name: self._select_category(c),
            )
            self.tree_container.controls.append(cat_header)

            # If selected category or searching, show child preset items
            if is_active_cat or self.search_filter:
                for p_name in sorted(display_presets.keys()):
                    is_selected_p = (p_name == self.selected_preset_name and cat_name == self.selected_category)
                    preset_item = ft.Container(
                        content=ft.Row([
                            ft.Icon(
                                ft.Icons.CHEVRON_RIGHT if is_selected_p else ft.Icons.RADIO_BUTTON_UNCHECKED,
                                size=12,
                                color=ThemeManager.colors["accent"] if is_selected_p else ThemeManager.colors["outline"]
                            ),
                            ft.Text(
                                p_name,
                                size=11,
                                weight=ft.FontWeight.W_600 if is_selected_p else ft.FontWeight.NORMAL,
                                color=ThemeManager.colors["text_primary"] if is_selected_p else ThemeManager.colors["text_secondary"],
                                no_wrap=True,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ], spacing=6),
                        padding=ft.Padding.only(left=20, top=4, bottom=4, right=8),
                        border_radius=4,
                        bgcolor=ft.Colors.with_opacity(0.12, ThemeManager.colors["accent"]) if is_selected_p else ft.Colors.TRANSPARENT,
                        ink=True,
                        on_click=lambda _, c=cat_name, p=p_name: self._select_preset(c, p),
                    )
                    self.tree_container.controls.append(preset_item)

    def _select_category(self, cat_name):
        self.selected_category = cat_name
        ctx = getattr(self.app.state, "ctx", None)
        source = ctx.scenes if self.active_tab == "scenes" else ctx.interactions
        presets = list(source.get(cat_name, {}).keys())
        self.selected_preset_name = presets[0] if presets else None
        self.build_tree()
        self.build_detail()
        self.update()

    def _select_preset(self, cat_name, preset_name):
        self.selected_category = cat_name
        self.selected_preset_name = preset_name
        self.build_tree()
        self.build_detail()
        self.update()

    def build_detail(self):
        self.detail_container.controls.clear()
        ctx = getattr(self.app.state, "ctx", None)
        if not ctx or not self.selected_category or not self.selected_preset_name:
            self.detail_container.controls.append(
                ft.Container(
                    content=ft.Text("Select a preset from the tree to view details.", size=13, color=ThemeManager.colors["text_secondary"]),
                    alignment=ft.Alignment(0, 0),
                    expand=True
                )
            )
            return

        source = ctx.scenes if self.active_tab == "scenes" else ctx.interactions
        preset_info = source.get(self.selected_category, {}).get(self.selected_preset_name)

        if isinstance(preset_info, dict):
            desc = preset_info.get("description", "")
            tags = preset_info.get("tags", [])
        else:
            desc = str(preset_info or "")
            tags = []

        # Category + Title Header
        tag_chips = [
            ft.Container(
                content=ft.Text(t, size=10, weight=ft.FontWeight.W_500, color=ThemeManager.colors["accent"]),
                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                border_radius=6,
                bgcolor=ft.Colors.with_opacity(0.1, ThemeManager.colors["accent"]),
                border=ft.Border.all(1, ft.Colors.with_opacity(0.2, ThemeManager.colors["accent"])),
            ) for t in tags
        ]

        title_section = ft.Column([
            ft.Row([
                ft.Container(
                    content=ft.Text(self.selected_category.upper(), size=10, weight=ft.FontWeight.W_700, color=ThemeManager.colors["text_secondary"]),
                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                    border_radius=4,
                    bgcolor=ft.Colors.with_opacity(0.08, ThemeManager.colors["text_primary"]),
                ),
            ]),
            ft.Text(self.selected_preset_name, size=20, weight=ft.FontWeight.BOLD, color=ThemeManager.colors["text_primary"]),
            ft.Row(tag_chips, wrap=True, spacing=6) if tag_chips else ft.Container(),
        ], spacing=6)

        # Description Card
        desc_markdown = ft.Markdown(
            desc if desc else "_No visual description provided._",
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_FLAVORED,
        )

        desc_card = ft.Container(
            content=desc_markdown,
            padding=14,
            border_radius=10,
            bgcolor=ThemeManager.colors["panel_bg"],
            border=ft.Border.all(1, ft.Colors.with_opacity(0.1, ThemeManager.colors["outline"])),
            expand=True,
        )

        # Apply Button
        apply_btn = ft.FilledButton(
            f"Apply Selected {'Scene' if self.active_tab == 'scenes' else 'Interaction'}",
            icon=ft.Icons.CHECK,
            on_click=self.handle_apply,
            style=ft.ButtonStyle(
                bgcolor=ThemeManager.colors["accent"],
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding.symmetric(horizontal=20, vertical=12),
            ),
        )

        self.detail_container.controls.extend([
            title_section,
            ft.Divider(height=1, color=ft.Colors.with_opacity(0.1, ThemeManager.colors["outline"])),
            desc_card,
            ft.Row([apply_btn], alignment=ft.MainAxisAlignment.END),
        ])

    def handle_apply(self, e):
        if self.active_tab == "scenes":
            self.app.state.state["scene_category"] = self.selected_category
            self.app.state.state["scene_preset"] = self.selected_preset_name
            if hasattr(self.app, "interaction_logic") and self.app.interaction_logic:
                desc = self.app.interaction_logic.process_scene_selection(self.selected_category, self.selected_preset_name)
                self.app.state.state["scene"] = desc
                if hasattr(self.app.sidebar, "scene_field"):
                    self.app.sidebar.scene_field.value = desc
            self.app.show_toast(f"Scene applied: {self.selected_preset_name}", color="green")
        else:
            self.app.state.state["interaction_category"] = self.selected_category
            self.app.state.state["interaction_preset"] = self.selected_preset_name
            if hasattr(self.app, "interaction_logic") and self.app.interaction_logic:
                template_data = self.app.interaction_logic.process_interaction_selection(self.selected_category, self.selected_preset_name)
                resolved = self.app.interaction_logic.resolve_interaction(template_data)
                self.app.state.state["notes"] = resolved
                if hasattr(self.app.sidebar, "notes_field"):
                    self.app.sidebar.notes_field.value = resolved
            self.app.show_toast(f"Interaction applied: {self.selected_preset_name}", color="green")

        if hasattr(self.app.sidebar, "populate_data"):
            self.app.sidebar.populate_data()
        self.app.update_preview()
        self.app.close_dialog(self)
