# -*- coding: utf-8 -*-
"""Tooltip widget for providing help text on hover."""

import tkinter as tk

from ui.constants import TOOLTIP_DELAY_MS


class ToolTip:
    """Create a tooltip for a given widget."""
    
    def __init__(self, widget, text, delay=None):
        """Initialize tooltip.
        
        Args:
            widget: Widget to attach tooltip to
            text: Tooltip text
            delay: Delay in ms before showing tooltip (defaults to TOOLTIP_DELAY_MS)
        """
        self.widget = widget
        self.text = text
        self.delay = delay if delay is not None else TOOLTIP_DELAY_MS
        self.tooltip_window = None
        self.id = None
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
        self.widget.bind("<ButtonPress>", self.on_leave)
    
    def on_enter(self, event=None):
        """Handle mouse enter event."""
        self.schedule()
    
    def on_leave(self, event=None):
        """Handle mouse leave event."""
        self.unschedule()
        self.hide_tooltip()
    
    def schedule(self):
        """Schedule tooltip to show after delay."""
        self.unschedule()
        self.id = self.widget.after(self.delay, self.show_tooltip)
    
    def unschedule(self):
        """Cancel scheduled tooltip."""
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
    
    def show_tooltip(self):
        """Display the tooltip."""
        if self.tooltip_window:
            return
        
        # Get widget position
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        # Create tooltip window
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        # Create label with text
        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            background="#ffffe0",
            foreground="#000000",
            relief="solid",
            borderwidth=1,
            font=("Segoe UI", 9),
            justify="left",
            padx=5,
            pady=3
        )
        label.pack()
    
    def hide_tooltip(self):
        """Hide the tooltip."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


def create_tooltip(widget, text, delay=None):
    """Create a tooltip for a widget.
    
    Args:
        widget: Widget to attach tooltip to
        text: Tooltip text
        delay: Delay in ms before showing (defaults to TOOLTIP_DELAY_MS)
        
    Returns:
        ToolTip instance
    """
    return ToolTip(widget, text, delay)
