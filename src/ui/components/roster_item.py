import flet as ft
from typing import Any
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
        
        self.padding = ft.Padding.all(8)
        self.border_radius = ft.BorderRadius.all(ThemeManager.styles["radius"])
        self.border = ft.Border.all(1, ft.Colors.with_opacity(0.1, ThemeManager.colors["text_primary"]))
        self.clip_behavior = ft.ClipBehavior.ANTI_ALIAS
        self.shadow = ThemeManager.styles.get("shadow_md", ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK)))
        
        # Internal State References for Surgical Updates
        self._refs = {}
        
        self.color_scheme_keys = sorted(self.app.state.ctx.color_schemes.keys()) if hasattr(self.app, 'state') and hasattr(self.app.state, 'ctx') else []
        self.build_ui()
        self.sync_style()
        
    def _get_val(self, key, default=None):
        """Helper to get value from self.char_data which might be an object or a dict."""
        if hasattr(self.char_data, key):
            return getattr(self.char_data, key)
        if isinstance(self.char_data, dict):
            return self.char_data.get(key, default)
        return default

    def _set_val(self, key, value):
        """Helper to set value on self.char_data which might be an object or a dict."""
        if hasattr(self.char_data, key):
            setattr(self.char_data, key, value)
        elif isinstance(self.char_data, dict):
            self.char_data[key] = value

    def build_ui(self):
        char_name = self._get_val("name")
        char_info = self.app.state.ctx.characters.get(char_name)
        char_meta = self.app.state.ctx.characters_metadata.get(char_name) if hasattr(self.app.state, "ctx") else None
        
        # Resolve signature color
        sig_color = None
        if char_info:
            sig_color = getattr(char_info, "signature_color", None) if not isinstance(char_info, dict) else char_info.get("signature_color")
        if not sig_color and char_meta:
            sig_color = getattr(char_meta, "signature_color", None) if not isinstance(char_meta, dict) else char_meta.get("signature_color")

        sig_dot = ft.Container(
            width=10, height=10, border_radius=5, bgcolor=sig_color,
            tooltip=f"Signature Color: {sig_color}",
            border=ft.Border.all(1, ft.Colors.WHITE_24)
        ) if sig_color else ft.Container()
        
        # --- Header ---
        self._refs["avatar_text"] = ft.Text(str(self.idx + 1), color="white", weight="bold", size=10)
        self._refs["avatar"] = ft.CircleAvatar(
            content=self._refs["avatar_text"],
            radius=12,
            bgcolor=self._get_avatar_color()
        )
        
        expanded = self._get_val("_expanded", False)
        
        self._refs["summary"] = ft.Text(
            self.app.character_logic.get_character_summary(self.idx) if hasattr(self.app, "character_logic") else "SUMMARY",
            size=11, color=ThemeManager.colors["text_secondary"],
            visible=not expanded,
            no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS
        )
        
        self._refs["toggle_icon"] = ft.Icon(
            ft.Icons.KEYBOARD_ARROW_DOWN if expanded else ft.Icons.KEYBOARD_ARROW_RIGHT,
            size=20, color=ThemeManager.colors["text_secondary"]
        )
        
        self._refs["header"] = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.DRAG_HANDLE, color=ThemeManager.colors["text_secondary"], size=18),
                    self._refs["avatar"],
                    ft.Column([
                        ft.Row([
                            ft.Text(char_name, weight=ft.FontWeight.BOLD, size=15, color=ThemeManager.colors["text_primary"]),
                            sig_dot,
                            # [NEW] Meta Chips (Mini)
                            ft.Row([
                                ft.Container(content=ft.Text((getattr(char_info, "age_presentation", "") if not isinstance(char_info, dict) else char_info.get("age_presentation", "")).upper() if (getattr(char_info, "age_presentation", "") if not isinstance(char_info, dict) else char_info.get("age_presentation", "")) else "", size=9, weight=ft.FontWeight.W_600, color=ThemeManager.colors["text_secondary"]), padding=ft.Padding.symmetric(horizontal=8, vertical=4), bgcolor=ft.Colors.with_opacity(0.1, ThemeManager.colors["text_secondary"]), border_radius=6) if (getattr(char_info, "age_presentation", "") if not isinstance(char_info, dict) else char_info.get("age_presentation", "")) else ft.Container(),
                                ft.Container(content=ft.Text((getattr(char_info, "vibe", "") if not isinstance(char_info, dict) else char_info.get("vibe", "")).upper() if (getattr(char_info, "vibe", "") if not isinstance(char_info, dict) else char_info.get("vibe", "")) else "", size=9, weight=ft.FontWeight.W_600, color=ThemeManager.colors["accent"]), padding=ft.Padding.symmetric(horizontal=8, vertical=4), bgcolor=ft.Colors.with_opacity(0.1, ThemeManager.colors["accent"]), border_radius=6) if (getattr(char_info, "vibe", "") if not isinstance(char_info, dict) else char_info.get("vibe", "")) else ft.Container(),
                            ], spacing=8)
                        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        self._refs["summary"]
                    ], spacing=2, alignment=ft.MainAxisAlignment.CENTER)
                ], spacing=15),
                ft.Row([
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ThemeManager.colors["error"], scale=0.9, 
                                  on_click=lambda e: self.app.remove_character(char_name)),
                    self._refs["toggle_icon"]
                ], spacing=5)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.Padding.all(12),
            on_click=self.toggle_expanded,
            bgcolor=ThemeManager.colors["active_item"] if expanded else ft.Colors.with_opacity(0.3, ThemeManager.colors["panel_bg"]),
            border_radius=ft.BorderRadius.all(ThemeManager.styles["radius"]),
            animate=ft.Animation(400, ft.AnimationCurve.EASE_OUT_EXPO)
        )

        # --- Details ---
        
        # 1. Identity Traits
        self._refs["identity_row"] = ft.Row(wrap=True, spacing=5)
        self._rebuild_identity_chips()

        # 2. Outfit Selector Row (Inline Dropdown + Advanced Builder Button)
        outfit_options = self._get_outfit_options()
        curr_cat = self._get_val('outfit_category', 'Personal')
        curr_out = self._get_val('outfit', 'Base')
        curr_key = f"{curr_cat}::{curr_out}"
        if curr_key not in [o.key for o in outfit_options]:
            outfit_options.insert(0, ft.dropdown.Option(key=curr_key, text=f"{curr_out} ({curr_cat})"))

        self._refs["outfit_dd"] = ft.Dropdown(
            label="Outfit Preset",
            options=outfit_options,
            value=curr_key,
            on_select=self.handle_outfit_select,
            text_size=11, height=40, content_padding=8,
            expand=True,
            border_color=ThemeManager.colors["outline"],
            focused_border_color=ThemeManager.colors["accent"],
        )
        self._refs["outfit_display_text"] = ft.Text(
            f"{curr_cat} > {curr_out}",
            size=12, weight="bold", color=ThemeManager.colors["text_primary"]
        )
        self._refs["outfit_display"] = ft.Row([
            ft.Icon(ft.Icons.CHECKROOM, size=18, color=ThemeManager.colors["accent"]),
            self._refs["outfit_dd"],
            ft.IconButton(
                icon=ft.Icons.TUNE,
                icon_color=ThemeManager.colors["accent"],
                tooltip="Advanced Layer Editor (Outfit Builder Studio)",
                on_click=lambda _: self.app.open_outfit_builder(character_index=self.idx),
                scale=0.9
            )
        ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        
        # 2b. Color Scheme (Conditional)
        self._refs["color_scheme_dd"] = ft.Dropdown(
            label="Team / Color Scheme",
            options=[ft.dropdown.Option(k) for k in self.color_scheme_keys],
            value=self.char_data.color_scheme or "The Standard",
            on_select=self.handle_color_scheme_change,
            text_size=11, height=38, content_padding=8,
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
            text_size=11, height=38, content_padding=8
        )
        
        self._refs["pose_preset_dd"] = ft.Dropdown(
            label="Pose Preset",
            options=[],
            value=self.char_data.pose_preset,
            expand=2,
            on_select=self.handle_pose_preset_change,
            text_size=11, height=38, content_padding=8
        )
        self._update_pose_options(curr_p_cat)

        self._refs["action_field"] = ft.TextField(
            label="Action / Pose Note (Override)",
            value=self.char_data.action_note or "",
            multiline=True, min_lines=1, max_lines=2, text_size=11,
            on_change=self.handle_action_change,
            content_padding=8
        )

        # 4. Footer Row
        sig_swatch = ft.Container(
            width=12, height=12, border_radius=6, bgcolor=sig_color or "#888888",
            border=ft.Border.all(1, ft.Colors.WHITE_38),
            tooltip=f"Signature: {sig_color or 'None'}"
        ) if sig_color else ft.Container()

        self._refs["sig_checkbox"] = ft.Checkbox(
            label="Use Sig Color", 
            value=self.char_data.use_signature_color or False,
            on_change=self.handle_sig_toggle,
            label_style=ft.TextStyle(size=11)
        )
        
        footer = ft.Row([
            ft.Row([
                 ft.IconButton(ft.Icons.ARROW_UPWARD, icon_size=16, on_click=lambda _: self.app.character_logic.move_character(self.idx, -1) or self.app.refresh_roster(), tooltip="Move Up"),
                 ft.IconButton(ft.Icons.ARROW_DOWNWARD, icon_size=16, on_click=lambda _: self.app.character_logic.move_character(self.idx, 1) or self.app.refresh_roster(), tooltip="Move Down"),
            ], spacing=2),
            ft.Row([
                sig_swatch,
                self._refs["sig_checkbox"],
                ft.IconButton(ft.Icons.CASINO, icon_color="amber", icon_size=18, on_click=lambda _: self.app.handle_solo_randomize(self.idx), tooltip="Randomize This Character")
            ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        self.traits_tile = ft.ExpansionTile(
            title=ft.Text("Traits & Modifiers", size=12, weight=ft.FontWeight.BOLD),
            leading=ft.Icon(ft.Icons.DENSITY_MEDIUM, size=15, color=ThemeManager.colors["accent"]),
            expanded=False,
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Text("IDENTITY TRAITS", size=10, weight=ft.FontWeight.W_700, color=ThemeManager.colors["text_secondary"]),
                        self._refs["identity_row"],
                        ft.Divider(height=6, color=ft.Colors.TRANSPARENT),
                        ft.Text("OUTFIT MODIFIERS", size=10, weight=ft.FontWeight.W_700, color=ThemeManager.colors["text_secondary"]),
                        self._refs["modifiers_row"]
                    ], spacing=4),
                    padding=ft.Padding.symmetric(vertical=6)
                )
            ]
        )

        self._refs["detail_content"] = ft.Column([
            ft.Divider(height=1, color=ft.Colors.with_opacity(0.1, ThemeManager.colors["text_primary"])),
            self._refs["outfit_display"],
            # Inject Conditional Scheme Dropdown
            self._refs["color_scheme_dd"], 
            self.traits_tile,
            ft.Row([self._refs["pose_cat_dd"], self._refs["pose_preset_dd"]], spacing=8),
            self._refs["action_field"],
            ft.Container(footer, padding=ft.Padding.only(top=2))
        ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

        self._refs["detail_container"] = ft.Container(
            content=self._refs["detail_content"],
            padding=ft.Padding.only(left=8, right=8, bottom=8, top=4),
            visible=expanded,
            animate_opacity=400
        )

        self.content = ft.Column([self._refs["header"], self._refs["detail_container"]], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    # --- Logic Helpers ---

    def _get_avatar_color(self):
        char_name = self._get_val("name")
        char_info = self.app.state.ctx.characters.get(char_name)
        sig_color = (char_info.signature_color if hasattr(char_info, "signature_color") else char_info.get("signature_color")) if char_info else None
        use_sig = self._get_val("use_signature_color", False)
        
        if use_sig and sig_color:
            # Handle hex or named color
            return sig_color if str(sig_color).startswith("#") else sig_color
        return ThemeManager.colors["accent"]

    def _rebuild_identity_chips(self):
        char_name = self._get_val("name")
        char_info = self.app.state.ctx.characters.get(char_name)
        chips = []
        if char_info:
            traits = char_info.traits if hasattr(char_info, "traits") else char_info.get("traits", {})
            for trait_name in sorted(traits.keys()):
                char_traits = self._get_val("character_traits", [])
                is_sel = trait_name in (char_traits or [])
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
             is_sel = mn in (self._get_val("outfit_traits", []) or [])
             chips.append(ft.Chip(
                label=ft.Text(mn, size=10),
                bgcolor=ThemeManager.colors["accent"] if is_sel else ThemeManager.colors["active_item"],
                on_click=lambda e, n=mn, s=is_sel: self.toggle_trait("outfit_traits", n, not s),
                padding=5,
                 shape=ft.RoundedRectangleBorder(radius=4)
            ))
        self._refs["modifiers_row"].controls = chips
        self._refs["modifiers_row"].visible = len(chips) > 0


    def _update_pose_options(self, cat):
        if not cat: 
             self._refs["pose_preset_dd"].options = []
             return
        presets = sorted(self.app.state.ctx.poses.get(cat, {}).keys())
        self._refs["pose_preset_dd"].options = [ft.dropdown.Option(p) for p in presets]

    def sync_style(self):
        self.bgcolor = ThemeManager.colors["surface_variant"] if self.idx % 2 == 0 else ThemeManager.colors["surface"]
        self.border.color = ft.Colors.with_opacity(0.1, ThemeManager.colors["text_primary"])

    # --- Handlers ---

    def _get_outfit_options(self):
        char_name = self._get_val("name")
        char_info = self.app.state.ctx.characters.get(char_name) if hasattr(self.app, "state") and hasattr(self.app.state, "ctx") else None
        if not char_info:
            return [ft.dropdown.Option(key="Personal::Base", text="Base (Personal)")]
        oc = getattr(char_info, "outfits_categorized", None)
        if not isinstance(oc, dict):
            oc = char_info.get("outfits_categorized", {}) if isinstance(char_info, dict) else {}
        options = []
        for cat in sorted(oc.keys()):
            for out_name in sorted(oc[cat].keys()):
                key = f"{cat}::{out_name}"
                options.append(ft.dropdown.Option(key=key, text=f"{out_name} ({cat})"))
        if not options:
            options.append(ft.dropdown.Option(key="Personal::Base", text="Base (Personal)"))
        return options

    def handle_outfit_select(self, e):
        val = e.control.value
        if not val or "::" not in val:
            return
        cat, out_name = val.split("::", 1)
        self._set_val("outfit_category", cat)
        self._set_val("outfit", out_name)
        self._set_val("outfit_pieces", {})
        self._set_val("outfit_traits", [])
        self.surgical_update()
        if self.on_update_callback:
            self.on_update_callback()
        if hasattr(self.app, "update_preview"):
            self.app.update_preview()

    def toggle_expanded(self, e=None):
        current = self._get_val("_expanded", False)
        self._set_val("_expanded", not current)
        self.surgical_update()



    def handle_pose_cat_change(self, e):
        val = e.control.value

        self._set_val("pose_category", val)
        
        # Pick default preset
        presets = sorted(self.app.state.ctx.poses.get(val, {}).keys())
        self._set_val("pose_preset", presets[0] if presets else "Default")
        
        self.surgical_update()
        if self.on_update_callback: self.on_update_callback()

    def handle_pose_preset_change(self, e):
        val = e.control.value

        self._set_val("pose_preset", val)
        if self.on_update_callback: self.on_update_callback()

    def handle_action_change(self, e):
        self._set_val("action_note", e.control.value)
        if self.on_update_callback: self.on_update_callback()

    def handle_sig_toggle(self, e):
        self._set_val("use_signature_color", e.control.value)
        self.surgical_update() # Update avatar
        if self.on_update_callback: self.on_update_callback()

    def toggle_trait(self, key, trait, selected):
        current = self._get_val(key, [])
        if selected:
            if trait not in current: current.append(trait)
        else:
            if trait in current: current.remove(trait)
        self._set_val(key, current)
        self.surgical_update() # Rebuild chips
        if self.on_update_callback: self.on_update_callback()

    def _supports_color_scheme(self):
        """Check if current outfit supports color substitution."""
        char_info = self.app.state.ctx.characters.get(self._get_val("name"))
        cat = self._get_val("outfit_category")
        outfit = self._get_val("outfit")
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

        self._set_val("color_scheme", val)
        if self.on_update_callback: self.on_update_callback()

    # --- Surgical Update ---

    def surgical_update(self):
        """Update just this component's UI based on char_data state."""
        
        # 1. Header & Summary
        expanded = self._get_val("_expanded", False)
        self._refs["header"].bgcolor = ThemeManager.colors["active_item"] if expanded else None
        self._refs["toggle_icon"].name = ft.Icons.KEYBOARD_ARROW_DOWN if expanded else ft.Icons.KEYBOARD_ARROW_RIGHT
        
        self._refs["summary"].visible = not expanded
        self._refs["summary"].value = (self.app.character_logic.get_character_summary(self.idx) 
                                       if hasattr(self.app, "character_logic") else "SUMMARY")
        
        self._refs["detail_container"].visible = expanded
        
        # 2. Avatar
        self._refs["avatar"].bgcolor = self._get_avatar_color()
        
        # 3. Inputs
        curr_cat = self._get_val('outfit_category', 'Category')
        curr_out = self._get_val('outfit', 'Base')
        curr_key = f"{curr_cat}::{curr_out}"
        self._refs["outfit_display_text"].value = f"{curr_cat} > {curr_out}"
        self._refs["outfit_display_text"].update()
        
        if "outfit_dd" in self._refs and self._refs["outfit_dd"]:
            opts = [o.key for o in self._refs["outfit_dd"].options]
            if curr_key not in opts:
                self._refs["outfit_dd"].options.insert(0, ft.dropdown.Option(key=curr_key, text=f"{curr_out} ({curr_cat})"))
            self._refs["outfit_dd"].value = curr_key
            self._refs["outfit_dd"].update()
        
        # Update Color Scheme Visibility
        supports_scheme = self._supports_color_scheme()
        self._refs["color_scheme_dd"].visible = supports_scheme
        self._refs["color_scheme_dd"].value = self._get_val("color_scheme") or "The Standard"
        self._refs["color_scheme_dd"].update()
        
        # Update Pose Controls
        self._refs["pose_cat_dd"].value = self._get_val("pose_category")
        self._refs["pose_preset_dd"].value = self._get_val("pose_preset")
        self._update_pose_options(self._get_val("pose_category"))
        
        self._refs["pose_cat_dd"].update()
        self._refs["pose_preset_dd"].update()

        self._refs["action_field"].value = self._get_val("action_note")
        self._refs["action_field"].update()

        self._refs["sig_checkbox"].value = self._get_val("use_signature_color")
        self._refs["sig_checkbox"].update()
        
        # 4. Chips (Rebuild)
        self._rebuild_identity_chips()
        self._rebuild_modifier_chips()
        
        self.update() # Update the container itself for structural changes

