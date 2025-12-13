# -*- coding: utf-8 -*-
"""State management for undo/redo and presets."""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any, Callable, Dict, Optional

from utils import PresetManager, UndoManager, logger


class StateManager:
    """Manages application state, undo/redo, and preset operations.
    
    Coordinates:
    - Undo/redo functionality
    - Preset save/load
    - Configuration import/export
    - State capture and restoration
    """
    
    def __init__(self, root: tk.Tk, preferences_manager):
        """Initialize state manager.
        
        Args:
            root: Tkinter root window
            preferences_manager: PreferencesManager instance
        """
        self.root = root
        self.prefs = preferences_manager
        
        self.undo_manager = UndoManager()
        self.preset_manager = PresetManager()
        
        # Callbacks for state operations
        self.get_state_callback: Optional[Callable[[], Dict[str, Any]]] = None
        self.restore_state_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self.update_preview_callback: Optional[Callable[[], None]] = None
    
    def set_callbacks(self, 
                     get_state: Callable[[], Dict[str, Any]],
                     restore_state: Callable[[Dict[str, Any]], None],
                     update_preview: Callable[[], None]):
        """Set callbacks for state operations.
        
        Args:
            get_state: Function that returns current state dict
            restore_state: Function that restores state from dict
            update_preview: Function that updates preview panel
        """
        self.get_state_callback = get_state
        self.restore_state_callback = restore_state
        self.update_preview_callback = update_preview
    
    def save_state_for_undo(self):
        """Save current state for undo functionality."""
        if not self.get_state_callback:
            logger.warning("Cannot save state: no get_state callback set")
            return
        
        try:
            state = self.get_state_callback()
            self.undo_manager.save_state(state)
            logger.debug("State saved for undo")
        except Exception:
            logger.exception("Error saving state for undo")
    
    def undo(self):
        """Undo last action."""
        if not self.undo_manager.can_undo():
            # Prefer toast if available, then status bar, then modal
            if hasattr(self.root, 'toasts'):
                try:
                    self.root.toasts.notify("Nothing to undo", 'info', 2000)
                except Exception:
                    from utils import logger
                    logger.exception('Auto-captured exception')
                    messagebox.showinfo("Undo", "Nothing to undo")
            elif hasattr(self.root, '_update_status'):
                try:
                    self.root._update_status("Nothing to undo")
                except Exception:
                    from utils import logger
                    logger.exception('Auto-captured exception')
                    messagebox.showinfo("Undo", "Nothing to undo")
            else:
                messagebox.showinfo("Undo", "Nothing to undo")
            return
        
        try:
            state = self.undo_manager.undo()
            if state and self.restore_state_callback:
                self.restore_state_callback(state)
                if self.update_preview_callback:
                    self.update_preview_callback()
                logger.info("Undo performed")
        except Exception:
            logger.exception("Error during undo")
            messagebox.showerror("Undo Error", "Could not undo; see log for details")
    
    def redo(self):
        """Redo last undone action."""
        if not self.undo_manager.can_redo():
            # Prefer toast if available, then status bar, then modal
            if hasattr(self.root, 'toasts'):
                try:
                    self.root.toasts.notify("Nothing to redo", 'info', 2000)
                except Exception:
                    from utils import logger
                    logger.exception('Auto-captured exception')
                    messagebox.showinfo("Redo", "Nothing to redo")
            elif hasattr(self.root, '_update_status'):
                try:
                    self.root._update_status("Nothing to redo")
                except Exception:
                    from utils import logger
                    logger.exception('Auto-captured exception')
                    messagebox.showinfo("Redo", "Nothing to redo")
            else:
                messagebox.showinfo("Redo", "Nothing to redo")
            return
        
        try:
            state = self.undo_manager.redo()
            if state and self.restore_state_callback:
                self.restore_state_callback(state)
                if self.update_preview_callback:
                    self.update_preview_callback()
                logger.info("Redo performed")
        except Exception:
            logger.exception("Error during redo")
            messagebox.showerror("Redo Error", "Could not redo; see log for details")
    
    def save_preset(self) -> bool:
        """Show dialog to save current state as a preset.
        
        Returns:
            True if saved successfully, False otherwise
        """
        if not self.get_state_callback:
            logger.warning("Cannot save preset: no get_state callback set")
            return False
        
        try:
            filepath = filedialog.asksaveasfilename(
                title="Save Preset",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialdir="presets"
            )
            
            if not filepath:
                return False
            
            state = self.get_state_callback()
            self.preset_manager.save_preset(filepath, state)
            
            # Add to recent presets
            preset_name = Path(filepath).stem
            self.prefs.add_recent("recent_presets", preset_name)
            
            # Prefer non-modal status update on the main window when available
            if hasattr(self.root, 'toasts'):
                try:
                    self.root.toasts.notify(f"Preset saved: {Path(filepath).name}", 'success', 3000)
                except Exception:
                    from utils import logger
                    logger.exception('Auto-captured exception')
                    pass
            elif hasattr(self.root, '_update_status'):
                try:
                    self.root._update_status(f"Preset saved: {Path(filepath).name}")
                except Exception:
                    from utils import logger
                    logger.exception('Auto-captured exception')
                    messagebox.showinfo("Success", f"Preset saved: {Path(filepath).name}")
            else:
                messagebox.showinfo("Success", f"Preset saved: {Path(filepath).name}")
            logger.info(f"Preset saved: {filepath}")
            return True
            
        except Exception:
            logger.exception("Error saving preset")
            messagebox.showerror("Save Error", "Could not save preset; see log for details")
            return False
    
    def load_preset(self) -> bool:
        """Show dialog to load a preset.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        if not self.restore_state_callback:
            logger.warning("Cannot load preset: no restore_state callback set")
            return False
        
        try:
            filepath = filedialog.askopenfilename(
                title="Load Preset",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialdir="presets"
            )
            
            if not filepath:
                return False
            
            # Save current state for undo before loading
            self.save_state_for_undo()
            
            self.preset_manager.load_preset(filepath, self.restore_state_callback)
            
            # Add to recent presets
            preset_name = Path(filepath).stem
            self.prefs.add_recent("recent_presets", preset_name)
            
            if self.update_preview_callback:
                self.update_preview_callback()
            
            if hasattr(self.root, 'toasts'):
                try:
                    self.root.toasts.notify(f"Preset loaded: {Path(filepath).name}", 'success', 3000)
                except Exception:
                    from utils import logger
                    logger.exception('Auto-captured exception')
                    pass
            elif hasattr(self.root, '_update_status'):
                try:
                    self.root._update_status(f"Preset loaded: {Path(filepath).name}")
                except Exception:
                    from utils import logger
                    logger.exception('Auto-captured exception')
                    messagebox.showinfo("Success", f"Preset loaded: {Path(filepath).name}")
            else:
                messagebox.showinfo("Success", f"Preset loaded: {Path(filepath).name}")
            logger.info(f"Preset loaded: {filepath}")
            return True
            
        except Exception:
            logger.exception("Error loading preset")
            messagebox.showerror("Load Error", "Could not load preset; see log for details")
            return False
    
    def load_preset_by_name(self, preset_name: str) -> bool:
        """Load a preset by name (from recent list).
        
        Args:
            preset_name: Name of preset (without .json extension)
            
        Returns:
            True if loaded successfully, False otherwise
        """
        preset_path = Path("presets") / f"{preset_name}.json"
        
        if not preset_path.exists():
            messagebox.showerror("Not Found", 
                               f"Preset '{preset_name}' no longer exists.")
            # Remove from recent list
            recent = self.prefs.get("recent_presets", [])
            if preset_name in recent:
                recent.remove(preset_name)
                self.prefs.set("recent_presets", recent)
            return False
        
        try:
            # Save current state for undo
            self.save_state_for_undo()
            
            self.preset_manager.load_preset(str(preset_path), 
                                          self.restore_state_callback)
            
            if self.update_preview_callback:
                self.update_preview_callback()
            
            logger.info(f"Preset loaded: {preset_name}")
            return True
            
        except Exception:
            logger.exception(f"Error loading preset {preset_name}")
            messagebox.showerror("Load Error", "Could not load preset; see log for details")
            return False
    
    def export_config(self) -> bool:
        """Export current configuration to file.
        
        Returns:
            True if exported successfully, False otherwise
        """
        if not self.get_state_callback:
            return False
        
        try:
            filepath = filedialog.asksaveasfilename(
                title="Export Configuration",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if not filepath:
                return False
            
            state = self.get_state_callback()
            self.preset_manager.export_config(filepath, state)
            
            if hasattr(self.root, 'toasts'):
                try:
                    self.root.toasts.notify(f"Configuration exported: {Path(filepath).name}", 'success', 3000)
                except Exception:
                    from utils import logger
                    logger.exception('Auto-captured exception')
                    pass
            elif hasattr(self.root, '_update_status'):
                try:
                    self.root._update_status(f"Configuration exported: {Path(filepath).name}")
                except Exception:
                    from utils import logger
                    logger.exception('Auto-captured exception')
                    messagebox.showinfo("Success", f"Configuration exported: {Path(filepath).name}")
            else:
                messagebox.showinfo("Success", f"Configuration exported: {Path(filepath).name}")
            logger.info(f"Configuration exported: {filepath}")
            return True
            
        except Exception:
            logger.exception("Error exporting configuration")
            messagebox.showerror("Export Error", "Could not export configuration; see log for details")
            return False
    
    def import_config(self) -> bool:
        """Import configuration from file.
        
        Returns:
            True if imported successfully, False otherwise
        """
        if not self.restore_state_callback:
            return False
        
        try:
            filepath = filedialog.askopenfilename(
                title="Import Configuration",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if not filepath:
                return False
            
            # Save current state for undo
            self.save_state_for_undo()
            
            self.preset_manager.import_config(filepath, self.restore_state_callback)
            
            if self.update_preview_callback:
                self.update_preview_callback()
            
            if hasattr(self.root, 'toasts'):
                try:
                    self.root.toasts.notify(f"Configuration imported: {Path(filepath).name}", 'success', 3000)
                except Exception:
                    from utils import logger
                    logger.exception('Auto-captured exception')
                    pass
            elif hasattr(self.root, '_update_status'):
                try:
                    self.root._update_status(f"Configuration imported: {Path(filepath).name}")
                except Exception:
                    from utils import logger
                    logger.exception('Auto-captured exception')
                    messagebox.showinfo("Success", f"Configuration imported: {Path(filepath).name}")
            else:
                messagebox.showinfo("Success", f"Configuration imported: {Path(filepath).name}")
            logger.info(f"Configuration imported: {filepath}")
            return True
            
        except Exception:
            logger.exception("Error importing configuration")
            messagebox.showerror("Import Error", "Could not import configuration; see log for details")
            return False
    
    def can_undo(self) -> bool:
        """Check if undo is available.
        
        Returns:
            True if undo is possible
        """
        return self.undo_manager.can_undo()
    
    def can_redo(self) -> bool:
        """Check if redo is available.
        
        Returns:
            True if redo is possible
        """
        return self.undo_manager.can_redo()
    
    def clear_history(self):
        """Clear undo/redo history."""
        self.undo_manager.clear()
        logger.info("Undo/redo history cleared")
