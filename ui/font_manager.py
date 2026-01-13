# -*- coding: utf-8 -*-
"""Font size management and adaptive scaling."""

import tkinter as tk
from typing import List, Optional

from utils import logger

from core.config import DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE
from ui.constants import (
    FONT_SIZE_BREAKPOINTS,
    MAX_FONT_SIZE,
    MIN_FONT_SIZE,
    RESIZE_SIGNIFICANT_CHANGE_PX,
    RESIZE_THROTTLE_MS,
)


class FontManager:
    """Manages font sizing and adaptive scaling based on window size.

    Handles:
    - Automatic font scaling based on window width
    - Manual font size adjustments
    - Throttled resize events
    - Font application to text widgets
    """

    def __init__(self, root: tk.Tk, preferences_manager):
        """Initialize font manager.

        Args:
            root: Tkinter root window
            preferences_manager: PreferencesManager instance for persistence
        """
        self.root = root
        self.prefs = preferences_manager

        self.font_family = DEFAULT_FONT_FAMILY
        self.base_font_size = DEFAULT_FONT_SIZE
        self.current_font_size = DEFAULT_FONT_SIZE

        # User adjustment offset (-3 to +3 typically)
        self.user_adjustment = self.prefs.get("font_adjustment", 0)

        # Widgets that should have their fonts updated
        self.managed_widgets: List[tk.Widget] = []

        # Resize throttling
        self._resize_after_id: Optional[str] = None
        self._last_resize_width = 0
        self._resize_throttle_ms = RESIZE_THROTTLE_MS

        # Bind resize event
        self.root.bind("<Configure>", self._on_resize)

    def register_widget(self, widget: tk.Widget):
        """Register a widget to have its font managed.

        Args:
            widget: Widget to manage (typically tk.Text or ttk widgets)
        """
        if widget not in self.managed_widgets:
            self.managed_widgets.append(widget)
            self._apply_font_to_widget(widget)

    def unregister_widget(self, widget: tk.Widget):
        """Unregister a widget from font management.

        Args:
            widget: Widget to stop managing
        """
        if widget in self.managed_widgets:
            self.managed_widgets.remove(widget)

    def increase_font_size(self):
        """Increase font size by 1 point (user adjustment)."""
        self.user_adjustment = min(self.user_adjustment + 1, MAX_FONT_SIZE - self.base_font_size)
        self._update_fonts()
        self.prefs.set("font_adjustment", self.user_adjustment)
        logger.info(f"Font size increased: adjustment={self.user_adjustment}")

    def decrease_font_size(self):
        """Decrease font size by 1 point (user adjustment)."""
        self.user_adjustment = max(self.user_adjustment - 1, MIN_FONT_SIZE - self.base_font_size)
        self._update_fonts()
        self.prefs.set("font_adjustment", self.user_adjustment)
        logger.info(f"Font size decreased: adjustment={self.user_adjustment}")

    def reset_font_size(self):
        """Reset font size to automatic scaling (no user adjustment)."""
        self.user_adjustment = 0
        self._update_fonts()
        self.prefs.set("font_adjustment", 0)
        logger.info("Font size reset to automatic")

    def update_font_size(self, size: int):
        """Manually update the base font size (used for UI scaling).

        Args:
            size: New base font size
        """
        self.base_font_size = size
        self._update_fonts()
        logger.info(f"Font size updated to {size}")

    def set_base_size_from_window_width(self, width: int):
        """Calculate base font size from window width using breakpoints.

        Args:
            width: Window width in pixels
        """
        # Find appropriate font size from breakpoints
        for breakpoint_width, font_size in FONT_SIZE_BREAKPOINTS:
            if width <= breakpoint_width:
                self.base_font_size = font_size
                break
        else:
            # Larger than all breakpoints, use max
            self.base_font_size = FONT_SIZE_BREAKPOINTS[-1][1]

    def _calculate_font_size(self) -> int:
        """Calculate current font size including user adjustment.

        Returns:
            Font size (clamped to min/max)
        """
        size = self.base_font_size + self.user_adjustment
        return max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, size))

    def _update_fonts(self):
        """Update all managed widgets with current font size."""
        self.current_font_size = self._calculate_font_size()
        for widget in self.managed_widgets:
            self._apply_font_to_widget(widget)

    def _apply_font_to_widget(self, widget: tk.Widget):
        """Apply current font to a specific widget.

        Args:
            widget: Widget to update
        """
        try:
            font = (self.font_family, self.current_font_size)
            widget.config(font=font)
        except tk.TclError as e:
            logger.warning(f"Could not set font on widget {widget}: {e}")

    def _on_resize(self, event):
        """Handle window resize events (throttled).

        Args:
            event: Tkinter Configure event
        """
        # Only respond to width changes of the root window
        if event.widget != self.root:
            return

        if not hasattr(event, "width"):
            return

        # Only update if width changed significantly
        width_change = abs(event.width - self._last_resize_width)
        if width_change < RESIZE_SIGNIFICANT_CHANGE_PX:
            return

        # Cancel pending resize
        if self._resize_after_id:
            self.root.after_cancel(self._resize_after_id)

        # Schedule resize
        self._resize_after_id = self.root.after(
            self._resize_throttle_ms, lambda: self._handle_resize(event.width)
        )

    def _handle_resize(self, width: int):
        """Actually handle the resize after throttle delay.

        Args:
            width: New window width
        """
        self._last_resize_width = width
        self.set_base_size_from_window_width(width)
        self._update_fonts()
        logger.debug(
            f"Font resized: width={width}, base={self.base_font_size}, "
            f"adjustment={self.user_adjustment}, final={self.current_font_size}"
        )

    def get_current_font_size(self) -> int:
        """Get current font size.

        Returns:
            Current font size in points
        """
        return self.current_font_size

    def get_current_font(self) -> tuple:
        """Get current font tuple.

        Returns:
            (family, size) tuple
        """
        return (self.font_family, self.current_font_size)
