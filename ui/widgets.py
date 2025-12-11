# -*- coding: utf-8 -*-
"""Custom UI widgets for the application."""

import tkinter as tk
from tkinter import ttk


class ScrollableCanvas(ttk.Frame):
    """A reusable scrollable canvas with mousewheel support and auto scroll region updates.
    
    Handles common scrolling patterns:
    - Mousewheel binding to canvas and all child widgets
    - Automatic scroll region updates
    - Canvas window width syncing for proper wrapping
    """
    
    def __init__(self, parent, *args, **kwargs):
        """Initialize scrollable canvas.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent, *args, **kwargs)
        
        # Configure grid
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", 
                                       command=self.canvas.yview,
                                       style="Vertical.TScrollbar")
        self.container = ttk.Frame(self.canvas, style="TFrame")
        
        # Create canvas window and sync width
        self._window = self.canvas.create_window((0, 0), window=self.container, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Bind canvas width to window width for proper wrapping
        def update_window_width(event):
            self.canvas.itemconfig(self._window, width=event.width)
            # Update scroll region when canvas resizes
            self.canvas.after_idle(self.update_scroll_region)
        
        self.canvas.bind("<Configure>", update_window_width)
        
        # Grid layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Bind mousewheel
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self._bind_mousewheel_recursive(self.container)
    
    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"
    
    def _bind_mousewheel_recursive(self, widget):
        """Recursively bind mousewheel to widget and all its children."""
        widget.bind("<MouseWheel>", self._on_mousewheel)
        for child in widget.winfo_children():
            self._bind_mousewheel_recursive(child)
    
    def update_scroll_region(self):
        """Update the canvas scroll region to fit all content."""
        try:
            self.canvas.update_idletasks()
            bbox = self.canvas.bbox("all")
            if bbox:
                self.canvas.config(scrollregion=bbox)
        except Exception:
            pass
    
    def refresh_mousewheel_bindings(self):
        """Rebind mousewheel to all widgets (call after adding new content)."""
        self._bind_mousewheel_recursive(self.container)
    
    def get_container(self):
        """Get the container frame for adding content.
        
        Returns:
            ttk.Frame: Container frame
        """
        return self.container


class CollapsibleFrame(ttk.Frame):
    """A frame that can be collapsed/expanded with a toggle button."""
    
    def __init__(self, parent, text="", *args, **kwargs):
        """Initialize collapsible frame.
        
        Args:
            parent: Parent widget
            text: Header text for the frame
        """
        super().__init__(parent, *args, **kwargs, style="Collapsible.TFrame")
        self.columnconfigure(0, weight=1)
        
        # Header frame with toggle button and clear button
        self._header = ttk.Frame(self, style="Collapsible.TFrame")
        self._header.grid(row=0, column=0, sticky="ew")
        
        self._toggle = ttk.Button(
            self._header, 
            text="▾ " + text, 
            command=self._toggle_cb, 
            style="Accent.TButton"
        )
        self._toggle.pack(side="left", anchor="w")
        
        self._clear_btn = ttk.Button(
            self._header, 
            text="Clear", 
            style="TButton"
        )
        self._clear_btn.pack(side="right")
        
        # Content frame
        self._content = ttk.Frame(self, style="Collapsible.TFrame")
        self._content.grid(row=1, column=0, sticky="nsew")
        self._open = True

    def _toggle_cb(self):
        """Toggle frame collapsed/expanded state."""
        self._open = not self._open
        if self._open:
            self._content.grid()
            self._toggle.config(text="▾ " + self._toggle.cget("text")[2:])
        else:
            self._content.grid_remove()
            self._toggle.config(text="▸ " + self._toggle.cget("text")[2:])

    def set_clear_command(self, cmd):
        """Set the command for the clear button.
        
        Args:
            cmd: Callback function
        """
        self._clear_btn.config(command=cmd)

    def get_content_frame(self):
        """Get the content frame for adding widgets.
        
        Returns:
            ttk.Frame: Content frame
        """
        return self._content


class FlowFrame(ttk.Frame):
    """A simple flow/wrap frame that places children left-to-right and wraps naturally.
    
    This implementation measures child widgets and places them into a
    grid so they wrap to new lines when the available width is exceeded.
    It automatically reflows on resize.
    """

    def __init__(self, parent, padding_x=6, padding_y=4, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self._padx = padding_x
        self._pady = padding_y
        self._children = []
        self._reflow_after_id = None
        self._last_width = 0
        self._reflow_retry_count = 0
        self._max_retries = 10  # Prevent infinite recursion
        # Bind Configure to reflow when width changes
        self.bind("<Configure>", self._on_configure)
    
    def _on_configure(self, event):
        """Handle width changes to trigger reflow."""
        if hasattr(event, 'width') and event.width > 1:
            # Only reflow if width actually changed significantly
            if abs(event.width - self._last_width) > 10:
                self._last_width = event.width
                # Cancel any pending reflow
                if self._reflow_after_id:
                    self.after_cancel(self._reflow_after_id)
                # Schedule reflow
                self._reflow_after_id = self.after(50, self._reflow)

    def _reflow(self):
        from .constants import FLOW_FRAME_REFLOW_DELAY_MS, WIDGET_REFLOW_RETRY_LIMIT
        
        # Place children into grid cells, wrapping when necessary
        if not self._children:
            return

        # Just use current width
        avail_width = self.winfo_width()
        if avail_width <= 1:
            # Not yet mapped; try again shortly (max retries to prevent infinite loop)
            if not hasattr(self, '_reflow_retry_count'):
                self._reflow_retry_count = 0
            if self._reflow_retry_count < WIDGET_REFLOW_RETRY_LIMIT:
                self._reflow_retry_count += 1
                self.after(FLOW_FRAME_REFLOW_DELAY_MS, self._reflow)
            return
        self._reflow_retry_count = 0  # Reset counter on successful reflow

        x = 0
        row = 0
        col = 0
        max_cols = 3  # Limit to 3 columns for better readability
        
        for btn in self._children:
            # Grid the button with better spacing
            btn.grid_configure(row=row, column=col, padx=self._padx, pady=self._pady, sticky='ew')
            
            col += 1
            # Wrap to next row after max_cols
            if col >= max_cols:
                row += 1
                col = 0

        # Configure column weights for uniform stretching
        for c in range(max_cols):
            self.columnconfigure(c, weight=1, uniform='outfit_col')
        
        # Configure row weights
        for r in range(row + 1):
            self.rowconfigure(r, weight=0)

    def add_button(self, text, style=None, command=None):
        """Add a button to the flow frame.
        
        Args:
            text: Button label
            style: ttk button style (e.g., 'Accent.TButton')
            command: Button callback
            
        Returns:
            ttk.Button: The created button
        """
        btn = ttk.Button(self, text=text, style=style or 'TButton', command=command)
        # Use grid placement managed by this frame's reflow logic
        btn.grid(row=0, column=len(self._children), padx=self._padx, pady=self._pady, sticky='ew')
        self._children.append(btn)
        # Trigger reflow to wrap if needed - use after() with delay to allow width to be set
        self.after(10, self._reflow)
        return btn

    def clear(self):
        """Clear all children and reset state."""
        for child in self._children:
            child.destroy()
        self._children.clear()
