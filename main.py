import flet as ft
import os
import sys
import threading
import json
import random
import subprocess
import traceback
import argparse
from typing import Dict, Any, List, Optional
# Add the current directory and src to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from core.builder import PromptBuilder
from core.app_state import AppState
from utils import logger
from core.flet_theme_manager import ThemeManager
from logic.interaction_logic import InteractionLogic
from logic.character_logic import CharacterLogic
from logic.controllers import CharacterController

# Modular UI Sections
from ui.sections.toolbar import ToolbarSection
from ui.sections.gallery import GallerySection
from ui.sections.roster import RosterSection
from ui.sections.sidebar import SidebarSection
from ui.sections.console import ConsoleSection
from ui.sections.dashboard import DashboardSection

class PlatformUtils:
    """Standardized platform-specific operations (web-safe)."""
    
    @staticmethod
    def open_path(path: str, is_web: bool = False):
        """Open a file or directory in the system's default handler."""
        if is_web:
            return  # No-op on web
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])
        except Exception as e:
            from utils import logger
            logger.error(f"Failed to open path {path}: {e}")

    @staticmethod
    def copy_to_clipboard(page: ft.Page, text: str, is_web: bool = False) -> bool:
        """Copy text to clipboard. Uses Flet API (works on both web and desktop)."""
        # Method 1: Flet API (works on web and desktop)
        if hasattr(page, "set_clipboard"):
            try:
                page.set_clipboard(text)
                return True
            except Exception:
                pass

        # Method 2: OS-specific commands (desktop only)
        if not is_web:
            try:
                if sys.platform == "win32":
                    subprocess.run("clip", input=text, text=True, shell=True, check=True)
                    return True
                elif sys.platform == "darwin":
                    subprocess.run("pbcopy", input=text, text=True, check=True)
                    return True
            except Exception:
                pass
            
        return False

class FletPromptBuilder:
    def __init__(self, page: ft.Page):
        self.page = page
        self.is_web = getattr(page, 'web', False)
        
        self.page.title = "Gemini Prompt Builder"
        self.page.padding = 0
        if not self.is_web:
            self.page.window_width = 1600
            self.page.window_height = 900
        
        # Initialize Logic & Controllers
        self.state = AppState(page)
        self.interaction_logic = InteractionLogic(self.state)
        # Controller layer (New)
        self.char_controller = CharacterController(self.state)
        # Legacy backup/internal logic
        self.character_logic = self.char_controller.logic 
        
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
        


    def load_initial_data(self):
        def _task():
            try:
                self.state.load_data()
                # Update UI components without triggering redundant page updates
                self.sidebar.populate_data()
                self.gallery.refresh(update_ui=False)
                self.roster.refresh(update_ui=False)
                
                # Finalize with a single update
                self.update_preview() 
                # self.page.update() is handled in update_preview
            except Exception as e:
                logger.error(f"Error loading initial data: {e}")
            
        threading.Thread(target=_task, daemon=True).start()

    def refresh_assets(self, e=None):
        """Reload all data from assets directory."""
        self.state.refresh_data()
        self.sidebar.populate_data()
        self.gallery.refresh(update_ui=False)
        self.roster.refresh(update_ui=False)
        self.update_preview()
        self.show_toast("Assets Refreshed!", color="green")

    # --- Actions ---

    # --- Proxy Methods for Modular Sections ---
    
    def add_character(self, name):
        """Toggle character in roster via controller."""
        if self.char_controller.add_character(name):
            self.refresh_roster()
            self.gallery.refresh() # Update selection status in gallery
            self.update_preview()
        else:
            # Check if it was a removal or a failure
            if any((c.name if hasattr(c, "name") else c["name"]) == name for c in self.state.state["selected_characters"]):
                 # Should not happen on success, but for safety:
                 self.show_toast(f"Failed to add: {name}", color="red")
            else:
                 # It was removed
                 self.refresh_roster()
                 self.gallery.refresh()
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

    def handle_solo_randomize(self, index):
        if not self.state.ctx.randomizer: 
            self.show_toast("Randomizer not available.", color="orange")
            return
        if not (0 <= index < len(self.state.state["selected_characters"])): return
        
        char_entry = self.state.state["selected_characters"][index]
        name = char_entry.name if hasattr(char_entry, "name") else char_entry["name"]
        
        new_config = self.state.ctx.randomizer._randomize_character(name)
        if new_config:
            new_config["action_note"] = ""
            self.char_controller.update_character(index, new_config)
        
        self.refresh_roster()
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
        
        # Propagate theme changes to UI sections (without redundant page.update calls)
        if hasattr(self, 'toolbar'): self.toolbar.refresh_theme(update_ui=False)
        if hasattr(self, 'gallery'): self.gallery.refresh_theme(update_ui=False)
        if hasattr(self, 'roster'): self.roster.refresh_theme(update_ui=False)
        if hasattr(self, 'sidebar'): self.sidebar.refresh_theme(update_ui=False)
        if hasattr(self, 'console'): self.console.refresh_theme(update_ui=False)
        
        self.show_toast(f"Theme set to: {theme_name}") 
        self.page.update()

    def toggle_theme_mode(self, e=None):
        # Legacy/Fallback
        current = "Light" if self.page.theme_mode == ft.ThemeMode.LIGHT else "Dark"
        new_theme = "Dark" if current == "Light" else "Light"
        self.set_theme(new_theme)

    def open_automation_dialog(self, e=None):

        try:
            from ui.dialogs.automation_dialog import AutomationDialog
            dlg = AutomationDialog(self)
            
            # Try new Flet API (0.21+)
            if hasattr(self.page, "open"):
                self.page.open(dlg)

            else:
                # Fallback: Use Overlay (often more reliable than page.dialog in some versions)
                self.page.overlay.append(dlg)
                dlg.open = True
                self.page.update()

                
        except Exception as err:
            logger.error(f"Failed to open dialog: {err}")
            self.show_toast(f"Error opening automation: {err}", color="red")

    # Stub implementations
    def open_import_from_text(self, e=None):
        try:
            from ui.dialogs.import_text_dialog import ImportTextDialog
            dlg = ImportTextDialog(self)
            self._open_dialog(dlg)
        except Exception as err:
            self.show_toast(f"Error opening Import Dialog: {err}", color="red")

    def open_asset_editor(self, e=None):
        try:

            from ui.dialogs.asset_editor_dialog import AssetEditorDialog
            dlg = AssetEditorDialog(self)
            self._open_dialog(dlg)
        except Exception as err:
            logger.error(f"Error opening Asset Editor: {traceback.format_exc()}")
            self.show_toast(f"Error opening Asset Editor: {err}", color="red")

    def open_outfit_builder(self, e=None, character_index=None):
        try:

            from ui.dialogs.outfit_builder_dialog import OutfitBuilderDialog
            # character_index=None means global browse mode
            dlg = OutfitBuilderDialog(self, character_index=character_index)
            self._open_dialog(dlg)
        except Exception as err:
            logger.error(f"Error opening Outfit Builder: {traceback.format_exc()}")
            self.show_toast(f"Error opening Outfit Builder: {err}", color="red")

    def _open_dialog(self, dlg):
        if hasattr(self.page, "open"):
            self.page.open(dlg)
        else:
            self.page.overlay.append(dlg)
            dlg.open = True
            self.page.update()

    def open_llm_export(self, e=None): self.show_toast("LLM Export: Coming Soon!")
    def open_llm_content_guide(self, e=None): self.show_toast("Content Guide: Coming Soon!")
    def open_settings(self, e=None): self.show_toast("Settings: Use Sidebar for configuration.")
    
    def open_output_gallery(self, e=None):
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
            logger.error(f"Failed to open gallery: {err}")
            # Fallback to file explorer if something breaks
            self.show_toast(f"Gallery Error, opening folder instead...", color="orange")
            if not self.is_web:
                output_dir = os.path.join(os.getcwd(), "output", "images", "generated_images")
                if os.path.exists(output_dir):
                    PlatformUtils.open_path(output_dir)

    def save_preset(self, e=None): 
        if self.is_web:
            # Web: Use browser localStorage via Flet's client_storage
            try:
                self.page.client_storage.set("promptbuilder_preset", json.dumps(self.state.state))
                self.show_toast("Preset saved to browser storage!")
            except Exception as err:
                self.show_toast(f"Failed to save: {err}", color="red400")
        else:
            # Desktop: File system
            path = os.path.join(os.getcwd(), "preset.json")
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self.state.state, f, indent=2)
                self.show_toast(f"Saved to {path}")
            except Exception as err:
                self.show_toast(f"Failed to save: {err}", color="red400")
            
    def load_preset(self, e=None): 
        if self.is_web:
            # Web: Load from browser localStorage
            try:
                raw = self.page.client_storage.get("promptbuilder_preset")
                if not raw:
                    self.show_toast("No saved preset found in browser", color="orange400")
                    return
                data = json.loads(raw)
            except Exception as err:
                self.show_toast(f"Failed to load: {err}", color="red400")
                return
        else:
            # Desktop: File system
            path = os.path.join(os.getcwd(), "preset.json")
            if not os.path.exists(path):
                self.show_toast("No preset.json found in app directory", color="orange400")
                return
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as err:
                self.show_toast(f"Failed to load: {err}", color="red400")
                return

        # Common validation and apply
        if "selected_characters" in data:
            self.state.state.update(data)
            self.sidebar.populate_data()
            self.refresh_roster()
            self.update_preview()
            self.gallery.refresh()
            self.show_toast("Preset loaded!")
        else:
            self.show_toast("Invalid preset structure", color="red400")

    def reset_all_outfits(self):
        for char in self.state.state["selected_characters"]:
            if hasattr(char, "outfit"):
                char.outfit = "Base"
            else:
                char["outfit"] = "Base"
                
            if hasattr(char, "outfit_traits"):
                char.outfit_traits = []
            else:
                char["outfit_traits"] = []
        self.refresh_roster()
        self.update_preview()
        self.show_toast("Reset all outfits to Base")

    def handle_copy(self, e=None):
        prompt = self.state.get_prompt()
        if prompt:
            if PlatformUtils.copy_to_clipboard(self.page, prompt, is_web=self.is_web):
                self.show_toast("Prompt copied to clipboard!", color="green")
            else:
                self.show_toast("Clipboard copy failed. Check console.", color="red")
        else:
            self.show_toast("No prompt to copy!", color="orange")

    def handle_generate(self, e=None):
        if self.is_web:
            self.show_toast("Image generation requires the desktop app (AI Studio automation).", color="orange")
            return
        
        prompt = self.state.get_prompt()
        if not prompt:
            self.show_toast("No prompt to generate!", color="orange")
            return
            
        if not self.state.ctx.automation_controller:
            self.show_toast("Automation module is still initializing or failed to load. Please wait or check logs.", color="orange")
            return

        # Show visual progress
        self.page.splash = ft.ProgressBar()
        self.page.update()
        self.show_toast("Launching browser for image generation...", color=ThemeManager.colors["accent"])
        
        def on_complete(results):
            self.page.splash = None
            if not results:
                self.show_toast("Generation finished but no images were returned.", color="orange")
                self.page.update()
                return

            path = results[0].get('image_path')
            if not path:
                self.show_toast("Generation finished but image path is missing.", color="orange")
                self.page.update()
                return
            
            def open_file(e):
                PlatformUtils.open_path(path, is_web=self.is_web)

            self.show_toast(f"Generation Complete! Saved to: {os.path.basename(path)}", action="OPEN", on_action=open_file)
            self.page.update()

        def on_error(err):
            self.page.splash = None
            logger.error(f"Generation error: {err}")
            self.show_toast(f"Generation Failed: {str(err)}", color="red")
            self.page.update()

        try:
            self.state.ctx.automation_controller.start_generation(
                count=1,
                match_outfits_prob=0,
                prompts_only=False,
                on_progress=lambda *args: None,
                on_complete=on_complete,
                on_error=on_error,
                fixed_prompt=prompt
            )
        except Exception as err:
            self.page.splash = None
            self.show_toast(f"Could not start generation: {err}", color="red")
            self.page.update()

    def close_dialog(self, dlg):
        dlg.open = False
        self.page.update()

def main(page: ft.Page):
    FletPromptBuilder(page)





if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gemini Prompt Builder")
    parser.add_argument("--web", action="store_true", help="Run in web browser mode")
    parser.add_argument("--port", type=int, default=8550, help="Port for web mode (default: 8550)")
    parser.add_argument("--audit", action="store_true", help="Generate 5 random prompts to the console for auditing")
    args = parser.parse_args()
    
    try:
        if args.audit:
            from logic.app_state import AppState
            import random
            print("Running randomizer audit...")
            state = AppState()
            state.theme_manager = None
            state.load_data()
            print(f"Loaded {len(state.data['characters'])} characters.")
            scenarios = list(state.data['scenarios'].values())
            for i in range(5):
                scen = random.choice(scenarios)
                b, s, c = state.ctx.randomizer._generate_single_candidate(scen, random.randint(1, min(3, scen.max_chars)))
                config_raw = {
                    "base_prompt": "Photography",
                    "scene": b.get("scene", ""),
                    "selected_characters": c,
                    "notes": b.get("notes", ""),
                    "metadata": b
                }
                prompt = state.ctx.builder.generate(config_raw)
                print(f"\n--- ROLL {i+1} (Score: {s}) ---")
                print(f"Scenario: {scen.name}")
                print(f"{prompt}\n")
            sys.exit(0)
            
        if args.web:
            ft.run(main=main, view=ft.AppView.WEB_BROWSER, assets_dir="assets", port=args.port)
        else:
            ft.run(main=main)
    except Exception:
        import traceback
        traceback.print_exc()
        if not args.web:
            input("Press enter to exit...")
