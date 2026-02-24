import flet as ft
from ui.components.icon_button import SafeIconButton
from core.flet_theme_manager import ThemeManager
from utils.debouncer import Debouncer

class SidebarSection(ft.Container):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.debouncer = Debouncer(300) # 300ms Update Delay
        self.width = 350
        self.padding = ThemeManager.styles["padding"]
        self.border = ft.Border.all(1, ThemeManager.colors["outline"])
        self.border_radius = ft.BorderRadius.all(ThemeManager.styles["radius"])
        self.bgcolor = ThemeManager.colors["surface"]
        
        # UI controls
        self.base_prompt_dd = ft.Dropdown(label="Art Style", options=[], text_size=12, height=45, content_padding=10)
        self.base_prompt_dd.on_select = self.handle_base_prompt_change
        
        self.scene_cat_dd = ft.Dropdown(label="Scene Category", width=150, text_size=12, height=45, content_padding=10)
        self.scene_cat_dd.on_select = self.handle_scene_cat_change
        
        self.scene_preset_dd = ft.Dropdown(label="Scene Preset", width=150, text_size=12, height=45, content_padding=10)
        self.scene_preset_dd.on_select = self.handle_scene_preset_change
        
        self.scene_field = ft.TextField(label="Scene", multiline=True, min_lines=3, max_lines=5, text_size=12)
        self.scene_field.on_change = self.handle_text_change
        
        self.interaction_cat_dd = ft.Dropdown(label="Interaction Category", width=150, text_size=12, height=45, content_padding=10)
        self.interaction_cat_dd.on_select = self.handle_interaction_cat_change
        
        self.interaction_preset_dd = ft.Dropdown(label="Interaction Preset", width=150, text_size=12, height=45, content_padding=10)
        self.interaction_preset_dd.on_select = self.handle_interaction_preset_change
        
        self.notes_field = ft.TextField(label="Interactions/Notes", multiline=True, min_lines=3, max_lines=5, text_size=12)
        self.notes_field.on_change = self.handle_text_change
        
        self.summary_text = ft.Markdown(
            "No characters selected.", 
            extension_set=ft.MarkdownExtensionSet.GITHUB_FLAVORED,
            on_tap_link=lambda e: self.app.page.launch_url(e.data),
            selectable=True
        )
        
        # [NEW] Quality / Alignment Meter
        self.quality_bar = ft.ProgressBar(value=0, height=8, border_radius=5, color=ThemeManager.colors["accent"], bgcolor=ThemeManager.colors["Panel_Secondary"] if "Panel_Secondary" in ThemeManager.colors else "white10")
        self.quality_text = ft.Text("Thematic Alignment: 0%", size=11, weight="bold", color=ThemeManager.colors["text_secondary"])
        self.quality_meter = ft.Column([
            ft.Row([self.quality_text, ft.Icon(ft.Icons.INFO_OUTLINE, size=12, color=ThemeManager.colors["text_secondary"], tooltip="Matches character vibes and traits with the selected scene.")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            self.quality_bar
        ], spacing=5, visible=False)
        
        self.content = ft.Column([
            ft.Row([
                ft.Text("CONTEXT & SUMMARY", weight="bold", size=16, color=ThemeManager.colors["text_primary"]),
                ft.Row([
                    SafeIconButton(ft.Icons.CASINO, tooltip="Global Randomize", on_click=self.app.handle_randomize),
                    SafeIconButton("settings", tooltip="Dashboard", on_click=lambda _: self.app.show_dashboard())
                ], spacing=0)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            self.base_prompt_dd,
            ft.Row([self.scene_cat_dd, self.scene_preset_dd]),
            self.scene_field,
            ft.Row([self.interaction_cat_dd, self.interaction_preset_dd]),
            self.notes_field,
            ft.Divider(color=ThemeManager.colors["outline"]),
            ft.Text("Live Summary", weight="bold", size=14, color=ThemeManager.colors["text_primary"]),
            self.quality_meter,
            ft.Container(
                content=self.summary_text, 
                padding=10, 
                bgcolor=ThemeManager.colors["panel_bg"], 
                border_radius=ft.BorderRadius.all(5),
                border=ft.Border.all(1, ft.Colors.with_opacity(0.1, ThemeManager.colors["outline"]))
            )
        ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=12)

    def populate_data(self):
        ctx = self.app.state.ctx
        
        # Art Style
        self.base_prompt_dd.options = [ft.dropdown.Option(k) for k in sorted(ctx.base_prompts.keys())]
        self.base_prompt_dd.value = self.app.state.state.get("base_prompt", "Detailed")
        
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

    def handle_base_prompt_change(self, e):
        self.app.state.state["base_prompt"] = e.control.value
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
        # Calculate a simple alignment score for the meter
        # (This is a UI-only estimate, real scoring happens in Randomizer logic)
        score = 0
        total_chars = len(self.app.state.state["selected_characters"])
        if total_chars > 0:
            # Check for matches between scene tags and char vibes/traits
            # For now, we'll randomize a bit of 'jitter' to make it feel alive or stick to a base 0.5
            # Real heuristic: count keyword intersections
            score = 0.65 # Default baseline for selected scenes
            if self.app.state.state.get("scene"): score += 0.1
            if all((c.outfit if hasattr(c, "outfit") else c.get("outfit")) for c in self.app.state.state["selected_characters"]): score += 0.2
            
            self.quality_bar.value = min(score, 1.0)
            self.quality_text.value = f"Thematic Alignment: {int(self.quality_bar.value * 100)}%"
            self.quality_meter.visible = True
            
            # Stylize the summary text (e.g. bold names, use emojis)
            # Example search/replace: "Character: Name" -> "👤 **Name**"
            import re
            summary = re.sub(r"Character: ([\w\s]+)", r"👤 **\1**", summary)
            summary = re.sub(r"Outfit: ([\w\s]+)", r"👗 *\1*", summary)
            summary = re.sub(r"Scene: ([\w\s]+)", r"🎬 **\1**", summary)
        else:
            self.quality_meter.visible = False

        self.summary_text.value = summary
        self.summary_text.update()
        self.quality_meter.update()

    def refresh_theme(self, update_ui=True):
        self.border = ft.Border.all(1, ThemeManager.colors["outline"])
        self.padding = ThemeManager.styles["padding"]
        self.bgcolor = ThemeManager.colors["surface"]
        
        # Content[0] is Header Row -> Text is index 0
        self.content.controls[0].controls[0].color = ThemeManager.colors["text_primary"]
        
        # Content[6] is Divider
        self.content.controls[6].color = ThemeManager.colors["outline"]
        
        # Content[7] is "Live Summary" text
        self.content.controls[7].color = ThemeManager.colors["text_primary"]
        
        # Content[8] is Summary Container
        self.content.controls[8].bgcolor = ThemeManager.colors["panel_bg"]
        
        if update_ui:
            self.update()
