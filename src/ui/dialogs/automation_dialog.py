import flet as ft
from core.flet_theme_manager import ThemeManager

class AutomationDialog(ft.AlertDialog):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.title = ft.Text("Automation Studio")
        
        # --- Controls ---
        self.count_slider = ft.Slider(min=1, max=10, divisions=9, value=1, label="{value}")
        self.num_chars_dd = ft.Dropdown(
            options=[ft.dropdown.Option("Auto")] + [ft.dropdown.Option(str(i)) for i in range(1, 4)],
            value="Auto", width=100
        )
        self.scene_switch = ft.Switch(label="Include Scene", value=True)
        self.notes_switch = ft.Switch(label="Include Interaction", value=True)
        self.prompts_only_switch = ft.Switch(label="Prompts Only (Test)", value=False)
        self.progress_bar = ft.ProgressBar(width=400, visible=False, value=0)
        self.status_text = ft.Text("", size=12, color="grey")

        # Character Selection
        self.char_checks = []
        char_list_col = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO, height=150)
        
        sorted_chars = sorted(self.app.state.ctx.characters.keys())
        for name in sorted_chars:
            chk = ft.Checkbox(label=name, value=False)
            self.char_checks.append(chk)
            char_list_col.controls.append(chk)

        # Layout
        self.content = ft.Container(
            width=500,
            content=ft.Column([
                ft.Text("Generation Settings", weight="bold"),
                ft.Row([
                    ft.Text("Count:"), self.count_slider,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    ft.Text("Characters per Image:"), self.num_chars_dd
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                ft.Row([self.scene_switch, self.notes_switch]),
                self.prompts_only_switch,
                ft.Divider(),
                ft.Text("Force Characters (Optional)", weight="bold"),
                ft.Container(
                    content=char_list_col,
                    height=150,
                    border=ft.Border.all(1, ThemeManager.colors["outline"]),
                    border_radius=5,
                    padding=5
                ),
                ft.Divider(color="transparent"),
                self.progress_bar,
                self.status_text
            ], spacing=10, tight=True)
        )
        
        self.actions = [
            ft.TextButton("Cancel", on_click=self.handle_close),
            ft.FilledButton("Start Generation", on_click=self.handle_start, icon=ft.Icons.AUTO_FIX_HIGH)
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def handle_close(self, e):
        self.app.close_dialog(self)

    def handle_start(self, e):
        if not self.app.state.ctx.automation_controller:
            self.app.show_toast("Automation Controller not initialized.", color="red")
            return

        # Gather params
        count = int(self.count_slider.value)
        num_chars = int(self.num_chars_dd.value) if self.num_chars_dd.value != "Auto" else None
        forced = [chk.label for chk in self.char_checks if chk.value]
        
        # Reset UI
        self.progress_bar.visible = True
        self.progress_bar.value = None # Indeterminate start
        self.status_text.value = "Starting..."
        self.actions[1].disabled = True
        self.update()

        # Callbacks
        def on_progress(current, total, msg):
            # Must queue update on main thread
            # Simply triggering self.update() works in Flet if app is thread-safe
            # But better to use page.run_task or similar if available, or just rely on Flet's threading model
            self.progress_bar.value = current / total if total > 0 else 0
            self.status_text.value = f"{msg} ({current}/{total})"
            self.update()

        def on_complete(results):
            self.progress_bar.visible = False
            self.status_text.value = "Complete!"
            self.actions[1].disabled = False
            self.update()
            
            msg = f"Generated {len(results)} items."
            if not self.prompts_only_switch.value and results:
                last_path = results[-1].get("image_path")
                if last_path:
                    msg += f" Saved to gallery."
            
            self.app.show_toast(msg)
            self.handle_close(None)
            
            if not self.prompts_only_switch.value:
                self.app.open_output_gallery()

        def on_error(err):
            self.progress_bar.visible = False
            self.status_text.value = f"Error: {err}"
            self.actions[1].disabled = False
            self.update()
            self.app.show_toast(f"Error: {err}", color="red")

        # Start
        self.app.state.ctx.automation_controller.start_generation(
            count=count,
            match_outfits_prob=0.3, # Hardcoded for now or add slider
            prompts_only=self.prompts_only_switch.value,
            on_progress=on_progress,
            on_complete=on_complete,
            on_error=on_error,
            num_characters=num_chars,
            include_scene=self.scene_switch.value,
            include_notes=self.notes_switch.value,
            forced_characters=forced if forced else None
        )
