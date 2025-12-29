"""Application context for managing global state and services."""
import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any, TYPE_CHECKING

from logic import DataLoader, PromptRandomizer
from themes import ThemeManager
from utils import PreferencesManager, logger
from .exceptions import DataLoadError

if TYPE_CHECKING:
    from ui.toast import ToastManager

class AppContext:
    """Holds references to global managers and data."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.prefs = PreferencesManager()
        self.data_loader = DataLoader()
        
        # UI Managers
        self.theme_manager: Optional[ThemeManager] = None
        self.toasts: Optional["ToastManager"] = None
        self.style: Optional[ttk.Style] = None
        
        # Data
        self.characters: Dict[str, Any] = {}
        self.base_prompts: Dict[str, str] = {}
        self.scenes: Dict[str, Any] = {}
        self.poses: Dict[str, Any] = {}
        self.interactions: Dict[str, Any] = {}
        self.color_schemes: Dict[str, Any] = {}
        self.modifiers: Dict[str, str] = {}
        self.framing: Dict[str, str] = {}
        
        self.randomizer: Optional[PromptRandomizer] = None

    def initialize_ui_services(self):
        """Initialize UI services that require the root window."""
        # Import here to avoid circular dependency with ui package
        from ui.toast import ToastManager
        
        self.style = ttk.Style()
        self.theme_manager = ThemeManager(self.root, self.style)
        self.toasts = ToastManager(self.root, self.theme_manager)
        
        # Attach to root for legacy/helper access
        self.root.toasts = self.toasts

    def load_data(self):
        """Load all application data."""
        try:
            self.characters = self.data_loader.load_characters()
            self.base_prompts = self.data_loader.load_base_prompts()
            self.scenes = self.data_loader.load_presets("scenes.md")
            self.poses = self.data_loader.load_presets("poses.md")
            self.interactions = self.data_loader.load_interactions()
            self.color_schemes = self.data_loader.load_color_schemes()
            self.modifiers = self.data_loader.load_modifiers()
            self.framing = self.data_loader.load_framing()
            
            self.randomizer = PromptRandomizer(
                self.characters, 
                self.base_prompts, 
                self.poses, 
                self.scenes, 
                self.interactions,
                self.color_schemes,
                self.modifiers,
                self.framing
            )
        except Exception as e:
            # Wrap any loading error into DataLoadError if it isn't already
            if isinstance(e, DataLoadError):
                raise
            logger.exception("Data loading failed")
            raise DataLoadError(f"Failed to load application data: {e}") from e

    def load_data_async(self, on_success, on_error):
        """Load data in a background thread.

        Args:
            on_success: Callback to run on the main thread when loading succeeds.
            on_error: Callback to run on the main thread when loading fails (receives exception).
        """
        import threading

        def _load_worker():
            try:
                self.load_data()
                # Schedule success callback on main thread
                self.root.after(0, on_success)
            except Exception as e:
                # Schedule error callback on main thread
                self.root.after(0, lambda: on_error(e))

        thread = threading.Thread(target=_load_worker, daemon=True)
        thread.start()
