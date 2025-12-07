# -*- coding: utf-8 -*-
"""Custom UI widgets for the application."""

from tkinter import ttk


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
        # Reflow on resize
        self.bind("<Configure>", self._on_configure)

    def _on_configure(self, event):
        from config import FLOW_FRAME_MIN_WIDTH_THRESHOLD
        # Throttle reflows - only update if width changed significantly
        if hasattr(event, 'width'):
            if abs(event.width - self._last_width) < FLOW_FRAME_MIN_WIDTH_THRESHOLD:
                return
            self._last_width = event.width
        
        # Cancel pending reflow
        if self._reflow_after_id:
            self.after_cancel(self._reflow_after_id)
        
        # Schedule new reflow with delay
        self._reflow_after_id = self.after_idle(self._reflow)

    def _reflow(self):
        from config import FLOW_FRAME_REFLOW_DELAY_MS
        # Place children into grid cells, wrapping when necessary
        if not self._children:
            return

        # Ensure sizes are updated
        self.update_idletasks()
        avail_width = self.winfo_width()
        if avail_width <= 1:
            # Not yet mapped; try again shortly (max 5 retries to prevent infinite loop)
            if not hasattr(self, '_reflow_retry_count'):
                self._reflow_retry_count = 0
            if self._reflow_retry_count < 5:
                self._reflow_retry_count += 1
                self.after(FLOW_FRAME_REFLOW_DELAY_MS, self._reflow)
            return
        self._reflow_retry_count = 0  # Reset counter on successful reflow

        x = 0
        row = 0
        col = 0
        for btn in self._children:
            w = btn.winfo_reqwidth() + self._padx
            # If the button doesn't fit on the current row, move to next row
            if col > 0 and (x + w) > avail_width:
                row += 1
                col = 0
                x = 0

            # Grid the button
            btn.grid_configure(row=row, column=col, padx=(self._padx//2), pady=(self._pady//2), sticky='w')
            # Advance counters
            x += w
            col += 1

        # Clear any extra columns/rows if present (no-op if none)
        for c in range(col, max(1, col + 1)):
            try:
                self.columnconfigure(c, weight=0)
            except Exception:
                pass

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
        # Limit button width to avoid very long labels forcing overflow; width
        # is in character units — keep reasonably wide but constrained.
        try:
            btn.config(width=20)
        except Exception:
            pass
        # Use grid placement managed by this frame's reflow logic
        btn.grid(row=0, column=len(self._children), padx=(self._padx//2), pady=(self._pady//2), sticky='w')
        self._children.append(btn)
        # Trigger reflow to wrap if needed
        self.after_idle(self._reflow)
        return btn

    def clear(self):
        """Clear all children and reset state."""
        for child in self._children:
            child.destroy()
        self._children.clear()
