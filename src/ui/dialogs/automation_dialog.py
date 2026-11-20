import flet as ft
from core.flet_theme_manager import ThemeManager


class AutomationDialog(ft.AlertDialog):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.modal = True

        # --- Header with gradient accent bar ---
        self.title = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.AUTO_AWESOME, color="#ffffff", size=20),
                    width=36, height=36,
                    border_radius=18,
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
                        colors=["#7c3aed", ThemeManager.colors["accent"]]
                    ),
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Column([
                    ft.Text("Automation Studio", size=16, weight=ft.FontWeight.W_700),
                    ft.Text("Configure and launch batch generation", size=11,
                            color=ThemeManager.colors["text_secondary"]),
                ], spacing=2, tight=True),
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.only(bottom=5),
        )

        # =====================================================================
        #  CONTROLS
        # =====================================================================
        self.count_slider = ft.Slider(
            min=1, max=10, divisions=9, value=1, label="{value}",
            active_color=ThemeManager.colors["accent"],
        )
        self.num_chars_dd = ft.Dropdown(
            options=[ft.dropdown.Option("Auto")] + [ft.dropdown.Option(str(i)) for i in range(1, 4)],
            value="Auto", width=100, text_size=12, height=42, content_padding=8,
            border_color=ThemeManager.colors["outline"],
            focused_border_color=ThemeManager.colors["accent"],
        )

        # --- Pipeline switches with semantic grouping ---
        self.scene_switch = ft.Switch(label="Scene", value=True, label_text_style=ft.TextStyle(size=12))
        self.notes_switch = ft.Switch(label="Interaction", value=True, label_text_style=ft.TextStyle(size=12))

        self.gemma_switch = ft.Switch(
            label="Enhance", value=False,
            active_color=ThemeManager.colors["accent"],
            label_text_style=ft.TextStyle(size=12),
        )
        self.critic_switch = ft.Switch(
            label="AI Critic", value=False,
            active_color="#f59e0b",
            label_text_style=ft.TextStyle(size=12),
        )
        self.pure_gemma_switch = ft.Switch(
            label="Pure Gemma", value=False,
            active_color="#a855f7",
            label_text_style=ft.TextStyle(size=12),
        )
        self.prompts_only_switch = ft.Switch(
            label="Prompts Only", value=False,
            label_text_style=ft.TextStyle(size=12),
        )
        self.format_mode_dd = ft.Dropdown(
            options=[
                ft.dropdown.Option("Markdown"),
                ft.dropdown.Option("Prose"),
                ft.dropdown.Option("Midjourney"),
                ft.dropdown.Option("SDXL"),
            ],
            value="Markdown", width=130, text_size=12, height=42, content_padding=8,
            border_color=ThemeManager.colors["outline"],
            focused_border_color=ThemeManager.colors["accent"],
        )

        # --- Progress & Log Console ---
        self.progress_bar = ft.ProgressBar(width=620, visible=False, value=0,
                                           color=ThemeManager.colors["accent"],
                                           bgcolor=ThemeManager.colors["outline"])

        # Status chip shown during generation
        self.status_chip = ft.Container(
            content=ft.Row([
                ft.ProgressRing(width=14, height=14, stroke_width=2, color=ThemeManager.colors["accent"]),
                ft.Text("Idle", size=11, color=ThemeManager.colors["text_secondary"],
                        weight=ft.FontWeight.W_500),
            ], spacing=8),
            visible=False,
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            border_radius=20,
            bgcolor=ft.Colors.with_opacity(0.15, ThemeManager.colors["accent"]),
        )

        self.log_list = ft.ListView(height=150, spacing=1, auto_scroll=True)
        self.log_container = ft.Container(
            content=ft.Column([
                # Console header bar
                ft.Container(
                    content=ft.Row([
                        ft.Row([
                            ft.Container(width=8, height=8, border_radius=4, bgcolor="#ff5f57"),
                            ft.Container(width=8, height=8, border_radius=4, bgcolor="#febc2e"),
                            ft.Container(width=8, height=8, border_radius=4, bgcolor="#28c840"),
                        ], spacing=5),
                        self.status_chip,
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                    bgcolor="#0a0a0a",
                    border_radius=ft.BorderRadius.only(top_left=10, top_right=10),
                ),
                # Console body
                ft.Container(
                    content=self.log_list,
                    padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                    bgcolor="#0c0c0c",
                    border_radius=ft.BorderRadius.only(bottom_left=10, bottom_right=10),
                    expand=True,
                ),
            ], spacing=0, tight=True),
            height=195,
            border=ft.Border.all(1, "#1a1a1a"),
            border_radius=10,
            visible=False,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=12,
                                color=ft.Colors.with_opacity(0.3, "#000"),
                                offset=ft.Offset(0, 4)),
        )

        # =====================================================================
        #  CHARACTER SELECTION with Search
        # =====================================================================
        self.char_selections = {}
        self._char_rows = []  # Keep references for filtering
        self._char_list_view = ft.ListView(spacing=1, height=155)

        # Search bar
        self.char_search = ft.TextField(
            hint_text="Search characters...",
            prefix_icon=ft.Icons.SEARCH,
            text_size=12, height=38, content_padding=8,
            border_color=ThemeManager.colors["outline"],
            focused_border_color=ThemeManager.colors["accent"],
            on_change=self._on_char_search,
            border_radius=8,
        )

        # Build character rows
        sorted_chars = sorted(self.app.state.ctx.characters_metadata.keys())
        for idx, name in enumerate(sorted_chars):
            force_chk = ft.Checkbox(value=False, fill_color="#f59e0b", scale=0.8)
            allow_chk = ft.Checkbox(value=False, fill_color=ThemeManager.colors["accent"], scale=0.8)
            self.char_selections[name] = {"force": force_chk, "allow": allow_chk}

            row = ft.Container(
                content=ft.Row([
                    ft.Container(force_chk, width=44, alignment=ft.Alignment(0, 0)),
                    ft.Container(allow_chk, width=44, alignment=ft.Alignment(0, 0)),
                    ft.Text(name, size=12, expand=True, weight=ft.FontWeight.W_500),
                ]),
                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                bgcolor=ft.Colors.with_opacity(0.04, "#ffffff") if idx % 2 == 0 else ft.Colors.TRANSPARENT,
                border_radius=4,
                data=name.lower(),  # Store lowercase name for search matching
            )
            self._char_rows.append(row)
            self._char_list_view.controls.append(row)

        # Header row
        list_header = ft.Container(
            content=ft.Row([
                ft.Text("Force", size=10, weight="bold", width=44, text_align=ft.TextAlign.CENTER,
                        color=ThemeManager.colors["text_secondary"]),
                ft.Text("Pool", size=10, weight="bold", width=44, text_align=ft.TextAlign.CENTER,
                        color=ThemeManager.colors["text_secondary"]),
                ft.Text("Character", size=10, weight="bold", expand=True,
                        color=ThemeManager.colors["text_secondary"]),
            ]),
            padding=ft.Padding.symmetric(horizontal=6, vertical=6),
            bgcolor=ft.Colors.with_opacity(0.08, "#ffffff"),
            border_radius=ft.BorderRadius.only(top_left=8, top_right=8),
        )

        char_panel = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Character Pool", weight="bold", size=12,
                            color=ThemeManager.colors["text_secondary"]),
                    ft.Text(f"{len(sorted_chars)} available", size=10,
                            color=ThemeManager.colors["text_secondary"], italic=True),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                self.char_search,
                ft.Container(
                    content=ft.Column([list_header, self._char_list_view], spacing=0, tight=True),
                    border=ft.Border.all(1, ThemeManager.colors["outline"]),
                    border_radius=8,
                    bgcolor=ThemeManager.colors["panel_bg"],
                ),
            ], spacing=8, tight=True),
        )

        # =====================================================================
        #  SCENARIO
        # =====================================================================
        self.scenario_dd = ft.Dropdown(
            label="Scenario",
            options=[ft.dropdown.Option("Auto / Random")] + [
                ft.dropdown.Option(s.name)
                for s in self.app.state.ctx.randomizer.scenario_registry.get_all()
            ],
            value="Auto / Random",
            text_size=12, height=42, content_padding=8,
            border_color=ThemeManager.colors["outline"],
            focused_border_color=ThemeManager.colors["accent"],
        )

        # =====================================================================
        #  ADVANCED
        # =====================================================================
        self.candidates_slider = ft.Slider(
            min=1, max=10, divisions=9, value=3, label="{value} Candidates",
            active_color=ThemeManager.colors["accent"],
        )
        self.cohesion_slider = ft.Slider(
            min=0.0, max=1.0, divisions=10, value=0.3, label="{value} Cohesion",
            active_color=ThemeManager.colors["accent"],
        )

        self.advanced_expander = ft.ExpansionTile(
            title=ft.Text("Advanced Settings", size=12, weight=ft.FontWeight.W_500),
            subtitle=ft.Text("Candidate pool size, outfit cohesion", size=10,
                             color=ThemeManager.colors["text_secondary"]),
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Text("Candidate Quality (more = slower but better)", size=11,
                                color=ThemeManager.colors["text_secondary"]),
                        self.candidates_slider,
                        ft.Text("Outfit Cohesion (higher = more matching)", size=11,
                                color=ThemeManager.colors["text_secondary"]),
                        self.cohesion_slider,
                    ], spacing=6, tight=True),
                    padding=ft.Padding.symmetric(horizontal=10, vertical=5),
                )
            ],
            tile_padding=ft.Padding.symmetric(horizontal=4),
            expanded=False,
        )

        # =====================================================================
        #  SECTION BUILDERS
        # =====================================================================
        def _make_section(title_text, icon, children, accent_color=None):
            """Build a styled card section."""
            border_color = accent_color or ThemeManager.colors["outline"]
            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(icon, size=15, color=accent_color or ThemeManager.colors["text_secondary"]),
                        ft.Text(title_text, weight=ft.FontWeight.W_600, size=12,
                                color=ThemeManager.colors["text_secondary"]),
                    ], spacing=8),
                    *children,
                ], tight=True, spacing=10),
                padding=14,
                border_radius=10,
                bgcolor=ThemeManager.colors["panel_bg"],
                border=ft.Border.all(1, border_color),
            )

        def _switch_pill(switch, icon=None, tooltip=None):
            """Wrap a switch in a pill-shaped container."""
            row_children = []
            if icon:
                row_children.append(ft.Icon(icon, size=14, color=ThemeManager.colors["text_secondary"]))
            row_children.append(switch)
            return ft.Container(
                content=ft.Row(row_children, spacing=6),
                padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                bgcolor=ft.Colors.with_opacity(0.06, "#ffffff"),
                border_radius=8,
                expand=True,
                tooltip=tooltip,
            )

        # --- Core Settings Section ---
        core_section = _make_section("Generation", ft.Icons.TUNE, [
            ft.Row([
                ft.Text("Count:", size=12, weight=ft.FontWeight.W_500, width=130),
                self.count_slider,
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row([
                ft.Text("Characters:", size=12, weight=ft.FontWeight.W_500, width=130),
                self.num_chars_dd,
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row([
                ft.Text("Engine Profile:", size=12, weight=ft.FontWeight.W_500, width=130),
                self.format_mode_dd,
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            self.scenario_dd,
        ])

        # --- Pipeline Section with semantic grouping ---
        pipeline_section = _make_section("Pipeline Engine", ft.Icons.ACCOUNT_TREE, [
            # Row 1: Content toggles
            ft.Row([
                _switch_pill(self.scene_switch, ft.Icons.LANDSCAPE, "Include scene descriptions"),
                _switch_pill(self.notes_switch, ft.Icons.PEOPLE, "Include interaction notes"),
            ], spacing=8),
            ft.Divider(height=1, color=ThemeManager.colors["outline"]),
            # Row 2: AI modes
            ft.Row([
                _switch_pill(self.gemma_switch, ft.Icons.AUTO_FIX_HIGH, "Post-process with Gemma"),
                _switch_pill(self.pure_gemma_switch, ft.Icons.PSYCHOLOGY, "Let Gemma architect the entire prompt"),
            ], spacing=8),
            # Row 3: Quality & output
            ft.Row([
                _switch_pill(self.critic_switch, ft.Icons.RATE_REVIEW, "AI auditor filters anachronisms"),
                _switch_pill(self.prompts_only_switch, ft.Icons.TEXT_SNIPPET, "Output text only, skip image generation"),
            ], spacing=8),
        ], accent_color="#7c3aed")

        # =====================================================================
        #  MAIN LAYOUT
        # =====================================================================
        self.content = ft.Container(
            width=660,
            content=ft.Column([
                core_section,
                pipeline_section,
                char_panel,
                self.advanced_expander,
                self.progress_bar,
                self.log_container,
            ], spacing=12, tight=True, scroll=ft.ScrollMode.AUTO),
        )

        # =====================================================================
        #  ACTION BUTTONS
        # =====================================================================
        self.stop_btn = ft.FilledButton(
            "Stop", on_click=self.handle_stop, icon=ft.Icons.STOP,
            visible=False, style=ft.ButtonStyle(bgcolor="#ef4444"),
        )
        self.start_btn = ft.FilledButton(
            "Start Generation", on_click=self.handle_start,
            icon=ft.Icons.ROCKET_LAUNCH,
            style=ft.ButtonStyle(
                bgcolor=ThemeManager.colors["accent"],
                color="#ffffff",
            ),
        )

        self.actions = [
            ft.TextButton("Cancel", on_click=self.handle_close),
            self.stop_btn,
            self.start_btn,
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    # =================================================================
    #  Character Search Filter
    # =================================================================
    def _on_char_search(self, e):
        query = (e.control.value or "").lower().strip()
        for row in self._char_rows:
            row.visible = query in row.data if query else True
        try:
            self._char_list_view.update()
        except Exception:
            pass

    # =================================================================
    #  Log Helpers
    # =================================================================
    def _log(self, current, total, msg, color=None):
        """Append a styled log line to the console."""
        if color is None:
            color = ThemeManager.colors["text_secondary"]

        # Prefix with step indicator
        prefix = f"[{current}/{total}]" if total > 0 else "[•]"

        self.log_list.controls.append(
            ft.Text(
                f"{prefix}  {msg}", size=11, color=color,
                font_family="Consolas", selectable=True,
            )
        )
        # Keep buffer bounded
        if len(self.log_list.controls) > 50:
            self.log_list.controls.pop(0)

    def _update_status(self, text):
        """Update the status chip text."""
        status_row = self.status_chip.content
        if status_row and len(status_row.controls) > 1:
            status_row.controls[1].value = text

    # =================================================================
    #  Handlers
    # =================================================================
    def handle_close(self, e):
        if self.app.state.ctx.automation_controller:
            self.app.state.ctx.automation_controller.stop()
        self.app.close_dialog(self)

    def handle_stop(self, e):
        if self.app.state.ctx.automation_controller:
            self.app.state.ctx.automation_controller.stop()
        self.stop_btn.visible = False
        self._log(0, 0, "⏹  Generation stopped by user.", color="#f59e0b")
        self._update_status("Stopped")
        self.update()

    def handle_start(self, e):
        if not self.app.state.ctx.automation_controller:
            self.app.show_toast("Automation Controller not initialized.", color="red")
            return

        # Gather params
        count = int(self.count_slider.value)
        num_chars = int(self.num_chars_dd.value) if self.num_chars_dd.value != "Auto" else None

        forced = [name for name, chks in self.char_selections.items() if chks["force"].value]
        allowed = [name for name, chks in self.char_selections.items() if chks["allow"].value]

        for f in forced:
            if f not in allowed:
                allowed.append(f)

        scenario_val = self.scenario_dd.value
        forced_scenario = scenario_val if scenario_val != "Auto / Random" else None

        candidates = int(self.candidates_slider.value)
        cohesion = float(self.cohesion_slider.value)

        # Reset UI
        self.progress_bar.visible = True
        self.progress_bar.value = None
        self.log_container.visible = True
        self.status_chip.visible = True
        self.log_list.controls.clear()
        self._log(0, count, "Initializing pipeline...", color=ThemeManager.colors["text_secondary"])
        self._update_status("Starting...")
        self.start_btn.disabled = True
        self.stop_btn.visible = True
        self.update()

        # Callbacks
        def on_progress(current, total, msg):
            try:
                if not self.page:
                    return
                self.progress_bar.value = current / total if total > 0 else 0

                # Color-code by pipeline step
                color = ThemeManager.colors["text_secondary"]
                status = "Working..."
                if "Step 1" in msg:
                    color = ThemeManager.colors["accent"]
                    status = "Step 1: Roster"
                elif "Step 2" in msg:
                    color = "#a855f7"
                    status = "Step 2: Gear"
                elif "Step 3" in msg:
                    color = "#22c55e"
                    status = "Step 3: Compose"
                elif "Audit" in msg:
                    color = "#f59e0b"
                    status = "Auditing..."
                elif "Rebuild" in msg:
                    color = "#ef4444"
                    status = "Rebuilding..."
                elif "Attempt" in msg:
                    color = "#f59e0b"
                elif "->" in msg:
                    color = ft.Colors.with_opacity(0.7, ThemeManager.colors["text_primary"])

                self._log(current, total, msg, color=color)
                self._update_status(status)
                self.update()
            except Exception:
                pass

        def on_complete(results):
            try:
                if not self.page:
                    return
                self.progress_bar.visible = False
                self._log(len(results), len(results),
                          f"✓  Complete — {len(results)} prompts generated",
                          color="#22c55e")
                self._update_status("Done")
                # Replace spinner with checkmark
                status_row = self.status_chip.content
                if status_row and len(status_row.controls) > 0:
                    status_row.controls[0] = ft.Icon(ft.Icons.CHECK_CIRCLE, size=14, color="#22c55e")
                self.status_chip.bgcolor = ft.Colors.with_opacity(0.15, "#22c55e")
                self.start_btn.disabled = False
                self.stop_btn.visible = False
                self.update()
            except Exception:
                pass

            msg = f"Generated {len(results)} items."

            if self.prompts_only_switch.value and results:
                import os
                import time
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                out_dir = os.path.join(base_dir, "output", "prompts")
                os.makedirs(out_dir, exist_ok=True)

                filename = f"automated_prompts_{int(time.time())}.txt"
                filepath = os.path.join(out_dir, filename)

                with open(filepath, "w", encoding="utf-8") as f:
                    for i, res in enumerate(results):
                        fmt_str = res.get("format", self.format_mode_dd.value.lower()).upper()
                        f.write(f"--- PROMPT {i+1} ({fmt_str}) ---\n")
                        f.write(res.get("prompt", ""))
                        f.write("\n\n")

                msg += f" Saved to output/prompts/{filename}"
            elif not self.prompts_only_switch.value and results:
                last_path = results[-1].get("image_path")
                if last_path:
                    msg += " Saved to gallery."

            self.app.show_toast(msg)
            self.handle_close(None)

            if not self.prompts_only_switch.value:
                self.app.open_output_gallery()

        def on_error(err):
            try:
                if not self.page:
                    return
                self.progress_bar.visible = False
                self._log(0, 0, f"✗  Error: {err}", color="#ef4444")
                self._update_status("Error")
                status_row = self.status_chip.content
                if status_row and len(status_row.controls) > 0:
                    status_row.controls[0] = ft.Icon(ft.Icons.ERROR, size=14, color="#ef4444")
                self.status_chip.bgcolor = ft.Colors.with_opacity(0.15, "#ef4444")
                self.start_btn.disabled = False
                self.stop_btn.visible = False
                self.update()
                self.app.show_toast(f"Error: {err}", color="red")
            except Exception:
                pass

        # Start generation
        self.app.state.ctx.automation_controller.start_generation(
            count=count,
            match_outfits_prob=cohesion,
            prompts_only=self.prompts_only_switch.value,
            on_progress=on_progress,
            on_complete=on_complete,
            on_error=on_error,
            num_characters=num_chars,
            include_scene=self.scene_switch.value,
            include_notes=self.notes_switch.value,
            candidates=candidates,
            forced_characters=forced if forced else None,
            forced_scenario=forced_scenario,
            use_gemma=self.gemma_switch.value,
            use_critic=self.critic_switch.value,
            pure_gemma=self.pure_gemma_switch.value,
            character_pool=allowed if allowed else None,
            format_type=self.format_mode_dd.value.lower(),
        )
