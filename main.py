import flet as ft
import os
import sys
import threading
from typing import Dict, Any, List

# Add the current directory to sys.path
# Add the current directory and src to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from core.app_context import AppContext
from core.builder import PromptBuilder
from utils import logger
from core.flet_theme_manager import ThemeManager
from logic.interaction_logic import InteractionLogic

# Modular UI Sections
from ui.sections.toolbar import ToolbarSection
from ui.sections.gallery import GallerySection
from ui.sections.roster import RosterSection
from ui.sections.sidebar import SidebarSection
from ui.sections.console import ConsoleSection
from ui.sections.dashboard import DashboardSection
from core.app_state import AppState

class FletPromptBuilder:
    def __init__(self, page: ft.Page):
        self.page = page
        
        self.page.title = "Gemini Prompt Builder"
        self.page.padding = 0
        self.page.window_width = 1600
        self.page.window_height = 900
        
        # Initialize Logic
        self.state = AppState(page)
        self.interaction_logic = InteractionLogic(self.state)
        
        # Initialize Theme
        ThemeManager.apply_theme(self.page, "Dark")
        
        self.build_ui()
        self.load_initial_data()

    def build_ui(self):
        # Instantiate Modular Sections
        self.toolbar = ToolbarSection(self)
        self.gallery = GallerySection(self)
        self.roster = RosterSection(self)
        self.sidebar = SidebarSection(self)
        self.console = ConsoleSection(self)
        self.dashboard = DashboardSection(self)
        
    def build_ui(self):
        # Instantiate Modular Sections
        self.toolbar = ToolbarSection(self)
        self.gallery = GallerySection(self)
        self.roster = RosterSection(self)
        self.sidebar = SidebarSection(self)
        self.console = ConsoleSection(self)
        self.dashboard = DashboardSection(self)
        
        # Simple Vertical Layout
        self.page.add(self.toolbar)
        self.page.add(self.gallery)
        self.page.add(ft.Container(height=10)) # Spacer
        
        # Main Area
        self.page.add(
            ft.Column([
                ft.Row([self.roster, self.sidebar], expand=True, spacing=10),
                self.console
            ], expand=True)
        )
        
        # Overlay
        self.page.overlay.append(self.dashboard)
        
        # self.page.on_click = lambda e: print(f"DEBUG_EVENT: PAGE_CLICK at ({e.page_x}, {e.page_y})")

    def load_initial_data(self):
        def _task():
            self.state.load_data()
            self.sidebar.populate_data()
            self.gallery.refresh()
            self.refresh_roster()
            self.update_preview()
            self.page.update()
            
            
        threading.Thread(target=_task, daemon=True).start()

    def refresh_assets(self, e=None):
        """Reload all data from assets directory."""
        self.state.refresh_data()
        self.sidebar.populate_data()
        self.gallery.refresh()
        self.refresh_roster()
        self.update_preview()
        self.page.update()
        self.show_toast("Assets Refreshed!", color="green")

    # --- Actions ---
    
    def handle_copy(self, e=None):
        prompt = self.state.get_prompt()
        if prompt:
            try:
                # Try standard method
                self.page.set_clipboard(prompt)
            except AttributeError:
                # Fallback for some versions
                try:
                    self.page.clipboard = prompt
                    self.page.update()
                except Exception:
                    self.show_toast("Clipboard not supported.", color="red")
                    return
            
            self.show_toast("Prompt copied to clipboard!", color="green")
        else:
            self.show_toast("No prompt to copy!", color="orange")

    # --- Proxy Methods for Modular Sections ---
    
    def add_character(self, name):
        """Toggle character in roster."""
        self.state.add_character(name)
        self.refresh_roster()
        self.gallery.refresh() # Update selection status in gallery
        self.update_preview()

    def remove_character(self, name):
        """Defensive alias for add_character."""
        self.add_character(name)

    def refresh_roster(self):
        self.roster.refresh()

    def update_preview(self):
        self.console.update_output(self.state.get_prompt())
        self.sidebar.update_summary(self.state.get_summary())
        self.page.update()

    def randomize_outfit(self, index):
        """Randomize outfit for character at index."""
        import random
        # TODO: Move this to a dedicated RandomizerLogic class if it grows
        if index >= len(self.state.state["selected_characters"]): return

        char = self.state.state["selected_characters"][index]
        char_info = self.state.ctx.characters.get(char["name"], {})
        
        # Determine valid outfits
        all_outfits = sorted(list(char_info.get("outfits", {}).keys()))
        if all_outfits:
            new_outfit = random.choice(all_outfits)
            
            # Find category
            categorized = char_info.get("outfits_categorized", {})
            for cat, outfits in categorized.items():
                if new_outfit in outfits:
                    char["outfit_category"] = cat
                    break
            char["outfit"] = new_outfit
            # Surgical update not possible cleanly from here since we want logic separation
            # Full refresh for now or utilize roster public method
            self.roster.update_character_ui(index)
            self.update_preview()

    def handle_solo_randomize(self, index):
        if not (0 <= index < len(self.state.state["selected_characters"])): return
        char_entry = self.state.state["selected_characters"][index]
        new_config = self.state.ctx.randomizer._randomize_character(char_entry["name"])
        if new_config:
            char_entry.update(new_config)
            char_entry["action_note"] = ""
        self.roster.update_character_ui(index)
        self.update_preview()

    def handle_randomize(self, e):
        if not self.state.ctx.randomizer: return
        
        config = self.state.ctx.randomizer.randomize(
            num_characters=None, # Auto
            include_scene=True,
            include_notes=True
        )
        
        if config:
            self.state.state["selected_characters"] = config["selected_characters"]
            self.state.state["base_prompt"] = config["base_prompt"]
            self.state.state["scene"] = config.get("scene", "")
            self.state.state["notes"] = config.get("notes", "")
            
            # Sync UI
            self.sidebar.populate_data()
            self.refresh_roster()
            self.update_preview()
            self.page.update()

    def clear_all_characters(self):
        self.state.state["selected_characters"] = []
        self.refresh_roster()
        self.gallery.refresh()
        self.update_preview()

    def show_toast(self, message, color=None, action=None, on_action=None):
        try:
            sb = getattr(self.page, "snack_bar", None)
            if not sb:
                sb = ft.SnackBar(ft.Text(""))
                self.page.snack_bar = sb
            
            sb.content.value = message
            sb.bgcolor = color or ThemeManager.colors["active_item"]
            sb.action = action
            sb.on_action = on_action
            sb.open = True
            self.page.update()
        except Exception:
            pass

    def show_dashboard(self, e=None):
        self.dashboard.show()

    def set_theme(self, theme_name):
        ThemeManager.apply_theme(self.page, theme_name)
        
        # Propagate theme changes to UI sections
        if hasattr(self, 'toolbar'): self.toolbar.refresh_theme()
        if hasattr(self, 'gallery'): self.gallery.refresh_theme()
        if hasattr(self, 'roster'): self.roster.refresh_theme()
        if hasattr(self, 'sidebar'): self.sidebar.refresh_theme()
        # Console usually inherits via basic props, or could add refresh if needed
        
        self.show_toast(f"Theme set to: {theme_name}") 
        self.page.update()

    def toggle_theme_mode(self, e=None):
        # Legacy/Fallback
        current = "Light" if self.page.theme_mode == ft.ThemeMode.LIGHT else "Dark"
        new_theme = "Dark" if current == "Light" else "Light"
        self.set_theme(new_theme)

    def open_automation_dialog(self, e=None):
        print(f"DEBUG: Opening Automation Dialog. Flet Version: {getattr(ft, 'version', 'unknown')}")
        try:
            from ui.dialogs.automation_dialog import AutomationDialog
            dlg = AutomationDialog(self)
            
            # Try new Flet API (0.21+)
            if hasattr(self.page, "open"):
                self.page.open(dlg)
                print("DEBUG: Used page.open(dlg)")
            else:
                # Fallback: Use Overlay (often more reliable than page.dialog in some versions)
                self.page.overlay.append(dlg)
                dlg.open = True
                self.page.update()
                print("DEBUG: Used page.overlay.append(dlg) + open=True")
                
        except Exception as err:
            print(f"ERROR: Failed to open dialog: {err}")
            self.show_toast(f"Error opening automation: {err}", color="red")

    # Stub implementations
    def open_llm_export(self, e=None): self.show_toast("LLM Export: Coming Soon!")
    def open_import_from_text(self, e=None): self.show_toast("Import: Coming Soon!")
    def open_llm_content_guide(self, e=None): self.show_toast("Content Guide: Coming Soon!")
    def open_asset_editor(self, e=None): self.show_toast("Asset Editor: Coming Soon!")
    def open_settings(self, e=None): self.show_toast("Settings: Use Sidebar for configuration.")
    
    def open_output_gallery(self, e=None):
        print("DEBUG: Opening Premium Output Gallery")
        try:
            from ui.dialogs.output_gallery import OutputGalleryDialog
            dlg = OutputGalleryDialog(self)
            
            if hasattr(self.page, "open"):
                self.page.open(dlg)
            else:
                self.page.overlay.append(dlg)
                dlg.open = True
                self.page.update()
        except Exception as err:
            print(f"ERROR: Failed to open gallery: {err}")
            # Fallback to file explorer if something breaks
            self.show_toast(f"Gallery Error, opening folder instead...", color="orange")
            output_dir = os.path.join(os.getcwd(), "output", "images", "generated_images")
            if os.path.exists(output_dir):
                os.startfile(output_dir)

    def save_preset(self, e=None): 
        # Fallback to simple file save due to FilePicker issues
        import json
        path = os.path.join(os.getcwd(), "preset.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.state.state, f, indent=2)
            self.show_toast(f"Saved to {path}")
        except Exception as err:
            self.show_toast(f"Failed to save: {err}", color="red400")
            
    def load_preset(self, e=None): 
        # Fallback to simple file load
        import json
        path = os.path.join(os.getcwd(), "preset.json")
        if not os.path.exists(path):
             self.show_toast("No preset.json found in app directory", color="orange400")
             return
             
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Basic validation
            if "selected_characters" in data:
                self.state.state.update(data)
                self.sidebar.populate_data()
                self.refresh_roster()
                self.update_preview()
                self.gallery.refresh() # In case characters changed
                self.show_toast(f"Loaded from {path}")
            else:
                self.show_toast("Invalid preset structure", color="red400")
        except Exception as err:
            self.show_toast(f"Failed to load: {err}", color="red400")

    def reset_all_outfits(self):
        for char in self.state.state["selected_characters"]:
            char["outfit"] = "Base"
            char["outfit_traits"] = []
        self.refresh_roster()
        self.update_preview()
        self.show_toast("Reset all outfits to Base")

    def handle_copy(self, e=None):
        prompt = self.state.get_prompt()
        if prompt:
            # Method 1: Try Flet set_clipboard (if exists)
            if hasattr(self.page, "set_clipboard"):
                try:
                    self.page.set_clipboard(prompt)
                    self.show_toast("Prompt copied to clipboard!", color="green")
                    return
                except Exception:
                    print("DEBUG: set_clipboard failed")

            # Method 2: Windows native 'clip' command
            import subprocess
            try:
                subprocess.run("clip", input=prompt, text=True, shell=True, check=True)
                self.show_toast("Prompt copied (Windows Native)!", color="green")
                return
            except Exception as err:
                 print(f"DEBUG: Windows clip failed: {err}")

            self.show_toast("Clipboard copy failed. Check console.", color="red")
        else:
            self.show_toast("No prompt to copy!", color="orange")

    def handle_generate(self, e=None):
        prompt = self.state.get_prompt()
        if not prompt:
            self.show_toast("No prompt to generate!")
            return
            
        if not self.state.ctx.automation_controller:
            self.show_toast("Automation module not available.")
            return

        self.page.splash = ft.ProgressBar()
        self.page.update()
        
        def on_complete(results):
            self.page.splash = None
            path = results[0].get('image_path', 'Unknown')
            
            def open_file(e):
                try:
                    os.startfile(path)
                except Exception:
                    pass

            self.show_toast(f"Generation Complete! Saved to: {path}", action="OPEN", on_action=open_file)
            self.page.update()

        def on_error(err):
            self.page.splash = None
            self.show_toast(f"Error: {str(err)}", color="red400")
            self.page.update()

        self.state.ctx.automation_controller.start_generation(
            count=1,
            match_outfits_prob=0,
            prompts_only=False,
            on_progress=lambda *args: None,
            on_complete=on_complete,
            on_error=on_error,
            fixed_prompt=prompt
        )
        
        self.show_toast("Starting generation...")

    def close_dialog(self, dlg):
        dlg.open = False
        self.page.update()

def main(page: ft.Page):
    FletPromptBuilder(page)



if __name__ == "__main__":
    try:
        ft.app(target=main)
    except Exception:
        import traceback
        traceback.print_exc()
        input("Press enter to exit...")
