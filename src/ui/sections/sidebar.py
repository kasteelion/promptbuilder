import flet as ft
from ui.components.icon_button import SafeIconButton
from core.flet_theme_manager import ThemeManager
from utils.debouncer import Debouncer

class SidebarSection(ft.Container):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.debouncer = Debouncer(300) # 300ms Update Delay
        self.expand = True
        self.padding = ThemeManager.styles["padding"]
        self.border = ft.Border.all(1, ThemeManager.colors["outline"])
        self.border_radius = ft.BorderRadius.all(ThemeManager.styles["radius"])
        self.bgcolor = ThemeManager.colors["surface"]
        self.shadow = ThemeManager.styles.get("shadow_lg")
        
        # References for robust styling
        self.header_text = ft.Text("CONTEXT & SUMMARY", weight=ft.FontWeight.BOLD, size=18, color=ThemeManager.colors["text_primary"])
        self.summary_header = ft.Text("Live Summary", weight=ft.FontWeight.BOLD, size=15, color=ThemeManager.colors["text_primary"])
        
        # UI controls (Compact and responsive)
        self.scene_cat_dd = ft.Dropdown(label="Category", expand=1, text_size=11, height=40, content_padding=8)
        self.scene_cat_dd.on_select = self.handle_scene_cat_change
        
        self.scene_preset_dd = ft.Dropdown(label="Preset", expand=1, text_size=11, height=40, content_padding=8)
        self.scene_preset_dd.on_select = self.handle_scene_preset_change
        
        self.scene_browse_btn = ft.FilledButton(
            "Browse Scenes (Tree View)",
            icon=ft.Icons.ACCOUNT_TREE,
            on_click=lambda _: self.app.open_context_studio(initial_tab="scenes"),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                bgcolor=ThemeManager.colors["surface_variant"],
                color=ThemeManager.colors["text_primary"],
            ),
        )

        self.scene_field = ft.TextField(
            label="Scene Description", 
            multiline=True, 
            min_lines=3, 
            max_lines=6, 
            text_size=12,
            border_radius=8,
            content_padding=10,
            bgcolor=ft.Colors.with_opacity(0.1, ThemeManager.colors["text_primary"])
        )
        self.scene_field.on_change = self.handle_text_change
        
        self.interaction_cat_dd = ft.Dropdown(label="Category", expand=1, text_size=11, height=40, content_padding=8)
        self.interaction_cat_dd.on_select = self.handle_interaction_cat_change
        
        self.interaction_preset_dd = ft.Dropdown(label="Preset", expand=1, text_size=11, height=40, content_padding=8)
        self.interaction_preset_dd.on_select = self.handle_interaction_preset_change
        
        self.interaction_browse_btn = ft.FilledButton(
            "Browse Interactions (Tree View)",
            icon=ft.Icons.ACCOUNT_TREE,
            on_click=lambda _: self.app.open_context_studio(initial_tab="interactions"),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                bgcolor=ThemeManager.colors["surface_variant"],
                color=ThemeManager.colors["text_primary"],
            ),
        )

        self.notes_field = ft.TextField(
            label="Interactions/Notes", 
            multiline=True, 
            min_lines=3, 
            max_lines=6, 
            text_size=12,
            border_radius=8,
            content_padding=10,
            bgcolor=ft.Colors.with_opacity(0.1, ThemeManager.colors["text_primary"])
        )
        self.notes_field.on_change = self.handle_text_change
        
        self.summary_text = ft.Markdown(
            "No characters selected.", 
            extension_set=ft.MarkdownExtensionSet.GITHUB_FLAVORED,
            on_tap_link=lambda e: self.app.page.launch_url(e.data),
            selectable=True
        )
        
        self.summary_container = ft.Container(
            content=self.summary_text, 
            padding=15, 
            bgcolor=ThemeManager.colors["panel_bg"], 
            border_radius=ft.BorderRadius.all(10),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.05, ThemeManager.colors["text_primary"])),
            shadow=ThemeManager.styles.get("shadow_md")
        )
        
        # Quality / Alignment / Completeness Meter
        self.quality_bar = ft.ProgressBar(value=0, height=10, border_radius=10, color=ThemeManager.colors["accent"], bgcolor=ft.Colors.with_opacity(0.1, ThemeManager.colors["text_primary"]))
        self.quality_text = ft.Text(
            "Prompt Completeness: 0%", 
            size=12, 
            weight=ft.FontWeight.BOLD, 
            color=ThemeManager.colors["text_secondary"],
            tooltip="Measures prompt readiness across characters, wardrobe, scene, interactions, and color harmony."
        )
        
        # [NEW] Interactive Suggestions Panel (1-Click Recommendations)
        self.suggestions_column = ft.Column(spacing=6)
        self.suggestions_container = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.LIGHTBULB_OUTLINED, size=14, color=ThemeManager.colors["accent"]),
                    ft.Text("SMART SUGGESTIONS (1-Click)", size=10, weight=ft.FontWeight.W_700, color=ThemeManager.colors["text_secondary"]),
                ], spacing=6),
                self.suggestions_column,
            ], spacing=6),
            padding=ft.Padding.all(8),
            bgcolor=ft.Colors.with_opacity(0.15, ThemeManager.colors["surface"]),
            border_radius=8,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.12, ThemeManager.colors["outline"])),
            visible=False,
        )
        
        self.quality_meter = ft.Column([
            ft.Row([self.quality_text, ft.Icon(ft.Icons.INFO_OUTLINE, size=14, color=ThemeManager.colors["text_secondary"], tooltip="Prompt completeness and thematic cohesion across character traits, wardrobe, scene, and palette.")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            self.quality_bar,
            self.suggestions_container,
        ], spacing=8, visible=False)
        
        # Collapsible Scene & Interaction panels (Streamlined)
        self.scene_tile = ft.ExpansionTile(
            title=ft.Text("Scene Settings", size=13, weight=ft.FontWeight.BOLD),
            leading=ft.Icon(ft.Icons.LANDSCAPE, size=18, color=ThemeManager.colors["accent"]),
            expanded=True,
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Row([self.scene_browse_btn]),
                        ft.Row([self.scene_cat_dd, self.scene_preset_dd], spacing=8),
                        self.scene_field,
                    ], spacing=8),
                    padding=ft.Padding.symmetric(vertical=6)
                )
            ]
        )

        self.interaction_tile = ft.ExpansionTile(
            title=ft.Text("Interaction Notes", size=13, weight=ft.FontWeight.BOLD),
            leading=ft.Icon(ft.Icons.PEOPLE_ALT, size=18, color=ThemeManager.colors["accent"]),
            expanded=False,
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Row([self.interaction_browse_btn]),
                        ft.Row([self.interaction_cat_dd, self.interaction_preset_dd], spacing=8),
                        self.notes_field,
                    ], spacing=8),
                    padding=ft.Padding.symmetric(vertical=6)
                )
            ]
        )

        # Visual Art Style Chips (Single-click)
        self.base_prompt_chips = ft.Row(spacing=6, wrap=True)
        self.base_prompt_panel = ft.Container(
            content=ft.Column([
                ft.Text("ART STYLE", size=11, weight=ft.FontWeight.W_700, color=ThemeManager.colors["text_secondary"]),
                self.base_prompt_chips
            ], spacing=6),
            padding=ft.Padding.only(top=5, bottom=5)
        )

        # AI Scene Director Controls
        self.director_prompt = ft.TextField(
            label="Director's Vision (Optional)",
            hint_text="e.g. 'Coffee shop chat with maroon & khaki contrast', 'Sudden rainstorm', or leave empty...",
            multiline=True,
            min_lines=2,
            max_lines=3,
            text_size=12,
            content_padding=10,
            border_radius=8,
            border_color=ThemeManager.colors["outline"],
            focused_border_color=ThemeManager.colors["accent"],
            bgcolor=ft.Colors.with_opacity(0.1, ThemeManager.colors["text_primary"]),
        )
        self.direct_btn = ft.FilledButton(
            "🎬 Bring Scene to Life",
            icon=ft.Icons.AUTO_AWESOME,
            on_click=self.handle_direct_scene,
            style=ft.ButtonStyle(
                bgcolor=ThemeManager.colors["accent"],
                color="#ffffff",
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
        )
        self.director_status = ft.Text("", size=11, color=ThemeManager.colors["text_secondary"], italic=True)

        self.director_tile = ft.ExpansionTile(
            title=ft.Text("AI Scene Director", size=13, weight=ft.FontWeight.BOLD),
            leading=ft.Icon(ft.Icons.MOVIE_CREATION_OUTLINED, size=18, color=ThemeManager.colors["accent"]),
            subtitle=ft.Text("Brings characters together with narrative action & contrast", size=10, color=ThemeManager.colors["text_secondary"]),
            expanded=False,
            controls=[
                ft.Container(
                    content=ft.Column([
                        self.director_prompt,
                        ft.Row([self.direct_btn, self.director_status], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ], spacing=8),
                    padding=ft.Padding.symmetric(vertical=8),
                )
            ],
        )

        # Color Palette & Contrast Inspector
        self.palette_swatches_row = ft.Row(wrap=True, spacing=6)
        
        harmony_options = [
            ("Maroon & Khaki", "#800020", "#C3B091", "Autumn Casual Contrast"),
            ("Olive & Rust", "#556B2F", "#B7410E", "Earthy Warm Contrast"),
            ("Navy & Amber", "#001F3F", "#FFBF00", "Complementary Pop"),
            ("Charcoal & Mustard", "#36454F", "#E1AD01", "Urban High Contrast"),
            ("Emerald & Bronze", "#50C878", "#CD7F32", "Jewel Tone Elegance"),
            ("Sage & Terracotta", "#9DC183", "#E2725B", "Warm Muted Contrast"),
            ("Midnight & Crimson", "#0A0F24", "#990000", "Dramatic Noir"),
        ]

        def _make_harmony_pill(name, p, s, desc):
            return ft.Container(
                content=ft.Row([
                    ft.Container(width=10, height=10, border_radius=5, bgcolor=p),
                    ft.Container(width=10, height=10, border_radius=5, bgcolor=s),
                    ft.Text(name, size=11, weight=ft.FontWeight.W_500),
                ], spacing=6),
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                bgcolor=ft.Colors.with_opacity(0.08, ThemeManager.colors["text_primary"]),
                border_radius=6,
                border=ft.Border.all(1, ft.Colors.with_opacity(0.12, ThemeManager.colors["outline"])),
                ink=True,
                tooltip=f"{desc} (Click to apply across all characters in roster)",
                on_click=lambda _, n=name: self._apply_color_harmony_all(n),
            )

        harmony_chips = ft.Row([
            _make_harmony_pill(n, p, s, d) for (n, p, s, d) in harmony_options
        ], wrap=True, spacing=6)

        self.palette_tile = ft.ExpansionTile(
            title=ft.Text("Color Palette & Contrast", size=13, weight=ft.FontWeight.BOLD),
            leading=ft.Icon(ft.Icons.PALETTE_OUTLINED, size=18, color=ThemeManager.colors["accent"]),
            subtitle=ft.Text("Live wardrobe swatches and curated color harmonies", size=10, color=ThemeManager.colors["text_secondary"]),
            expanded=False,
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Text("ACTIVE PALETTE SWATCHES", size=10, weight=ft.FontWeight.W_700, color=ThemeManager.colors["text_secondary"]),
                        self.palette_swatches_row,
                        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                        ft.Text("QUICK COLOR HARMONIES (Click to apply)", size=10, weight=ft.FontWeight.W_700, color=ThemeManager.colors["text_secondary"]),
                        harmony_chips,
                    ], spacing=6),
                    padding=ft.Padding.symmetric(vertical=8),
                )
            ],
        )
        
        self.content = ft.Column([
            ft.Row([
                self.header_text,
                ft.Row([
                    SafeIconButton(ft.Icons.CASINO, tooltip="Global Randomize", on_click=self.app.handle_randomize, scale=0.9),
                    SafeIconButton("settings", tooltip="Dashboard", on_click=lambda _: self.app.show_dashboard(), scale=0.9)
                ], spacing=0)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            # Thematic Alignment Meter & Live Recommendations elevated to top of Sidebar
            ft.Container(self.quality_meter, padding=ft.Padding.only(top=2, bottom=4)),
            self.summary_container,
            ft.Divider(color=ft.Colors.with_opacity(0.1, ThemeManager.colors["outline"]), height=6),
            self.base_prompt_panel,
            self.palette_tile,
            self.scene_tile,
            self.interaction_tile,
            self.director_tile,
        ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=10)

    def populate_data(self):
        ctx = self.app.state.ctx
        
        # Art Style Chips
        base_prompts = ctx.base_prompts if isinstance(getattr(ctx, "base_prompts", None), dict) else {}
        current_style = self.app.state.state.get("base_prompt", "Detailed")
        if base_prompts:
            if current_style not in base_prompts:
                for k in base_prompts.keys():
                    if k.lower() in current_style.lower() or current_style.lower() in k.lower():
                        current_style = k
                        self.app.state.state["base_prompt"] = k
                        break
                else:
                    if "Studio Photorealism" in base_prompts:
                        current_style = "Studio Photorealism"
                    else:
                        current_style = list(base_prompts.keys())[0]
                    self.app.state.state["base_prompt"] = current_style
        else:
            current_style = "Detailed"

        self.base_prompt_chips.controls = []
        for style_name in sorted(base_prompts.keys()):
            is_selected = (style_name == current_style)
            self.base_prompt_chips.controls.append(
                ft.Chip(
                    label=ft.Text(style_name, size=11, weight=ft.FontWeight.W_600 if is_selected else ft.FontWeight.NORMAL),
                    selected=is_selected,
                    on_select=lambda e, n=style_name: self.handle_art_style_select(n),
                    selected_color=ThemeManager.colors["accent"],
                    show_checkmark=True,
                )
            )
        
        # Scene Categories
        self.scene_cat_dd.options = [ft.dropdown.Option(k) for k in sorted(ctx.scenes.keys())]
        self.scene_cat_dd.value = self.app.state.state.get("scene_category")
        
        # Scene Presets
        if self.scene_cat_dd.value:
            presets = ctx.scenes.get(self.scene_cat_dd.value, {})
            self.scene_preset_dd.options = [ft.dropdown.Option(k) for k in sorted(presets.keys())]
            self.scene_preset_dd.value = self.app.state.state.get("scene_preset")
        else:
            self.scene_preset_dd.options = []
            self.scene_preset_dd.value = None
        
        # Interaction Categories
        self.interaction_cat_dd.options = [ft.dropdown.Option(k) for k in sorted(ctx.interactions.keys())]
        self.interaction_cat_dd.value = self.app.state.state.get("interaction_category")
        
        # Interaction Presets
        if self.interaction_cat_dd.value:
            presets = ctx.interactions.get(self.interaction_cat_dd.value, {})
            self.interaction_preset_dd.options = [ft.dropdown.Option(k) for k in sorted(presets.keys())]
            self.interaction_preset_dd.value = self.app.state.state.get("interaction_preset")
        else:
            self.interaction_preset_dd.options = []
            self.interaction_preset_dd.value = None

        # Sync Fields
        self.scene_field.value = self.app.state.state.get("scene", "")
        self.notes_field.value = self.app.state.state.get("notes", "")

    def handle_art_style_select(self, name):
        """Update active art style in state and visual chip indicators."""
        self.app.state.state["base_prompt"] = name
        for ctrl in self.base_prompt_chips.controls:
            if isinstance(ctrl, ft.Chip):
                is_sel = (ctrl.label.value == name)
                ctrl.selected = is_sel
                ctrl.label.weight = ft.FontWeight.W_600 if is_sel else ft.FontWeight.NORMAL
        self.base_prompt_chips.update()
        self.app.update_preview()

    def handle_scene_cat_change(self, e):
        cat = e.control.value

        presets = self.app.state.ctx.scenes.get(cat, {})
        keys = sorted(presets.keys())
        
        self.scene_preset_dd.options = [ft.dropdown.Option(k) for k in keys]
        
        if keys:
            first_preset = keys[0]

            self.scene_preset_dd.value = first_preset
            self._apply_scene_preset(cat, first_preset)
        else:

            self.scene_preset_dd.value = None
            self.scene_field.value = ""
            self.app.state.state["scene"] = ""
            self.app.update_preview()
            self.scene_field.update()
            
        self.scene_preset_dd.update()
        self.update()

    def handle_scene_preset_change(self, e):
        cat = self.scene_cat_dd.value
        preset = e.control.value

        if cat and preset:
            self._apply_scene_preset(cat, preset)

    def _apply_scene_preset(self, cat, preset):
        self.app.state.state["scene_category"] = cat
        self.app.state.state["scene_preset"] = preset
        
        # Use InteractionLogic to resolve text
        description = self.app.interaction_logic.process_scene_selection(cat, preset)
        self.scene_field.value = description
        self.scene_field.update()
        
        self.app.state.state["scene"] = description
        self.app.update_preview() # Triggers page update

    def handle_interaction_cat_change(self, e):
        cat = e.control.value

        presets = self.app.state.ctx.interactions.get(cat, {})
        keys = sorted(presets.keys())
        
        self.interaction_preset_dd.options = [ft.dropdown.Option(k) for k in keys]
        
        if keys:
            first = keys[0]

            self.interaction_preset_dd.value = first
            self._apply_interaction_preset(cat, first)
        else:
            self.interaction_preset_dd.value = None
            self.notes_field.value = ""
            self.app.state.state["notes"] = ""
            self.app.update_preview()
            self.notes_field.update()
            
        self.interaction_preset_dd.update()
        self.update()

    def handle_interaction_preset_change(self, e):
        cat = self.interaction_cat_dd.value
        preset = e.control.value
        if cat and preset:
            self._apply_interaction_preset(cat, preset)

    def _apply_interaction_preset(self, cat, preset):
        self.app.state.state["interaction_category"] = cat
        self.app.state.state["interaction_preset"] = preset
        
        # Use InteractionLogic
        data = self.app.interaction_logic.process_interaction_selection(cat, preset)
        desc = data.get("description", "")
        
        # Resolve placeholders via logic
        selected_chars = self.app.state.state["selected_characters"]
        resolved_desc = self.app.interaction_logic.resolve_interaction(desc, selected_chars)
        
        # Sync Poses via logic
        self.app.interaction_logic.sync_poses_from_interaction(data, selected_chars)
        
        # Refresh Roster UI since sync_poses might have changed char state
        self.app.refresh_roster()
            
        self.notes_field.value = resolved_desc
        self.app.state.state["notes"] = resolved_desc
        self.notes_field.update()
        self.app.update_preview()

    def handle_text_change(self, e):
        """Debounced text update."""
        if self.debouncer:
             self.debouncer.debounce(self._process_text_change, e.control, e.control.value)
        else:
             self._process_text_change(e.control, e.control.value)

    def _process_text_change(self, control, value):
        """Execute the actual update after delay."""
        if control == self.scene_field:
            self.app.state.state["scene"] = value
        elif control == self.notes_field:
            self.app.state.state["notes"] = value
        
        # Update preview (generates prompt)
        self.app.update_preview()

    def update_summary(self, summary: str):
        # Calculate real alignment & completeness score across multi-dimensional prompt facets
        score = 0.0
        selected_chars = self.app.state.state.get("selected_characters", [])
        total_chars = len(selected_chars)
        if total_chars > 0:
            # 1. Base score for active characters in roster: 20%
            score = 0.20
            
            # 2. Art style active beyond Default: +5%
            base_prompt = self.app.state.state.get("base_prompt", "")
            if base_prompt and base_prompt not in ("Default", "None"):
                score += 0.05
                
            # 3. Scene context set: +25% base
            scene = (self.app.state.state.get("scene") or "").strip()
            if scene:
                score += 0.25
                # Bonus if scene matches character tags/vibes (+10%)
                char_tags = set()
                for char_cfg in selected_chars:
                    char_name = char_cfg.name if hasattr(char_cfg, "name") else char_cfg.get("name", "")
                    try:
                        details = self.app.state.data_loader.get_character_details(char_name)
                        for t in (details.tags or []):
                            char_tags.update(part.lower() for part in t.replace("_", " ").split() if len(part) > 2)
                        for field in [details.vibe, details.bearing]:
                            if field:
                                char_tags.update(w.strip(".,;").lower() for w in field.split() if len(w) > 3)
                    except Exception:
                        pass
                scene_lower = scene.lower()
                if any(t in scene_lower for t in char_tags):
                    score += 0.10
                    
            # 4. Wardrobe customization (non-Base outfit): +15% scaled by roster
            non_base = 0
            for c in selected_chars:
                outfit = getattr(c, "outfit", "Base") if hasattr(c, "outfit") else c.get("outfit", "Base")
                if outfit and outfit not in ("Base", "Default", ""):
                    non_base += 1
            if non_base > 0:
                score += 0.15 * (non_base / total_chars)
                
            # 5. Narrative interaction / Action notes: +15%
            notes = (self.app.state.state.get("notes") or "").strip()
            if notes:
                score += 0.15
                
            # 6. Color harmony or signature color coordination: +10%
            has_scheme = any(
                (getattr(c, "color_scheme", None) if hasattr(c, "color_scheme") else c.get("color_scheme"))
                not in (None, "", "The Standard", "Default (No Scheme)")
                for c in selected_chars
            )
            has_sig = any(
                (getattr(c, "use_signature_color", False) if hasattr(c, "use_signature_color") else c.get("use_signature_color", False))
                for c in selected_chars
            )
            if has_scheme or has_sig:
                score += 0.10
                
            score = min(max(score, 0.0), 1.0)
            
            self.quality_bar.value = score
            pct = int(score * 100)
            
            # Dynamic visual color based on prompt completeness
            if pct < 40:
                self.quality_bar.color = ft.Colors.AMBER_600
            elif pct < 75:
                self.quality_bar.color = ThemeManager.colors["accent"]
            else:
                self.quality_bar.color = ft.Colors.GREEN_400
                
            self.quality_text.value = f"Prompt Completeness: {pct}%"
            self.quality_meter.visible = True
            self._update_suggestions()
            
            # Stylize the summary text
            import re
            summary = re.sub(r"Character: ([\w\s]+)", r"👤 **\1**", summary)
            summary = re.sub(r"Outfit: ([\w\s]+)", r"👗 *\1*", summary)
            summary = re.sub(r"Scene: ([\w\s]+)", r"🎬 **\1**", summary)
        else:
            self.quality_meter.visible = False
            self.suggestions_container.visible = False
            summary = (
                "### 🚀 Get Started\n\n"
                "1. **Select characters** from the gallery above to add them to your active roster.\n"
                "2. **Choose an Art Style** and customize the Scene & Interactions above.\n"
                "3. **Customize outfits & poses** for each character by expanding their card in the roster.\n"
                "4. **Optimize your prompt** using the **Enhance with Gemma** button in the console.\n"
                "5. **Generate your image** using the **Generate Image** button!"
            )

        self.summary_text.value = summary
        try:
            self.summary_text.update()
            self.quality_meter.update()
        except Exception:
            pass
        self._update_palette_swatches()

    def _apply_color_harmony_all(self, scheme_name: str):
        selected_chars = self.app.state.state.get("selected_characters", [])
        if not selected_chars:
            self.app.show_toast("Add characters to roster first to apply color harmony!", color="orange")
            return
        for char in selected_chars:
            if hasattr(char, "color_scheme"):
                char.color_scheme = scheme_name
            elif isinstance(char, dict):
                char["color_scheme"] = scheme_name
        self.app.refresh_roster()
        self.app.update_preview()
        self._update_palette_swatches()
        self.app.show_toast(f"Applied '{scheme_name}' color harmony to all characters!", color="green")

    def _update_palette_swatches(self):
        selected_chars = self.app.state.state.get("selected_characters", [])
        swatches = []
        schemes_found = set()

        for c in selected_chars:
            c_name = c.name if hasattr(c, "name") else c.get("name", "")
            c_info = self.app.state.ctx.characters.get(c_name)
            c_meta = self.app.state.ctx.characters_metadata.get(c_name) if hasattr(self.app.state, "ctx") else None
            sig_color = None
            if c_info:
                sig_color = getattr(c_info, "signature_color", None) if not isinstance(c_info, dict) else c_info.get("signature_color")
            if not sig_color and c_meta:
                sig_color = getattr(c_meta, "signature_color", None) if not isinstance(c_meta, dict) else c_meta.get("signature_color")

            if sig_color:
                swatches.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Container(width=12, height=12, border_radius=6, bgcolor=sig_color, border=ft.Border.all(1, ft.Colors.WHITE_38)),
                            ft.Text(f"{c_name.split()[0]} ({sig_color})", size=10, weight=ft.FontWeight.W_500),
                        ], spacing=5),
                        padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                        bgcolor=ft.Colors.with_opacity(0.12, sig_color),
                        border_radius=12,
                        border=ft.Border.all(1, ft.Colors.with_opacity(0.25, sig_color)),
                        tooltip=f"{c_name}'s Signature Color: {sig_color}",
                    )
                )

            scheme = getattr(c, "color_scheme", None) if not isinstance(c, dict) else c.get("color_scheme")
            if scheme and scheme != "The Standard":
                schemes_found.add(scheme)

        for s_name in schemes_found:
            s_dict = self.app.state.ctx.color_schemes.get(s_name, {}) if hasattr(self.app.state, "ctx") else {}
            p = s_dict.get("primary_color") or s_dict.get("primary", "#ffffff")
            s = s_dict.get("secondary_color") or s_dict.get("secondary", "#000000")
            swatches.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(width=10, height=10, border_radius=5, bgcolor=p),
                        ft.Container(width=10, height=10, border_radius=5, bgcolor=s),
                        ft.Text(s_name, size=10, weight=ft.FontWeight.W_600),
                    ], spacing=4),
                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                    bgcolor=ft.Colors.with_opacity(0.12, ThemeManager.colors["accent"]),
                    border_radius=12,
                    border=ft.Border.all(1, ThemeManager.colors["outline"]),
                    tooltip=f"Active Scheme: {s_name} (Primary: {p}, Secondary: {s})",
                )
            )

        if not swatches:
            self.palette_swatches_row.controls = [
                ft.Text("Add characters or select a Color Harmony below to view palette contrast.", size=11, color=ThemeManager.colors["text_secondary"], italic=True)
            ]
        else:
            self.palette_swatches_row.controls = swatches

        try:
            self.palette_swatches_row.update()
        except Exception:
            pass

    def _update_suggestions(self):
        """Generate context-aware 1-click recommendations using SuggestionEngine."""
        from logic.suggestion_engine import SuggestionEngine

        suggestions = SuggestionEngine.get_suggestions(self.app.state)
        controls = []

        # 1. Suggested Scenes (Gap: missing scene or best aesthetic matches)
        if suggestions.get("scenes"):
            chips = []
            for item in suggestions["scenes"]:
                p = item.payload
                chips.append(
                    self._make_suggestion_chip(
                        ft.Icons.LANDSCAPE,
                        item.label,
                        f"Set Scene: {item.label} ({item.category})\n{item.description[:120]}...",
                        lambda _, pl=p: self._apply_suggested_scene(pl),
                    )
                )
            controls.append(
                ft.Column([
                    ft.Text("SUGGESTED SCENES:", size=9, weight=ft.FontWeight.W_700, color=ThemeManager.colors["text_secondary"]),
                    ft.Row(chips, wrap=True, spacing=4),
                ], spacing=3)
            )

        # 2. Suggested Multi-Character Interactions
        if suggestions.get("interactions"):
            chips = []
            for item in suggestions["interactions"]:
                p = item.payload
                chips.append(
                    self._make_suggestion_chip(
                        ft.Icons.HANDSHAKE,
                        item.label,
                        f"Interaction: {item.description[:140]}...",
                        lambda _, pl=p: self._apply_suggested_interaction(pl),
                    )
                )
            controls.append(
                ft.Column([
                    ft.Text("MULTI-CHARACTER DYNAMICS:", size=9, weight=ft.FontWeight.W_700, color=ThemeManager.colors["text_secondary"]),
                    ft.Row(chips, wrap=True, spacing=4),
                ], spacing=3)
            )

        # 3. Wardrobe / Outfit Matches
        if suggestions.get("outfits"):
            chips = []
            for item in suggestions["outfits"]:
                p = item.payload
                chips.append(
                    self._make_suggestion_chip(
                        ft.Icons.CHECKROOM,
                        item.label,
                        item.description,
                        lambda _, pl=p: self._apply_suggested_outfit(pl),
                    )
                )
            controls.append(
                ft.Column([
                    ft.Text("THEMATIC WARDROBE:", size=9, weight=ft.FontWeight.W_700, color=ThemeManager.colors["text_secondary"]),
                    ft.Row(chips, wrap=True, spacing=4),
                ], spacing=3)
            )

        # 4. Color Harmonies
        if suggestions.get("harmonies"):
            chips = []
            for item in suggestions["harmonies"]:
                p = item.payload
                name = p["scheme_name"]
                primary = p.get("primary", "#ffffff")
                secondary = p.get("secondary", "#000000")
                chips.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Container(width=8, height=8, border_radius=4, bgcolor=primary),
                            ft.Container(width=8, height=8, border_radius=4, bgcolor=secondary),
                            ft.Text(name, size=10, weight=ft.FontWeight.W_500, no_wrap=True),
                        ], spacing=4),
                        padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                        bgcolor=ft.Colors.with_opacity(0.12, ThemeManager.colors["text_primary"]),
                        border_radius=6,
                        border=ft.Border.all(1, ft.Colors.with_opacity(0.15, ThemeManager.colors["outline"])),
                        tooltip=f"Apply {name} across all characters",
                        ink=True,
                        on_click=lambda _, s=name: self._apply_color_harmony_all(s),
                    )
                )
            controls.append(
                ft.Column([
                    ft.Text("COORDINATED PALETTES:", size=9, weight=ft.FontWeight.W_700, color=ThemeManager.colors["text_secondary"]),
                    ft.Row(chips, wrap=True, spacing=4),
                ], spacing=3)
            )

        self.suggestions_column.controls = controls
        has_items = bool(controls)
        self.suggestions_container.visible = has_items

        try:
            self.suggestions_container.update()
        except Exception:
            pass

    def _make_suggestion_chip(self, icon, label, tooltip_text, on_click_fn):
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, size=12, color=ThemeManager.colors["accent"]),
                ft.Text(label, size=10, weight=ft.FontWeight.W_500, no_wrap=True),
            ], spacing=4),
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            bgcolor=ft.Colors.with_opacity(0.12, ThemeManager.colors["text_primary"]),
            border_radius=6,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.15, ThemeManager.colors["outline"])),
            tooltip=tooltip_text,
            ink=True,
            on_click=on_click_fn,
        )

    def _apply_suggested_scene(self, payload):
        desc = payload["description"]
        cat = payload.get("category")
        preset = payload.get("preset")
        self.app.state.state["scene"] = desc
        self.app.state.state["scene_category"] = cat
        self.app.state.state["scene_preset"] = preset
        self.scene_field.value = desc
        if hasattr(self, "scene_cat_dd") and cat in [opt.key for opt in self.scene_cat_dd.options]:
            self.scene_cat_dd.value = cat
            presets = self.app.state.ctx.scenes.get(cat, {})
            self.scene_preset_dd.options = [ft.dropdown.Option(k) for k in sorted(presets.keys())]
            self.scene_preset_dd.value = preset
        self.app.update_preview()
        self.app.show_toast(f"Applied scene: {preset}", color="green")

    def _apply_suggested_interaction(self, payload):
        desc = payload["description"]
        cat = payload.get("category")
        preset = payload.get("preset")
        self.app.state.state["notes"] = desc
        self.app.state.state["interaction_category"] = cat
        self.app.state.state["interaction_preset"] = preset
        self.app.update_preview()
        self.app.show_toast(f"Applied interaction: {preset}", color="green")

    def _apply_suggested_outfit(self, payload):
        idx = payload["char_index"]
        outfit_name = payload["outfit"]
        chars = self.app.state.state.get("selected_characters", [])
        if 0 <= idx < len(chars):
            chars[idx].outfit = outfit_name
            self.app.refresh_roster()
            self.app.update_preview()
            self.app.show_toast(f"Equipped {outfit_name} on {payload['char_name']}!", color="green")

    def handle_direct_scene(self, e):
        import threading
        ai_client = self.app.state.ctx.gemma_client
        if not ai_client:
            self.app.show_toast("AI Client not initialized.", color="red")
            return

        selected_chars = self.app.state.state.get("selected_characters", [])
        if not selected_chars:
            self.app.show_toast("Select at least 1 character in the roster to direct!", color="orange")
            return

        directive = (self.director_prompt.value or "").strip()
        self.direct_btn.disabled = True
        self.director_status.value = "Directing scene..."
        self.direct_btn.update()
        self.director_status.update()

        def _direct():
            try:
                bios = []
                for c in selected_chars:
                    name = c.name if hasattr(c, "name") else c.get("name", "")
                    details = self.app.state.ctx.characters.get(name)
                    if details:
                        summary = getattr(details, "summary", "") or ""
                        vibe = getattr(details, "vibe", "") or ""
                        bearing = getattr(details, "bearing", "") or ""
                        bios.append(f"{name}: Vibe='{vibe}', Bearing='{bearing}', Summary='{summary[:120]}'")

                result = ai_client.direct_scene(
                    selected_characters=selected_chars,
                    current_scene=self.scene_field.value or "",
                    current_notes=self.notes_field.value or "",
                    art_style=self.app.state.state.get("base_prompt", "Detailed"),
                    user_directive=directive,
                    character_details=bios,
                )

                scene_desc = result.get("scene_description", "")
                action_notes = result.get("action_notes", "")
                director_notes = result.get("director_notes", "")
                color_pairing = result.get("color_pairing", "")

                if scene_desc:
                    self.scene_field.value = scene_desc
                    self.app.state.state["scene"] = scene_desc

                if action_notes:
                    self.notes_field.value = action_notes
                    self.app.state.state["notes"] = action_notes

                self.director_status.value = director_notes[:70] if director_notes else "Scene directed!"
                self.app.update_preview()
                self.scene_field.update()
                self.notes_field.update()
                self.director_status.update()
                self.app.show_toast(f"Brought to life! Color contrast: {color_pairing}", color="green")
            except Exception as ex:
                self.director_status.value = f"Error: {ex}"
                self.director_status.update()
                self.app.show_toast(f"Director error: {ex}", color="red")
            finally:
                self.direct_btn.disabled = False
                if self.page:
                    self.direct_btn.update()

        threading.Thread(target=_direct, daemon=True).start()

    def refresh_theme(self, update_ui=True):
        self.border = ft.Border.all(1, ThemeManager.colors["outline"])
        self.padding = ThemeManager.styles["padding"]
        self.bgcolor = ThemeManager.colors["surface"]
        
        # Direct reference mapping for clean updates
        self.header_text.color = ThemeManager.colors["text_primary"]
        self.summary_header.color = ThemeManager.colors["text_primary"]
        self.summary_container.bgcolor = ThemeManager.colors["panel_bg"]
        self.summary_container.border = ft.Border.all(1, ft.Colors.with_opacity(0.05, ThemeManager.colors["text_primary"]))
        
        # Inputs & Dropdowns
        for dd in [self.scene_cat_dd, self.scene_preset_dd, self.interaction_cat_dd, self.interaction_preset_dd]:
            dd.border_color = ThemeManager.colors["outline"]
            dd.focused_border_color = ThemeManager.colors["accent"]
            
        self.scene_field.border_color = ThemeManager.colors["outline"]
        self.scene_field.focused_border_color = ThemeManager.colors["accent"]
        self.notes_field.border_color = ThemeManager.colors["outline"]
        self.notes_field.focused_border_color = ThemeManager.colors["accent"]
        
        if hasattr(self, "suggestions_container"):
            self.suggestions_container.bgcolor = ft.Colors.with_opacity(0.15, ThemeManager.colors["surface"])
            self.suggestions_container.border = ft.Border.all(1, ft.Colors.with_opacity(0.12, ThemeManager.colors["outline"]))

        if update_ui:
            self.update()
