# -*- coding: utf-8 -*-
"""Main application window."""

import platform
import tkinter as tk
from tkinter import ttk
from typing import Optional

from config import DEFAULT_THEME, DEFAULT_FONT_SIZE
from core.app_context import AppContext
from utils import create_tooltip, logger

from .character_card import CharacterGalleryPanel
from .characters_tab import CharactersTab
from .constants import PREVIEW_UPDATE_THROTTLE_MS
from .controllers.gallery import GalleryController
from .controllers.menu_actions import MenuActions
from .controllers.prompt_controller import PromptController
from .controllers.character_controller import CharacterController
from .controllers.data_controller import DataController
from .controllers.window_state import WindowStateController
from .dialog_manager import DialogManager
from .font_manager import FontManager
from .menu_manager import MenuManager
from .preview_controller import PreviewController
from .preview_panel import PreviewPanel
from .scene_panel import ScenePanel
from .notes_panel import NotesPanel
from .summary_panel import SummaryPanel
from .searchable_combobox import SearchableCombobox
from .state_manager import StateManager
from .widgets import CollapsibleFrame, ScrollableCanvas
from .components.toolbar import ToolbarComponent
from .components.status_bar import StatusBarComponent
from .layout_manager import LayoutManager


class PromptBuilderApp:
    """Main application class for Prompt Builder."""

    def __init__(self, root: tk.Tk, data_loader=None, preferences=None, theme_manager=None, lite_mode=False):
        """Initialize the application.

        Args:
            root: Tkinter root window
            data_loader: Optional DataLoader instance
            preferences: Optional Preferences instance
            theme_manager: Optional ThemeManager instance
            lite_mode: If True, interface is simplified (no gallery)
        """
        self.root = root
        self.lite_mode = lite_mode
        self.root.title("Prompt Builder — Group Picture Generator")

        # Hide window during setup to prevent flickering/resizing
        self.root.withdraw()
        
        # Set a hard minimum size for the entire window - Refactor 1
        self.root.update_idletasks()
        self.root.minsize(1000, 700) # Prevents the "hilarious collapse"

        # Initialize Application Context
        self.ctx = AppContext(self.root)
        self.ctx.initialize_ui_services()

        # Initialize preferences
        self.prefs = preferences if preferences else self.ctx.prefs
        
        # Initialize data loader - if provided, we should probably override context or just use it
        # Ideally AppContext should manage this, but for now we follow the existing pattern
        # If injected, we assign it. If not, we wait for _initialize_data_references
        if data_loader:
            self.data_loader = data_loader
        if theme_manager:
            self.theme_manager = theme_manager

        # Initialize managers (font and state managers will be set up after UI)

        # Initialize managers (font and state managers will be set up after UI)
        self.font_manager: Optional[FontManager] = None
        self.state_manager: Optional[StateManager] = None
        self.menu_manager: Optional[MenuManager] = None
        self.dialog_manager = DialogManager(self.root, self.prefs)

        # Initialize Controllers
        self.prompt_controller = PromptController(self.ctx)
        self.character_controller = CharacterController(self)
        self.data_controller = DataController(self.ctx)
        
        # Throttling for preview updates
        self._throttle_ms = PREVIEW_UPDATE_THROTTLE_MS

        # Build loading screen
        self._build_loading_screen()
        
        # Center and show window
        self._center_window()
        self.root.deiconify()

        # Start async data load
        self.data_controller.load_initial_data(self._on_init_success, self._on_init_error)

    def _build_loading_screen(self):
        """Build a simple loading screen."""
        self.loading_frame = ttk.Frame(self.root)
        self.loading_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Center container
        container = ttk.Frame(self.loading_frame)
        container.place(relx=0.5, rely=0.5, anchor="center")
        
        ttk.Label(
            container, 
            text="Prompt Builder", 
            font=("Lexend", 24, "bold")
        ).pack(pady=(0, 20))
        
        ttk.Label(
            container, 
            text="Loading assets...", 
            font=("Lexend", 12)
        ).pack(pady=(0, 10))
        
        self.loading_progress = ttk.Progressbar(
            container, 
            mode="indeterminate", 
            length=300
        )
        self.loading_progress.pack(pady=10)
        self.loading_progress.start(10)

    def _on_init_success(self):
        """Handle successful initial data load."""
        # Stop progress bar
        self.loading_progress.stop()
        
        # Initialize references
        self._initialize_data_references()
        
        # Sync tags from characters (manual file additions)
        self.data_controller.sync_character_tags()

        # Complete initialization
        self._complete_initialization()
        
        # Remove loading screen with a fade out effect (simulated by just destroying for now)
        self.loading_frame.destroy()
        del self.loading_frame

    def _on_init_error(self, error):
        """Handle initial data load error."""
        logger.exception("Error loading data", exc_info=error)
        self.loading_progress.stop()
        self.dialog_manager.show_error(
            "Error loading data", 
            f"Failed to load application data: {error}\nSee log for details."
        )
        self.root.destroy()

    def _initialize_data_references(self):
        """Initialize local references to context data."""
        self.data_loader = self.ctx.data_loader
        self.characters = self.ctx.characters
        self.base_prompts = self.ctx.base_prompts
        self.scenes = self.ctx.scenes
        self.poses = self.ctx.poses
        self.interactions = self.ctx.interactions
        self.color_schemes = self.ctx.color_schemes
        self.modifiers = self.ctx.modifiers
        self.framing = self.ctx.framing
        # Expose to root for easier access by components
        self.root.modifiers = self.modifiers
        self.root.framing = self.framing
        self.randomizer = self.ctx.randomizer
        
        self.theme_manager = self.ctx.theme_manager
        self.root.theme_manager = self.theme_manager
        self.toasts = self.ctx.toasts

        # Expose toast manager and status updater on the root
        try:
            self.root._update_status = self._update_status
        except Exception:
            logger.exception("Failed to attach status to root")

    def _complete_initialization(self):
        """Complete UI initialization after data is loaded."""
        # Build UI
        self._build_ui()

        # Initialize managers that depend on UI elements
        self._initialize_managers()

        # Create preview controller after UI elements are ready
        try:
            # Will be re-assigned in _initialize_managers once preview_panel exists
            self.preview_controller = None
        except Exception:
            logger.exception("Failed to initialize preview controller placeholder")

        # Keyboard shortcuts are now bound in LayoutManager via MenuManager


        # Auto-detect theme or use saved preference
        theme_to_use = self.prefs.get("last_theme", DEFAULT_THEME)
        if self.prefs.get("auto_theme", False):
            theme_to_use = self._detect_os_theme()
        self._apply_theme(theme_to_use)

        # Restore window geometry and state via WindowStateController
        try:
            self.window_state_controller = WindowStateController(self)
            restored = self.window_state_controller.restore_geometry_and_state()
            saved_geometry = None if not restored else self.prefs.get("window_geometry")
            saved_state = self.prefs.get("window_state")
        except Exception:
            logger.exception("Failed to initialize WindowStateController")
            saved_geometry = None
            saved_state = None

        # Restore UI scale
        saved_scale = self.prefs.get("ui_scale", "Medium")
        self._change_ui_scale(saved_scale)

        # Restore last base prompt
        last_base_prompt = self.prefs.get("last_base_prompt")
        if last_base_prompt and last_base_prompt in self.base_prompts:
            self.characters_tab.set_base_prompt(last_base_prompt)

        # Load characters into gallery
        self.character_gallery.load_characters(self.characters)

        # Initial preview update
        self.update_preview()

        # Position window properly if not restored
        if not saved_geometry:
            self._center_window()

        # Restore window state (maximized/zoomed state)
        if saved_state and saved_state in ("zoomed", "normal", "iconic"):
            try:
                self.root.state(saved_state)
            except tk.TclError as e:
                logger.warning(f"Could not restore window state: {e}")

        # Show welcome dialog for first-time users
        if self.prefs.get("show_welcome", True):
            self.root.after(100, self.dialog_manager.show_welcome)

        # Save state on close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _build_ui(self):
        """Build the main UI layout."""
        self.layout_manager = LayoutManager(self)
        self.layout_manager.build_ui()



    def _initialize_managers(self):
        """Initialize managers that depend on UI elements."""
        # Initialize font manager
        self.font_manager = FontManager(self.root, self.prefs)

        # Register text widgets for font management
        for widget in [
            self.scene_panel.text,
            self.notes_panel.text,
            self.summary_panel.text,
            self.preview_panel.preview_text,
        ]:
            self.font_manager.register_widget(widget)

        # Initialize state manager
        self.state_manager = StateManager(self.root, self.prefs)
        self.state_manager.set_callbacks(
            get_state=self._get_current_state,
            restore_state=self._restore_state,
            update_preview=self.schedule_preview_update,
        )

        # Create preview controller now that preview_panel and characters_tab exist
        try:
            self.preview_controller = PreviewController(
                self.root,
                self.preview_panel,
                self._generate_prompt_or_error,
                lambda: len(self.characters_tab.get_selected_characters()),
                throttle_ms=self._throttle_ms,
            )
        except Exception:
            logger.exception("Failed to create PreviewController")
        # Initialize gallery controller to encapsulate gallery behaviors
        try:
            self.gallery_controller = GalleryController(self)
        except Exception:
            logger.exception("Failed to create GalleryController")



    def randomize_all(self):
        """Generate a random prompt and update the UI."""
        self._update_status("🎲 Randomizing...")
        self._save_state_for_undo()

        config = self.randomizer.randomize(
            num_characters=self.characters_tab.get_num_characters(),
            include_scene=True,
            include_notes=True,
        )

        self.characters_tab.set_selected_characters(config["selected_characters"])
        self.characters_tab.set_base_prompt(config["base_prompt"])

        # Set scene and notes directly
        self.scene_panel.set_text(config.get("scene", ""))
        self.notes_panel.set_text(config.get("notes", ""))

        self.schedule_preview_update()
        self._update_status("✨ Randomized successfully")

    def _center_window(self):
        """Center the window on the screen using current geometry."""
        # Get current geometry string (e.g., "1000x700")
        geom = self.root.geometry()
        # Parse width and height
        if "x" in geom:
            dims = geom.split("+")[0]  # Get "1000x700" part
            width, height = map(int, dims.split("x"))
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
            self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _increase_font(self):
        """Increase font size by user preference."""
        self.font_manager.increase_font_size()

    def _decrease_font(self):
        """Decrease font size by user preference."""
        self.font_manager.decrease_font_size()

    def _reset_font(self):
        """Reset font size to automatic scaling."""
        self.font_manager.reset_font_size()

    def _on_closing(self):
        """Handle window closing - save preferences."""
        # Use WindowStateController to save geometry, state, and sash positions
        if hasattr(self, "window_state_controller"):
            self.window_state_controller.save_geometry_and_state()

        # Save current theme
        if hasattr(self, "menu_manager") and self.menu_manager:
            self.prefs.set("last_theme", self.menu_manager.get_theme())

        # Save last base prompt
        base_prompt = self.characters_tab.get_base_prompt_name()
        if base_prompt:
            self.prefs.set("last_base_prompt", base_prompt)

        # Shutdown preview controller if present
        try:
            if self.preview_controller:
                self.preview_controller.shutdown()
        except Exception:
            logger.exception("Error shutting down preview controller")

        self.root.destroy()

    def _change_theme(self, theme_name):
        """Handle theme change from menu.

        Args:
            theme_name: Name of new theme
        """
        if hasattr(self, "menu_manager") and self.menu_manager:
            self.menu_manager.set_theme(theme_name)
        self._apply_theme(theme_name)

    def _change_ui_scale(self, scale_name):
        """Change the global UI scale.

        Args:
            scale_name: Name of scale ('Small', 'Medium', 'Large')
        """
        scales = {"Small": 0.8, "Medium": 1.0, "Large": 1.25, "Extra Large": 1.5}
        factor = scales.get(scale_name, 1.0)
        
        self.theme_manager.scale_factor = factor
        self.prefs.set("ui_scale", scale_name)
        
        if hasattr(self, "menu_manager"):
            self.menu_manager.ui_scale_var.set(scale_name)
        
        # Apply theme again to update all styles with new scale
        current_theme = self.theme_manager.current_theme or self.prefs.get("last_theme", DEFAULT_THEME)
        self._apply_theme(current_theme)
        
        # Update fonts in text widgets
        if hasattr(self, "font_manager"):
            self.font_manager.update_font_size(int(DEFAULT_FONT_SIZE * factor))

    def _apply_theme(self, theme_name):
        """Apply theme to all UI elements.

        Args:
            theme_name: Name of theme to apply
        """
        theme = self.theme_manager.apply_theme(theme_name)
        panel_bg = theme.get("panel_bg", theme["bg"])
        self._last_panel_bg = panel_bg # Update stored background for hover logic

        # Manual updates for remaining non-modular components
        if hasattr(self, "collapse_all_btn"):
            self.collapse_all_btn.config(bg=panel_bg, fg=theme.get("border", "gray"))
        if hasattr(self, "expand_all_btn"):
            self.expand_all_btn.config(bg=panel_bg, fg=theme.get("border", "gray"))
            
        if hasattr(self, "toolbar_component"):
            self.toolbar_component.apply_theme(theme)

        # Refactor 5: Update status bar
        if hasattr(self, "status_bar_component"):
            self.status_bar_component.apply_theme(theme)
        
        # Update PanedWindow backgrounds for invisible splitters - Refactor 1
        if hasattr(self, "main_paned"):
            try:
                self.main_paned.config(bg=panel_bg)
                for child in self.main_paned.winfo_children():
                    if isinstance(child, tk.PanedWindow):
                        child.config(bg=panel_bg)
            except Exception:
                pass

        # Apply to character gallery (use controller if available)
        if hasattr(self, "gallery_controller") and self.gallery_controller:
            try:
                self.gallery_controller.apply_theme(theme)
            except Exception:
                logger.exception("Failed to apply theme via GalleryController")
        elif hasattr(self, "character_gallery"):
            try:
                self.character_gallery.theme_colors = theme
                self.character_gallery._refresh_display()
            except Exception:
                logger.exception("Failed to apply theme to character_gallery")

        # Apply theme to toasts
        if hasattr(self, "toasts"):
            try:
                self.toasts.apply_theme(theme)
            except Exception:
                from utils import logger as _logger

                _logger.debug("Failed to apply theme to toasts", exc_info=True)

        # Refactor 3: Propagate theme to open dialogs
        if hasattr(self, "dialog_manager"):
            self.dialog_manager.apply_theme(theme)

    def schedule_preview_update(self):
        """Schedule a preview update with adaptive throttling."""
        # Adaptive throttling - faster for simpler prompts
        num_chars = len(self.characters_tab.get_selected_characters())
        delay = 50 if num_chars <= 2 else self._throttle_ms

        if self.preview_controller:
            try:
                self.preview_controller.schedule_update(delay)
            except Exception:
                logger.exception("Failed to schedule preview update via controller")
        else:
            # Fallback: do synchronous update after delay
            try:
                self.root.after(delay, lambda: self.update_preview())
            except Exception:
                logger.exception("Failed to schedule synchronous preview update")

    # Preview submission is handled by PreviewController now.

    def update_preview(self):
        """Update the preview panel with current prompt."""
        config = self._get_current_state()
        prompt = self.prompt_controller.generate_or_error(config)
        self.preview_panel.update_preview(prompt)
        
        # Update summary only if not being manually edited
        if not self.summary_panel.is_modified:
            summary = self.prompt_controller.generate_summary(config)
            self.summary_panel.set_text(summary)
        
        num_chars = len(config["selected_characters"])
        self._update_status(f"Ready • {num_chars} character(s) selected")

        # Update gallery highlights
        if hasattr(self, "character_gallery") and hasattr(self.character_gallery, "update_used_status"):
            selected_names = [c["name"] for c in config["selected_characters"]]
            self.character_gallery.update_used_status(selected_names)

    def _update_status(self, message):
        """Update status bar message.

        Args:
            message: Status message to display
        """
        if hasattr(self, "status_bar_component"):
            self.status_bar_component.update_status(message)

    def _generate_prompt_or_error(self):
        """Bridge for PreviewController/Panel."""
        return self.prompt_controller.generate_or_error(self._get_current_state())

    def _validate_prompt(self):
        """Bridge for PreviewController/Panel."""
        return self.prompt_controller.validate(self.characters_tab.get_selected_characters())

    def _generate_prompt(self):
        """Bridge for PreviewController/Panel."""
        return self.prompt_controller.generate_full_prompt(self._get_current_state())

    def _reload_interaction_templates(self):
        """Reload interaction templates from file."""
        try:
            # Reload interactions from markdown file
            self.interactions = self.data_loader.load_interactions()
            
            # Notify notes panel
            self.notes_panel.update_presets(self.interactions)

            logger.info("Interaction templates reloaded successfully")
        except Exception:
            logger.exception("Error reloading interaction templates")

    def _create_new_character(self):
        """Open dialog to create a new character."""
        try:
            from .character_creator import CharacterCreatorDialog
            dialog = CharacterCreatorDialog(self.root, self.data_loader, self.reload_data)
            dialog.show()
        except Exception:
            logger.exception("Failed to open Character Creator")

    def _create_new_interaction(self):
        """Open dialog to create a new interaction template."""
        from .interaction_creator import InteractionCreatorDialog

        dialog = InteractionCreatorDialog(
            self.root, self.data_loader, self._reload_interaction_templates
        )
        dialog.show()

    def _create_new_scene(self):
        """Open dialog to create a new scene."""
        from .scene_creator import SceneCreatorDialog

        dialog = SceneCreatorDialog(self.root, self.data_loader, self.reload_data)
        dialog.show()

    def _open_theme_editor(self):
        """Open the Theme Editor dialog to create/edit custom themes."""
        try:
            from .theme_editor import ThemeEditorDialog

            dlg = ThemeEditorDialog(
                self.root,
                self.theme_manager,
                self.prefs,
                on_theme_change=self.menu_manager.refresh_theme_menu,
            )
            dlg.show()
        except Exception:
            logger.exception("Failed to open Theme Editor")

    def reload_data(self):
        """Reload all data from markdown files asynchronously."""
        self._update_status("🔄 Reloading data...")
        self.root.config(cursor="watch")
        
        # Show reloading overlay
        self._show_reload_overlay()

        # Start async load via controller
        self.data_controller.reload_all_data(self._on_reload_success, self._on_reload_error)

    def _show_reload_overlay(self):
        """Show a modal overlay during reload."""
        self.reload_overlay = ttk.Frame(self.root)
        self.reload_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Get theme colors safely
        try:
            theme = self.theme_manager.themes.get(self.theme_manager.current_theme, {})
            panel_bg = theme.get("panel_bg", theme.get("bg", "#1e1e1e"))
            accent = theme.get("accent", "#0078d7")
        except Exception:
            panel_bg = "#1e1e1e"
            accent = "#0078d7"

        # Semi-transparent background effect (simulated with a label if needed, or just opaque)
        # For simplicity, we use an opaque frame with a label
        
        container = ttk.Frame(self.reload_overlay)
        container.place(relx=0.5, rely=0.5, anchor="center")
        
        loading_label = tk.Label(
            container, text="RELOADING...", font=("Lexend", 16, "bold"),
            bg=panel_bg, fg=accent
        )
        loading_label.pack()
        
        self.reload_progress = ttk.Progressbar(container, mode="indeterminate", length=200)
        self.reload_progress.pack(pady=10)
        self.reload_progress.start(10)

    def _hide_reload_overlay(self):
        """Hide the reload overlay."""
        if hasattr(self, "reload_overlay"):
            self.reload_progress.stop()
            self.reload_overlay.destroy()
            del self.reload_overlay

    def _on_reload_success(self):
        """Handle successful data reload."""
        try:
            # Migration logic (preserved from original)
            self._handle_theme_migration()
            
            # Update local references
            self._initialize_data_references()
            
            # Reload themes (synchronous, but usually fast)
            if hasattr(self, "theme_manager") and self.theme_manager:
                self.theme_manager.reload_md_themes()

            # Sync tags from characters
            try:
                added = self.data_loader.sync_tags()
                if added:
                    logger.info(f"Reload: Added {added} new tags from character files.")
            except Exception:
                logger.exception("Error syncing tags on reload")

            # Update UI
            self._update_ui_after_reload()
            
            self._hide_reload_overlay()
            self.root.config(cursor="")
            self._update_status("✅ Data reloaded successfully")
            self.dialog_manager.show_info("Success", "Data reloaded successfully!")
            
        except Exception:
            logger.exception("Error during reload post-processing")
            self._hide_reload_overlay()
            self.root.config(cursor="")
            self.dialog_manager.show_error("Reload Error", "Error updating UI after reload.")

    def _on_reload_error(self, error):
        """Handle data reload error."""
        logger.exception("Error reloading data", exc_info=error)
        self._hide_reload_overlay()
        self.root.config(cursor="")
        self.dialog_manager.show_error(
            "Reload Error", f"Failed to reload data: {error}\nSee log for details."
        )
        self._update_status("❌ Error loading data")

    def _handle_theme_migration(self):
        """Handle one-time theme migration."""
        try:
            migrated = False
            if hasattr(self, "theme_manager") and self.theme_manager:
                migrated = self.theme_manager.migrate_from_prefs(self.prefs)
            if migrated:
                try:
                    if hasattr(self, "menu_manager") and self.menu_manager:
                        self.menu_manager.refresh_theme_menu()
                except Exception:
                    logger.debug("Failed to refresh theme menu after migration")
        except Exception:
            logger.exception("Theme migration failed during reload")

    def _update_ui_after_reload(self):
        """Update UI components with new data."""
        # Update character selection validity
        new_chars_keys = set(self.characters.keys())
        selected = self.characters_tab.get_selected_characters()
        updated_selected = []
        chars_removed = False

        for c in selected:
            if c["name"] in new_chars_keys:
                c.setdefault("pose_category", "")
                c.setdefault("pose_preset", "")
                c.setdefault("action_note", "")
                updated_selected.append(c)
            else:
                chars_removed = True

        self.characters_tab.selected_characters = updated_selected

        if chars_removed:
            self.dialog_manager.show_info(
                "Reload Info",
                "Some previously selected characters were removed as they no longer exist in the updated data.",
            )

        # Reload data in tabs/panels
        self.characters_tab.load_data(self.characters, self.base_prompts, self.poses, self.scenes)
        self.scene_panel.update_presets(self.scenes)
        self.notes_panel.update_presets(self.interactions)

        # Re-apply theme
        current = self.prefs.get("last_theme") or None
        if current:
            try:
                self._apply_theme(current)
                if hasattr(self, "menu_manager") and self.menu_manager:
                    self.menu_manager.refresh_theme_menu()
            except Exception:
                logger.debug("Failed to re-apply theme after reload")

        # Reload character gallery
        if hasattr(self, "gallery_controller") and self.gallery_controller:
            try:
                self.gallery_controller.load_characters(self.characters)
            except Exception:
                logger.exception("Failed to reload gallery via GalleryController")
        elif hasattr(self, "character_gallery"):
            try:
                self.character_gallery.load_characters(self.characters)
            except Exception:
                logger.exception("Failed to reload character_gallery")

        self.schedule_preview_update()



    def _import_from_summary_box(self):
        """Parse and apply the text currently in the summary box."""
        raw_text = self.summary_panel.get_text()
        if not raw_text:
            return

        available_chars = list(self.characters.keys())
        from utils.text_parser import TextParser
        
        try:
            config = TextParser.parse_import_text(raw_text, available_chars)
            self._save_state_for_undo()
            self._restore_state(config)
            self.summary_panel.is_modified = False
            # Reset background
            self._apply_theme(self.theme_manager.current_theme) 
            self._update_status("Applied changes from summary console")
        except Exception as e:
            logger.error(f"Failed to parse summary box: {e}")
            self._update_status("❌ Error parsing summary text")

    def randomize_all(self):
        """Generate a random prompt and update the UI."""
        self._update_status("🎲 Randomizing...")
        self._save_state_for_undo()

        config = self.randomizer.randomize(
            num_characters=self.characters_tab.get_num_characters(),
            include_scene=True,
            include_notes=True,
        )

        self.characters_tab.set_selected_characters(config["selected_characters"])
        self.characters_tab.set_base_prompt(config["base_prompt"])

        # Set scene and notes directly via panels
        self.scene_panel.set_text(config.get("scene", ""))
        self.notes_panel.set_text(config.get("notes", ""))

        self.schedule_preview_update()
        self._update_status("✨ Randomized successfully")

    def _center_window(self):
        """Center the window on the screen using current geometry."""
        # Get current geometry string (e.g., "1000x700")
        geom = self.root.geometry()
        # Parse width and height
        if "x" in geom:
            dims = geom.split("+")[0]  # Get "1000x700" part
            width, height = map(int, dims.split("x"))
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
            self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _increase_font(self):
        """Increase font size by user preference."""
        self.font_manager.increase_font_size()

    def _decrease_font(self):
        """Decrease font size by user preference."""
        self.font_manager.decrease_font_size()

    def _reset_font(self):
        """Reset font size to automatic scaling."""
        self.font_manager.reset_font_size()

    def _on_closing(self):
        """Handle window closing - save preferences."""
        # Use WindowStateController to save geometry, state, and sash positions
        if hasattr(self, "window_state_controller"):
            self.window_state_controller.save_geometry_and_state()

        # Save current theme
        if hasattr(self, "menu_manager") and self.menu_manager:
            self.prefs.set("last_theme", self.menu_manager.get_theme())

        # Save last base prompt
        base_prompt = self.characters_tab.get_base_prompt_name()
        if base_prompt:
            self.prefs.set("last_base_prompt", base_prompt)

        # Shutdown preview controller if present
        try:
            if self.preview_controller:
                self.preview_controller.shutdown()
        except Exception:
            logger.exception("Error shutting down preview controller")

        self.root.destroy()

    def _get_current_state(self):
        """Get current application state for undo/redo.

        Returns:
            Dictionary of current state
        """
        return {
            "selected_characters": self.characters_tab.get_selected_characters(),
            "base_prompt": self.characters_tab.get_base_prompt_name(),
            "scene": self.scene_panel.get_text(),
            "notes": self.notes_panel.get_text(),
        }

    def _restore_state(self, state):
        """Restore application state from dictionary.

        Args:
            state: State dictionary
        """
        if not state:
            return

        # Restore characters
        self.characters_tab.set_selected_characters(state.get("selected_characters", []))

        # Restore base prompt
        base_prompt = state.get("base_prompt", "")
        if base_prompt:
            self.characters_tab.set_base_prompt(base_prompt)

        # Restore scene
        self.scene_panel.set_text(state.get("scene", ""))

        # Restore notes
        self.notes_panel.set_text(state.get("notes", ""))

        self.update_preview()

    def _save_state_for_undo(self):
        """Save current state for undo."""
        self.state_manager.save_state_for_undo()

    def _undo(self):
        """Undo last action."""
        success = self.state_manager.undo()
        if success:
            self._update_status("Undo successful")
        else:
            self._update_status("Nothing to undo")

    def _redo(self):
        """Redo last undone action."""
        success = self.state_manager.redo()
        if success:
            self._update_status("Redo successful")
        else:
            self._update_status("Nothing to redo")

    def _save_preset(self):
        """Save current configuration as a preset."""
        success = self.state_manager.save_preset()
        if success:
            self._update_status("Preset saved")

    def _load_preset(self):
        """Load a preset configuration."""
        success = self.state_manager.load_preset()
        if success:
            self._update_status("Preset loaded successfully")

    def _export_config(self):
        """Export current configuration to JSON file."""
        self.state_manager.export_config()

    def _import_config(self):
        """Import configuration from JSON file."""
        success = self.state_manager.import_config()
        if success:
            self._update_status("Configuration imported successfully")

    def _clear_all_characters(self):
        """Clear all selected characters."""
        if not self.characters_tab.get_selected_characters():
            return

        if self.dialog_manager.ask_yes_no("Clear All", "Remove all characters from the prompt?"):
            self._save_state_for_undo()
            self.characters_tab.set_selected_characters([])
            self._update_status("All characters cleared")

    def _reset_all_outfits(self):
        """Reset all characters to their base/first outfit."""
        characters = self.characters_tab.get_selected_characters()
        if not characters:
            return

        if self.dialog_manager.ask_yes_no(
            "Reset Outfits", "Reset all characters to their default outfit?"
        ):
            self._save_state_for_undo()
            for char in characters:
                char_def = self.characters.get(char["name"], {})
                outfits = char_def.get("outfits", {})
                if "Base" in outfits:
                    char["outfit"] = "Base"
                elif outfits:
                    char["outfit"] = sorted(list(outfits.keys()))[0]
            self.characters_tab.set_selected_characters(characters)
            self._update_status("All outfits reset to default")

    def _apply_same_pose_to_all(self):
        """Apply same pose to all characters."""
        characters = self.characters_tab.get_selected_characters()
        if not characters:
            return

        # Create dialog to select pose
        dialog = tk.Toplevel(self.root)
        dialog.title("Apply Pose to All")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(
            dialog, text="Select pose to apply to all characters:", font=("Lexend", 10, "bold")
        ).pack(pady=10, padx=10)

        frame = ttk.Frame(dialog)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(frame, text="Category:").grid(row=0, column=0, sticky="w", pady=5)
        cat_var = tk.StringVar()
        cat_combo = SearchableCombobox(
            frame, 
            values=[""] + sorted(list(self.poses.keys())),
            textvariable=cat_var,
            on_select=lambda val: update_presets(),
            placeholder="Search category...",
            width=20
        )
        cat_combo.grid(row=0, column=1, sticky="ew", pady=5, padx=(5, 0))

        ttk.Label(frame, text="Preset:").grid(row=1, column=0, sticky="w", pady=5)
        preset_var = tk.StringVar()
        preset_combo = SearchableCombobox(
            frame,
            values=[""],
            textvariable=preset_var,
            on_select=lambda val: None,
            placeholder="Search preset...",
            width=20
        )
        preset_combo.grid(row=1, column=1, sticky="ew", pady=5, padx=(5, 0))

        def update_presets():
            cat = cat_var.get()
            if cat and cat in self.poses:
                preset_combo.set_values([""] + sorted(list(self.poses[cat].keys())))
            else:
                preset_combo.set_values([""])
            preset_var.set("")
            dialog.update_idletasks()

        frame.columnconfigure(1, weight=1)

        def apply_pose():
            cat = cat_var.get()
            preset = preset_var.get()
            if cat or preset:
                self._save_state_for_undo()
                for char in characters:
                    char["pose_category"] = cat
                    char["pose_preset"] = preset
                self.characters_tab.set_selected_characters(characters)
                self._update_status(f"Applied pose to {len(characters)} character(s)")
                dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(btn_frame, text="Apply", command=apply_pose).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side="right", padx=2)

        dialog.wait_window()

    def _detect_os_theme(self):
        """Detect OS theme preference.

        Returns:
            Theme name based on OS settings
        """
        try:
            if platform.system() == "Windows":
                import winreg

                try:
                    registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                    key = winreg.OpenKey(
                        registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
                    )
                    value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                    winreg.CloseKey(key)
                    return "Light" if value == 1 else "Dark"
                except (OSError, FileNotFoundError) as e:
                    logger.debug(f"Could not read Windows theme registry: {e}")
            elif platform.system() == "Darwin":  # macOS
                import subprocess

                try:
                    result = subprocess.run(
                        ["defaults", "read", "-g", "AppleInterfaceStyle"],
                        capture_output=True,
                        text=True,
                        timeout=2.0,  # 2 second timeout
                        check=False,  # Don't raise on non-zero exit
                    )
                    return "Light" if result.returncode != 0 else "Dark"
                except (FileNotFoundError, subprocess.TimeoutExpired) as e:
                    logger.debug(f"macOS theme detection failed: {e}")
        except Exception as e:
            logger.debug(f"Failed to detect OS theme: {e}")

        return DEFAULT_THEME

    def _clear_interface(self):
        """Clear UI inputs: preview, notes, scene, and selected characters."""
        try:
            # Clear preview panel
            if hasattr(self, "preview_panel"):
                try:
                    self.preview_panel.clear_preview()
                except Exception:
                    from utils import logger as _logger

                    _logger.debug(
                        "Could not delete temp file while replacing content", exc_info=True
                    )

            # Clear panels via their internal methods
            try:
                self.scene_panel.set_text("")
            except Exception:
                from utils import logger as _logger
                _logger.debug("Failed to clear scene panel", exc_info=True)

            try:
                self.notes_panel.set_text("")
            except Exception:
                from utils import logger as _logger
                _logger.debug("Failed to clear notes panel", exc_info=True)

            try:
                self.summary_panel.set_text("")
            except Exception:
                from utils import logger as _logger
                _logger.debug("Failed to clear summary panel", exc_info=True)

            # Clear selected characters
            if hasattr(self, "characters_tab"):
                try:
                    self.characters_tab.set_selected_characters([])
                except Exception:
                    from utils import logger as _logger

                    _logger.debug("Failed to clear selected characters", exc_info=True)

            self._update_status("Interface cleared")
        except Exception:
            from utils import logger

            logger.exception("Auto-captured exception")
            # Best-effort; if clearing fails, show status
            self._update_status("Interface cleared")

    def _toggle_auto_theme(self):
        """Toggle auto theme detection."""
        auto = self.menu_manager.get_auto_theme() if hasattr(self, "menu_manager") else False
        self.prefs.set("auto_theme", auto)
        if auto:
            detected_theme = self._detect_os_theme()
            self._change_theme(detected_theme)
            self._update_status(f"Auto-detected theme: {detected_theme}")

    def _toggle_character_gallery(self):
        """Toggle visibility of the character gallery."""
        if self.lite_mode or not self.gallery_frame:
            return

        if self.gallery_visible:
            self.main_paned.forget(self.gallery_frame)
            self.gallery_visible = False
        else:
            self.main_paned.add(self.gallery_frame, before=self.main_paned.panes()[0], width=300, minsize=200)
            self.gallery_visible = True
        
        # Save preference
        self.prefs.set("gallery_visible", self.gallery_visible)
        
        # Update menu checkmark
        if hasattr(self, "menu_manager") and self.menu_manager:
            self.menu_manager.set_gallery_visible(self.gallery_visible)
        
        # Delegate gallery show/hide to controller when available
        if hasattr(self, "gallery_controller") and self.gallery_controller:
            try:
                self.gallery_controller.toggle_visibility(
                    self.gallery_visible, self.characters if self.gallery_visible else None
                )
            except Exception:
                logger.exception("Failed to toggle gallery via GalleryController")
        else:
            if self.gallery_visible:
                # Show gallery - insert at position 0 (leftmost)
                try:
                    panes = self.main_paned.panes()
                    if panes:
                        self.main_paned.add(self.gallery_frame, before=panes[0], width=300)
                    else:
                        self.main_paned.add(self.gallery_frame, width=300)
                    # Reload characters in case they changed
                    self.character_gallery.load_characters(self.characters)
                except tk.TclError:
                    # Already added
                    pass
            else:
                # Hide gallery
                try:
                    self.main_paned.forget(self.gallery_frame)
                except tk.TclError:
                    # Not in paned window
                    pass

    def _on_gallery_character_selected(self, character_name):
        """Handle character selection from gallery.

        Args:
            character_name: Name of selected character
        """
        # Add character to the characters tab
        self.characters_tab.add_character_from_gallery(character_name)
        self.schedule_preview_update()
