import flet as ft
from core.flet_theme_manager import ThemeManager

class RosterItem(ft.Container):
    """
    A self-contained component representing a single character in the Roster.
    Supports 'surgical' updates to minimize re-renders.
    """
    def __init__(self, app, idx: int, char_data: Any, on_update_callback=None):
        super().__init__()
        self.app = app
        self.idx = idx
        self.char_data = char_data # SelectedCharacterConfig
        self.on_update_callback = on_update_callback # Callback to notify parent of changes
        
        self.padding = 0
        self.border_radius = ThemeManager.styles["radius"]
        self.border = ft.Border.all(1, ThemeManager.colors["outline"])
        self.clip_behavior = ft.ClipBehavior.HARD_EDGE
        
        # Internal State References for Surgical Updates
        self._refs = {}
        
        self.color_scheme_keys = sorted(self.app.state.ctx.color_schemes.keys())
        
        self.build_ui()
        self.sync_style()

    def build_ui(self):
        char_name = self.char_data.name
        char_info = self.app.state.ctx.characters.get(char_name)
        
        # --- Header ---
        self._refs["avatar_text"] = ft.Text(str(self.idx + 1), color="white", weight="bold", size=10)
        self._refs["avatar"] = ft.CircleAvatar(
            content=self._refs["avatar_text"],
            radius=12,
            bgcolor=self._get_avatar_color()
        )
        
        self._refs["summary"] = ft.Text(
            self.app.character_logic.get_character_summary(self.idx),
            size=11, color=ThemeManager.colors["text_secondary"],
            visible=not self.char_data._expanded,
            no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS
        )
        
        self._refs["toggle_icon"] = ft.Icon(
            ft.Icons.KEYBOARD_ARROW_DOWN if self.char_data._expanded else ft.Icons.KEYBOARD_ARROW_RIGHT,
            size=20, color=ThemeManager.colors["text_secondary"]
        )
        
        self._refs["header"] = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.DRAG_HANDLE, color=ThemeManager.colors["outline"], size=16),
                    self._refs["avatar"],
                    ft.Column([
                        ft.Row([
                            ft.Text(char_name, weight="bold", size=14, color=ThemeManager.colors["text_primary"]),
                            # [NEW] Meta Chips (Mini)
                            ft.Row([
                                ft.Container(content=ft.Text(char_info.age_presentation.upper() if char_info and char_info.age_presentation else "", size=8, color=ThemeManager.colors["text_secondary"]), padding=ft.padding.symmetric(6, 2), bgcolor=ft.Colors.with_opacity(0.1, ThemeManager.colors["text_secondary"]), border_radius=3) if char_info and char_info.age_presentation else ft.Container(),
                                ft.Container(content=ft.Text(char_info.vibe.upper() if char_info and char_info.vibe else "", size=8, color=ThemeManager.colors["accent"]), padding=ft.padding.symmetric(6, 2), bgcolor=ft.Colors.with_opacity(0.1, ThemeManager.colors["accent"]), border_radius=3) if char_info and char_info.vibe else ft.Container(),
                            ], spacing=5)
                        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        self._refs["summary"]
                    ], spacing=0, alignment=ft.MainAxisAlignment.CENTER)
                ], spacing=10),
                ft.Row([
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="red400", scale=0.8, 
                                  on_click=lambda e: self.app.remove_character(char_name)),
                    self._refs["toggle_icon"]
                ], spacing=0)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.Padding(10, 8, 10, 8),
            on_click=self.toggle_expanded,
            bgcolor=ThemeManager.colors["active_item"] if self.char_data._expanded else None,
            animate=ft.Animation(300, "easeOut")
        )

        # --- Details ---
        
        # 1. Identity Traits
        self._refs["identity_row"] = ft.Row(wrap=True, spacing=5)
        self._rebuild_identity_chips()

        # 2. Outfit Controls
        outfit_cats = sorted(char_info.outfits_categorized.keys()) if char_info else []
        curr_cat = self.char_data.outfit_category or (outfit_cats[0] if outfit_cats else "")
        
        # Dropdowns
        self._refs["outfit_cat_dd"] = ft.Dropdown(
            label="Category",
            options=[ft.dropdown.Option(c) for c in outfit_cats],
            value=curr_cat,
            expand=1,
            on_select=self.handle_outfit_cat_change,
            text_size=12, height=45, content_padding=10
        )
        
        self._refs["outfit_preset_dd"] = ft.Dropdown(
            label="Outfit",
            options=[], # Populated below
            value=self.char_data.outfit,
            expand=2,
            on_select=self.handle_outfit_preset_change,
             text_size=12, height=45, content_padding=10
        )
        
        self._update_outfit_options(curr_cat) # Populate options
        
        # 2b. Color Scheme (Conditional)
        self._refs["color_scheme_dd"] = ft.Dropdown(
            label="Team / Color Scheme",
            options=[ft.dropdown.Option(k) for k in self.color_scheme_keys],
            value=self.char_data.color_scheme or "The Standard",
            on_select=self.handle_color_scheme_change,
            text_size=12, height=45, content_padding=10,
            visible=False # Hidden by default, toggled by logic
        )

        # Modifiers
        self._refs["modifiers_row"] = ft.Row(wrap=True, spacing=5)
        self._rebuild_modifier_chips()

        pose_cats = sorted(self.app.state.ctx.poses.keys())
        curr_p_cat = self.char_data.pose_category or (pose_cats[0] if pose_cats else "")
        
        self._refs["pose_cat_dd"] = ft.Dropdown(
            label="Pose Category",
            options=[ft.dropdown.Option(c) for c in pose_cats],
            value=curr_p_cat,
            expand=1,
            on_select=self.handle_pose_cat_change,
            text_size=12, height=45, content_padding=10
        )
        
        self._refs["pose_preset_dd"] = ft.Dropdown(
            label="Pose Preset",
            options=[],
            value=self.char_data.pose_preset,
            expand=2,
            on_select=self.handle_pose_preset_change,
            text_size=12, height=45, content_padding=10
        )
        self._update_pose_options(curr_p_cat)

        self._refs["action_field"] = ft.TextField(
            label="Action / Pose Note (Override)",
            value=self.char_data.action_note or "",
            multiline=True, min_lines=1, max_lines=3, text_size=12,
            on_change=self.handle_action_change,
            content_padding=10
        )

        # 4. Footer Row
        self._refs["sig_checkbox"] = ft.Checkbox(
            label="Use Sig Color", 
            value=self.char_data.use_signature_color or False,
            on_change=self.handle_sig_toggle,
            label_style=ft.TextStyle(size=12)
        )
        
        footer = ft.Row([
            ft.Row([
                 ft.IconButton(ft.Icons.ARROW_UPWARD, icon_size=18, on_click=lambda _: self.app.character_logic.move_character(self.idx, -1) or self.app.refresh_roster(), tooltip="Move Up"),
                 ft.IconButton(ft.Icons.ARROW_DOWNWARD, icon_size=18, on_click=lambda _: self.app.character_logic.move_character(self.idx, 1) or self.app.refresh_roster(), tooltip="Move Down"),
            ]),
            ft.Row([
                self._refs["sig_checkbox"],
                ft.IconButton(ft.Icons.CHECKROOM, icon_color=ThemeManager.colors["accent"], on_click=lambda _: self.app.open_outfit_builder(character_index=self.idx), tooltip="Edit Outfit"),
                ft.IconButton(ft.Icons.CASINO, icon_color="amber", on_click=lambda _: self.app.handle_solo_randomize(self.idx), tooltip="Randomize This Character")
            ])
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        self._refs["detail_content"] = ft.Column([
            ft.Divider(height=1, color="white10"),
            self._refs["identity_row"],
            ft.Row([self._refs["outfit_cat_dd"], self._refs["outfit_preset_dd"]]),
            # Inject Conditional Scheme Dropdown
            self._refs["color_scheme_dd"], 
            self._refs["modifiers_row"],
            ft.Row([self._refs["pose_cat_dd"], self._refs["pose_preset_dd"]]),
            self._refs["action_field"],
            footer
        ], spacing=10)

        self._refs["detail_container"] = ft.Container(
            content=self._refs["detail_content"],
            padding=ft.Padding(10, 0, 10, 10),
            visible=self.char_data._expanded,
            animate_opacity=200
        )

        self.content = ft.Column([self._refs["header"], self._refs["detail_container"]], spacing=0)

    # --- Logic Helpers ---

    def _get_avatar_color(self):
        char_info = self.app.state.ctx.characters.get(self.char_data.name)
        sig_color = char_info.signature_color if char_info else None
        use_sig = self.char_data.use_signature_color or False
        
        if use_sig and sig_color:
            # Handle hex or named color
            return sig_color if str(sig_color).startswith("#") else sig_color
        return ThemeManager.colors["accent"]

    def _rebuild_identity_chips(self):
        char_info = self.app.state.ctx.characters.get(self.char_data.name)
        chips = []
        if char_info:
            for trait_name in sorted(char_info.traits.keys()):
                is_sel = trait_name in (self.char_data.character_traits or [])
                chips.append(ft.Chip(
                    label=ft.Text(trait_name, size=10),
                    bgcolor=ThemeManager.colors["accent"] if is_sel else ThemeManager.colors["active_item"],
                    on_click=lambda e, n=trait_name, s=is_sel: self.toggle_trait("character_traits", n, not s),
                    padding=5,
                    shape=ft.RoundedRectangleBorder(radius=4)
                ))
        self._refs["identity_row"].controls = chips
        self._refs["identity_row"].visible = len(chips) > 0

    def _rebuild_modifier_chips(self):
        char_info = self.app.state.ctx.characters.get(self.char_data.name)
        cat = self.char_data.outfit_category
        outfit = self.char_data.outfit
        # Find modifiers
        outfit_data = char_info.outfits_categorized.get(cat, {}).get(outfit, {}) if char_info else {}
        if isinstance(outfit_data, str) or not isinstance(outfit_data, dict): outfit_data = {}
        mods = outfit_data.get("modifiers", {}) if isinstance(outfit_data, dict) else {}
        
        chips = []
        for mn in sorted(mods.keys()):
             is_sel = mn in (self.char_data.outfit_traits or [])
             chips.append(ft.Chip(
                label=ft.Text(mn, size=10),
                bgcolor=ThemeManager.colors["accent"] if is_sel else ThemeManager.colors["active_item"],
                on_click=lambda e, n=mn, s=is_sel: self.toggle_trait("outfit_traits", n, not s),
                padding=5,
                 shape=ft.RoundedRectangleBorder(radius=4)
            ))
        self._refs["modifiers_row"].controls = chips
        self._refs["modifiers_row"].visible = len(chips) > 0

    def _update_outfit_options(self, cat):
        char_info = self.app.state.ctx.characters.get(self.char_data.name)
        outfits = sorted(char_info.outfits_categorized.get(cat, {}).keys()) if char_info else []
        self._refs["outfit_preset_dd"].options = [ft.dropdown.Option(o) for o in outfits]

    def _update_pose_options(self, cat):
        if not cat: 
             self._refs["pose_preset_dd"].options = []
             return
        presets = sorted(self.app.state.ctx.poses.get(cat, {}).keys())
        self._refs["pose_preset_dd"].options = [ft.dropdown.Option(p) for p in presets]

    def sync_style(self):
        self.bgcolor = ThemeManager.colors["panel_bg"] if self.idx % 2 == 0 else ft.Colors.with_opacity(0.5, ThemeManager.colors["surface"])
        self.border.color = ThemeManager.colors["outline"]

    # --- Handlers ---

    def toggle_expanded(self, e=None):
        current = self.char_data._expanded
        self.char_data._expanded = not current
        self.surgical_update()

    def handle_outfit_cat_change(self, e):
        new_cat = e.control.value

        self.char_data.outfit_category = new_cat
        # Default to first outfit
        char_info = self.app.state.ctx.characters.get(self.char_data.name)
        outfits = sorted(char_info.outfits_categorized.get(new_cat, {}).keys()) if char_info else []
        self.char_data.outfit = outfits[0] if outfits else "Base"

        self.char_data.outfit_traits = []
        
        self.surgical_update()
        if self.on_update_callback: self.on_update_callback()

    def handle_outfit_preset_change(self, e):
        val = e.control.value

        self.char_data.outfit = val
        self.char_data.outfit_traits = []
        self.surgical_update() # To rebuild modifiers
        if self.on_update_callback: self.on_update_callback()

    def handle_pose_cat_change(self, e):
        val = e.control.value

        self.char_data.pose_category = val
        
        # Pick default preset
        presets = sorted(self.app.state.ctx.poses.get(val, {}).keys())
        self.char_data.pose_preset = presets[0] if presets else "Default"
        
        self.surgical_update()
        if self.on_update_callback: self.on_update_callback()

    def handle_pose_preset_change(self, e):
        val = e.control.value

        self.char_data.pose_preset = val
        if self.on_update_callback: self.on_update_callback()

    def handle_action_change(self, e):
        self.char_data.action_note = e.control.value
        if self.on_update_callback: self.on_update_callback()

    def handle_sig_toggle(self, e):
        self.char_data.use_signature_color = e.control.value
        self.surgical_update() # Update avatar
        if self.on_update_callback: self.on_update_callback()

    def toggle_trait(self, key, trait, selected):
        current = getattr(self.char_data, key, [])
        if selected:
            if trait not in current: current.append(trait)
        else:
            if trait in current: current.remove(trait)
        setattr(self.char_data, key, current)
        self.surgical_update() # Rebuild chips
        if self.on_update_callback: self.on_update_callback()

    def _supports_color_scheme(self):
        """Check if current outfit supports color substitution."""
        char_info = self.app.state.ctx.characters.get(self.char_data.name)
        cat = self.char_data.outfit_category
        outfit = self.char_data.outfit
        if not cat or not outfit or not char_info: return False
        
        outfit_data = char_info.outfits_categorized.get(cat, {}).get(outfit, "")
        
        # Convert outfit data to a checkable string
        outfit_str = ""
        if isinstance(outfit_data, dict):
            outfit_str = " ".join(str(v) for k, v in outfit_data.items() if isinstance(v, str))
        else:
            outfit_str = str(outfit_data)
        
        # Check for placeholders
        return any(x in outfit_str for x in ["{team}", "{primary_color}", "{secondary_color}", "{accent}"])

    def handle_color_scheme_change(self, e):
        val = e.control.value

        self.char_data.color_scheme = val
        if self.on_update_callback: self.on_update_callback()

    # --- Surgical Update ---

    def surgical_update(self):
        """Update just this component's UI based on char_data state."""
        
        # 1. Header & Summary
        expanded = self.char_data._expanded
        self._refs["header"].bgcolor = ThemeManager.colors["active_item"] if expanded else None
        self._refs["toggle_icon"].name = ft.Icons.KEYBOARD_ARROW_DOWN if expanded else ft.Icons.KEYBOARD_ARROW_RIGHT
        
        self._refs["summary"].visible = not expanded
        self._refs["summary"].value = self.app.character_logic.get_character_summary(self.idx)
        
        self._refs["detail_container"].visible = expanded
        
        # 2. Avatar
        self._refs["avatar"].bgcolor = self._get_avatar_color()
        
        # 3. Inputs
        self._refs["outfit_cat_dd"].value = self.char_data.outfit_category
        self._refs["outfit_preset_dd"].value = self.char_data.outfit
        # Ensure options are correct for current category
        self._update_outfit_options(self.char_data.outfit_category)
        
        # Explicitly update dropdowns to ensure options refresh visually
        self._refs["outfit_cat_dd"].update()
        self._refs["outfit_preset_dd"].update()
        
        # Update Color Scheme Visibility
        supports_scheme = self._supports_color_scheme()
        self._refs["color_scheme_dd"].visible = supports_scheme
        self._refs["color_scheme_dd"].value = self.char_data.color_scheme or "The Standard"
        self._refs["color_scheme_dd"].update()
        
        # Update Pose Controls
        self._refs["pose_cat_dd"].value = self.char_data.pose_category
        self._refs["pose_preset_dd"].value = self.char_data.pose_preset
        self._update_pose_options(self.char_data.pose_category)
        
        self._refs["pose_cat_dd"].update()
        self._refs["pose_preset_dd"].update()

        self._refs["action_field"].value = self.char_data.action_note
        self._refs["action_field"].update()

        self._refs["sig_checkbox"].value = self.char_data.use_signature_color
        self._refs["sig_checkbox"].update()
        
        # 4. Chips (Rebuild)
        self._rebuild_identity_chips()
        self._rebuild_modifier_chips()
        
        self.update() # Update the container itself for structural changes

