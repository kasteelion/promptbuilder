import flet as ft
from core.flet_theme_manager import ThemeManager
from scripts.automation.bulk_generator import parse_bulk_text, resolve_config

class ImportTextDialog(ft.AlertDialog):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.title = ft.Text("Import from Text", weight="bold")
        
        # UI Components
        self.input_field = ft.TextField(
            multiline=True,
            min_lines=10,
            max_lines=15,
            text_size=12,
            hint_text="Paste PROMPT CONFIG blocks here...",
            expand=True,
            border_color=ThemeManager.colors["outline"]
        )
        
        self.config_list = ft.ListView(expand=True, spacing=5, height=200)
        self.parsed_configs = []
        
        self.content = ft.Container(
            width=700,
            height=500,
            content=ft.Column([
                ft.Text("Paste your prompt configuration text below:", size=12, color="grey"),
                self.input_field,
                ft.FilledTonalButton("Parse Text", on_click=self.handle_parse, icon=ft.Icons.ANALYTICS),
                ft.Divider(),
                ft.Text("Detected Configurations:", weight="bold"),
                ft.Container(
                    content=self.config_list,
                    border=ft.Border.all(1, ThemeManager.colors["outline"]),
                    border_radius=5,
                    padding=5,
                    expand=True
                )
            ])
        )
        
        self.actions = [
            ft.TextButton("Close", on_click=self.handle_close)
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def handle_parse(self, e):
        text = self.input_field.value
        if not text:
            self.app.show_toast("Please paste text first.", color="orange")
            return
            
        try:
            raw_configs = parse_bulk_text(text)
            self.parsed_configs = []
            self.config_list.controls.clear()
            
            if not raw_configs:
                self.config_list.controls.append(ft.Text("No valid configurations found.", color="red"))
            else:
                for idx, conf in enumerate(raw_configs):
                    # Resolve logic (needs loader/poses, using existing app context if possible)
                    # We need access to poses, but app.state.ctx.poses contains them.
                    # We might need to mock or reuse 'resolve_config' dependencies.
                    # resolve_config expects 'loader' object with 'load_characters' etc.
                    # Our app.state.data_loader has these methods.
                    
                    try:
                        resolved = resolve_config(conf, self.app.state.data_loader, self.app.state.ctx.poses)
                        self.parsed_configs.append(resolved)
                        
                        # Create List Item
                        desc = f"Base: {resolved.get('base_prompt', 'Unknown')}"
                        chars = ", ".join([c['name'] for c in resolved.get('selected_characters', [])])
                        if chars: desc += f" | Chars: {chars}"
                        
                        btn = ft.ListTile(
                            leading=ft.Icon(ft.Icons.DESCRIPTION),
                            title=ft.Text(f"Config #{idx+1}", weight="bold"),
                            subtitle=ft.Text(desc, size=12),
                            trailing=ft.FilledButton("Load", on_click=lambda e, c=resolved: self.load_config(c))
                        )
                        self.config_list.controls.append(btn)
                        
                    except Exception as err:
                        print(f"Error resolving config {idx}: {err}")
                        self.config_list.controls.append(ft.Text(f"Error parsing config #{idx+1}", color="red"))
            
            self.update()
            
        except Exception as err:
            self.app.show_toast(f"Parse Error: {err}", color="red")

    def load_config(self, config):
        """Apply config to AppState."""
        try:
            # 1. Base Prompt
            if "base_prompt" in config:
                self.app.state.state["base_prompt"] = config["base_prompt"]
                
            # 2. Scene
            if "scene" in config:
                self.app.state.state["scene"] = config["scene"]
                
            # 3. Notes
            if "notes" in config:
                self.app.state.state["notes"] = config["notes"]
                
            # 4. Characters
            start_idx = 0
            # Clear existing? Or append? Usually "Load" implies replace.
            self.app.state.state["selected_characters"] = []
            
            for char_conf in config.get("selected_characters", []):
                name = char_conf["name"]
                
                # Check if char exists in library
                if hasattr(self.app.state, "ensure_character_loaded"):
                    self.app.state.ensure_character_loaded(name)
                
                # Use controller to safely add character
                if hasattr(self.app, "char_controller"):
                    self.app.char_controller.add_character(name)
                elif hasattr(self.app, "add_character"):
                    self.app.add_character(name)
                
                if not self.app.state.state["selected_characters"]:
                    continue

                new_char = self.app.state.state["selected_characters"][-1]
                
                def _set_attr(obj, key, val):
                    if hasattr(obj, key):
                        setattr(obj, key, val)
                    elif isinstance(obj, dict):
                        obj[key] = val

                if "outfit" in char_conf:
                    _set_attr(new_char, "outfit", char_conf["outfit"])
                if "color_scheme" in char_conf:
                    _set_attr(new_char, "color_scheme", char_conf["color_scheme"])
                if "use_signature_color" in char_conf:
                    _set_attr(new_char, "use_signature_color", char_conf["use_signature_color"])
                if "pose_preset" in char_conf:
                    _set_attr(new_char, "pose_preset", char_conf["pose_preset"])
                    if "pose_category" in char_conf:
                        _set_attr(new_char, "pose_category", char_conf["pose_category"])
                if "action_note" in char_conf:
                    _set_attr(new_char, "action_note", char_conf["action_note"])

            # Refresh UI
            self.app.sidebar.populate_data()
            self.app.refresh_roster()
            self.app.update_preview()
            self.app.gallery.refresh()
            
            self.app.show_toast("Configuration Loaded!")
            self.handle_close(None)
            
        except Exception as e:
            self.app.show_toast(f"Load Failed: {e}", color="red")

    def handle_close(self, e):
        self.app.close_dialog(self)
