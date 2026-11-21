import flet as ft
import os
import sys
import json
import subprocess
import traceback
import argparse
# Add the current directory and src to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from core.app_state import AppState
from utils import logger
from core.flet_theme_manager import ThemeManager
from logic.interaction_logic import InteractionLogic
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
            if hasattr(self.page, "window") and self.page.window:
                self.page.window.width = 1600
                self.page.window.height = 900
            else:
                try:
                    self.page.window_width = 1600
                    self.page.window_height = 900
                except Exception:
                    pass
            
        self.page.on_resized = self.handle_resize
        
        # Typography: Modern Google Fonts
        self.page.fonts = {
            "Inter": "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/static/Inter-Regular.ttf",
            "Inter-Bold": "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/static/Inter-Bold.ttf",
            "Kanit": "https://raw.githubusercontent.com/google/fonts/main/ofl/kanit/Kanit-Bold.ttf",
        }
        
        # Initialize Logic & Controllers
        self.state = AppState(page)
        self.interaction_logic = InteractionLogic(self.state)
        # Controller layer (New)
        self.char_controller = CharacterController(self.state)
        # Legacy backup/internal logic
        self.character_logic = self.char_controller.logic 
        
        # Initialize Theme
        ThemeManager.apply_theme(self.page, "Dark")
        
        # Load lightweight character metadata first (30ms) so gallery populates immediately
        self.state.load_metadata_fast()
        
        self.build_ui()
        self.load_initial_data()


    def handle_resize(self, e):
        """Handle window resize events to ensure UI components re-layout."""
        if hasattr(self, "sidebar"):
            self.sidebar.update()
        if hasattr(self, "roster"):
            self.roster.update()
        if hasattr(self, "gallery"):
            self.gallery.update()
        self.page.update()


    def build_ui(self):
        # Instantiate Modular Sections
        self.toolbar = ToolbarSection(self)
        self.gallery = GallerySection(self)
        # Pre-populate gallery immediately from fast metadata on first frame
        self.gallery.refresh(update_ui=False)
        self.roster = RosterSection(self)
        self.sidebar = SidebarSection(self)
        self.console = ConsoleSection(self)
        self.dashboard = DashboardSection(self)
        
        # Workspace Area split side-by-side: balanced flex prevents console from crushing roster
        self.roster.expand = 6
        self.console.expand = 5
        self.sidebar.expand = True
        
        left_column = ft.Column(
            [
                self.roster,
                self.console
            ],
            expand=7,
            spacing=10
        )
        
        right_column = ft.Column(
            [
                self.sidebar
            ],
            expand=5,
            spacing=0
        )
        
        self.workspace = ft.Row(
            [
                left_column,
                right_column
            ],
            spacing=16,
            expand=True
        )
        
        # Main Layout: edge-to-edge Toolbar + padded workspace
        self.layout = ft.Column(
            [
                self.toolbar,
                ft.Container(
                    content=ft.Column(
                        [
                            self.gallery,
                            ft.Container(height=10), # Spacer
                            self.workspace
                        ],
                        spacing=0,
                        expand=True
                    ),
                    padding=ft.Padding.only(left=16, right=16, bottom=16),
                    expand=True
                )
            ],
            spacing=0,
            expand=True
        )

        self.page.add(self.layout)
        
        # Overlay
        self.page.overlay.append(self.dashboard)
        


    def load_initial_data(self):
        async def _task():
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
            
        self.page.run_task(_task)

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
            if any(c.name == name for c in self.state.state["selected_characters"]):
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
        format_type = getattr(self.console, "format_mode", "markdown") if hasattr(self, "console") else "markdown"
        self.console.update_output(self.state.get_prompt(format_type=format_type))
        self.sidebar.update_summary(self.state.get_summary())
        self.page.update()

    def handle_solo_randomize(self, index):
        if not self.state.ctx.randomizer: 
            self.show_toast("Randomizer not available.", color="orange")
            return
        if not (0 <= index < len(self.state.state["selected_characters"])): return
        
        char_entry = self.state.state["selected_characters"][index]
        name = char_entry.name
        
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
        prev_chars = list(self.state.state["selected_characters"])
        if not prev_chars:
            return
        self._last_cleared_roster = prev_chars
        self.state.state["selected_characters"] = []
        self.refresh_roster()
        self.gallery.refresh()
        self.update_preview()

        def undo_clear(e):
            if hasattr(self, "_last_cleared_roster") and self._last_cleared_roster:
                self.state.state["selected_characters"] = list(self._last_cleared_roster)
                self._last_cleared_roster = []
                self.refresh_roster()
                self.gallery.refresh()
                self.update_preview()
                self.show_toast("Roster restored")

        self.show_toast(
            f"Cleared {len(prev_chars)} character(s)", 
            action="UNDO", 
            on_action=undo_clear
        )

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

    def _safe_open_dialog(self, dialog_class, *args, **kwargs):
        """Unified helper to instantiate and open a dialog with error handling."""
        try:
            dlg = dialog_class(self, *args, **kwargs)
            self._open_dialog(dlg)
            if hasattr(dlg, "animate_intro"):
                import asyncio
                async def _animate():
                    await asyncio.sleep(0.05)
                    try:
                        dlg.animate_intro()
                    except Exception:
                        pass
                self.page.run_task(_animate)
            return dlg
        except Exception as err:
            logger.error(f"Error opening {dialog_class.__name__}: {traceback.format_exc()}")
            self.show_toast(f"Error opening {dialog_class.__name__}: {err}", color="red")
            return None

    def open_automation_dialog(self, e=None):
        from ui.dialogs.automation_dialog import AutomationDialog
        self._safe_open_dialog(AutomationDialog)

    def open_import_from_text(self, e=None):
        from ui.dialogs.import_text_dialog import ImportTextDialog
        self._safe_open_dialog(ImportTextDialog)

    def open_asset_editor(self, e=None):
        from ui.dialogs.asset_editor_dialog import AssetEditorDialog
        self._safe_open_dialog(AssetEditorDialog)

    def open_ai_character_creator(self, e=None):
        from ui.dialogs.ai_character_dialog import AICharacterDialog
        self._safe_open_dialog(AICharacterDialog)

    def open_outfit_builder(self, e=None, character_index=None):
        from ui.dialogs.outfit_builder_dialog import OutfitBuilderDialog
        self._safe_open_dialog(OutfitBuilderDialog, character_index=character_index)

    def _open_dialog(self, dlg):
        if hasattr(self.page, "show_dialog"):
            self.page.show_dialog(dlg)
        elif hasattr(self.page, "open"):
            self.page.open(dlg)
        else:
            self.page.overlay.append(dlg)
            dlg.open = True
            self.page.update()

    def open_context_studio(self, e=None, initial_tab="scenes"):
        from ui.dialogs.scene_interaction_dialog import SceneInteractionDialog
        self._safe_open_dialog(SceneInteractionDialog, initial_tab=initial_tab)

    def open_llm_export(self, e=None):
        from ui.dialogs.llm_dialogs import LLMExportDialog
        self._safe_open_dialog(LLMExportDialog)

    def open_asset_studio(self, e=None):
        from ui.dialogs.asset_generator_dialog import AssetGeneratorDialog
        self._safe_open_dialog(AssetGeneratorDialog)

    def open_settings(self, e=None):
        from ui.dialogs.settings_dialog import SettingsDialog
        self._safe_open_dialog(SettingsDialog)
    
    def open_output_gallery(self, e=None):
        from ui.dialogs.output_gallery import OutputGalleryDialog
        if not self._safe_open_dialog(OutputGalleryDialog):
            # Fallback to file explorer if something breaks
            self.show_toast("Gallery Error, opening folder instead...", color="orange")
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
            char.outfit = "Base"
            char.outfit_traits = []
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
        # We allow this in web mode because the user is typically running the server locally
        # If it were a remote server, Playwright would just open on the server desktop.
        
        # Priority 1: Use the text currently in the console (useful for Gemma enhancements)
        prompt = self.console.output_field.value
        
        # Priority 2: Fallback to generating from state if console is empty
        if not prompt:
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
        if hasattr(self.page, "pop_dialog"):
            try:
                self.page.pop_dialog()
                return
            except Exception:
                pass
        if hasattr(self.page, "close"):
            try:
                self.page.close(dlg)
                return
            except Exception:
                pass
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
            from core.app_state import AppState
            print("Running randomizer audit...")
            # Note: AppState needs a page object for some logic, but audit mode might work without it
            state = AppState(None) 
            state.load_data()
            print(f"Loaded {len(state.ctx.characters_metadata)} characters.")
            # ... rest of audit logic ...
            sys.exit(0)
            
        # Launching the app
        if args.web:
            ft.run(main=main, view=ft.AppView.WEB_BROWSER, assets_dir="assets", port=args.port)
        else:
            ft.run(main=main, assets_dir="assets")
        
    except Exception:
        import traceback
        traceback.print_exc()
        if not args.web:
            input("Press enter to exit...")
