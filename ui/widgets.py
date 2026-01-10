# -*- coding: utf-8 -*-
"""Custom UI widgets for the application.

Provides:
- `ScrollableCanvas`: a frame containing a canvas + vertical scrollbar with an inner container.
- `CollapsibleFrame`: a header + content frame that can be toggled.
- `FlowFrame`: a placement-based flow/wrap container used for tag chips.
"""

import tkinter as tk
from tkinter import ttk

from utils import logger


class ScrollableCanvas(ttk.Frame):
    """A reusable scrollable canvas with mousewheel support and auto scroll region updates."""

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # Configure grid
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Create canvas and scrollbar
        # Default to dark bg to prevent white flash
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0, bg="#1e1e1e")
        self.scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview, style="Themed.Vertical.TScrollbar"
        )
        self.container = ttk.Frame(self.canvas, style="TFrame")
        
        self._scroll_after_id = None # Debounce tracking for scroll region updates
        self._resize_after_id = None # Debounce tracking for canvas width updates

        # Create canvas window and sync width
        self._window = self.canvas.create_window((0, 0), window=self.container, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Auto-update scroll region when inner content changes size
        self.container.bind("<Configure>", lambda e: self.update_scroll_region())

        # Bind canvas width to window width for proper wrapping and filling
        def update_window_width(event):
            if self._resize_after_id:
                self.after_cancel(self._resize_after_id)
            
            def _do_resize():
                try:
                    if self.canvas.winfo_exists():
                        # Ensure the inner container fills the canvas width
                        self.canvas.itemconfig(self._window, width=event.width)
                        # Update scroll region when canvas resizes
                        self.update_scroll_region()
                except Exception:
                    pass
                self._resize_after_id = None

            # Small 20ms debounce to prevent layout thrashing during movement
            self._resize_after_id = self.after(20, _do_resize)

        self.canvas.bind("<Configure>", update_window_width)

        # Grid layout - Refactor 3: Stop Layout Thrashing (Reserved Space)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Reserve fixed space for scrollbar so content doesn't jump
        self.columnconfigure(1, minsize=16) 
        
        self._hide_scrollbar_timer = None

        def _cancel_hide_timer():
            if self._hide_scrollbar_timer:
                self.after_cancel(self._hide_scrollbar_timer)
                self._hide_scrollbar_timer = None

        def show_scrollbar(event=None):
            _cancel_hide_timer()
            if self._is_scrolling_needed():
                self.scrollbar.grid(row=0, column=1, sticky="ns")
            
        def schedule_hide_scrollbar(event=None):
            _cancel_hide_timer()
            # Delay hiding to allow moving between canvas and scrollbar
            self._hide_scrollbar_timer = self.after(400, lambda: self.scrollbar.grid_remove())

        # Bind to both to handle transitions smoothly
        self.canvas.bind("<Enter>", show_scrollbar)
        self.canvas.bind("<Leave>", schedule_hide_scrollbar)
        
        self.scrollbar.bind("<Enter>", show_scrollbar)
        self.scrollbar.bind("<Leave>", schedule_hide_scrollbar)
        
        # Initially hidden
        self.scrollbar.grid_remove()

        # Bind mousewheel
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self._bind_mousewheel_recursive(self.container)

    def apply_theme(self, theme):
        """Update canvas background with theme colors. (Refactor 3)"""
        bg = theme.get("bg", "#121212")
        self.canvas.config(bg=bg)

    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling with smooth pixel-based movement."""
        # Ensure scrollbar is enabled for scrolling - Refactor 3 Fix
        if not self._is_scrolling_needed():
            return "break"
            
        scroll_pixels = 40  # pixels per notch
        direction = -1 if event.delta > 0 else 1
        amount = direction * scroll_pixels
        
        try:
            bbox = self.canvas.bbox("all")
            if not bbox:
                return "break"
            
            total_height = bbox[3] - bbox[1]
            if total_height <= 0:
                return "break"
                
            current_top = self.canvas.yview()[0]
            new_top = current_top + (amount / total_height)
            new_top = max(0, min(1, new_top))
            self.canvas.yview_moveto(new_top)
        except Exception:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            
        return "break"

    def _bind_mousewheel_recursive(self, widget):
        widget.bind("<MouseWheel>", self._on_mousewheel)
        for child in widget.winfo_children():
            self._bind_mousewheel_recursive(child)

    def update_scroll_region(self):
        """Update the scroll region with debouncing to handle async layouts efficiently."""
        if self._scroll_after_id:
            self.after_cancel(self._scroll_after_id)
            
        def _apply():
            try:
                if not self.winfo_exists():
                    return
                    
                # Always force an idle update to ensure geometries are calculated
                self.container.update_idletasks()
                
                # Get the bounding box of all items in the canvas
                bbox = self.canvas.bbox("all")
                
                if bbox:
                    # Calculate height from bbox
                    # Add padding to ensuring the last item isn't cut off
                    content_width = max(self.container.winfo_reqwidth(), bbox[2])
                    content_height = bbox[3] + 50 
                    
                    self.canvas.config(scrollregion=(0, 0, content_width, content_height))
                else:
                    # Fallback to reqheight if bbox empty (shouldn't happen if window is created)
                    self.canvas.config(scrollregion=(0, 0, self.container.winfo_reqwidth(), self.container.winfo_reqheight() + 50))
                
                # Check visibility
                if self._is_scrolling_needed():
                     # Let hover logic handle showing it, but we can update state if needed
                     pass
                else:
                    self.scrollbar.grid_remove()
                
                self._scroll_after_id = None
            except Exception:
                self._scroll_after_id = None

        # Coalesce multiple layout calls into one update
        self._scroll_after_id = self.after(50, _apply)

    def _is_scrolling_needed(self):
        """Check if the content height exceeds the viewable height. (Refactor 3)"""
        try:
            self.canvas.update_idletasks()
            view_height = self.canvas.winfo_height()
            if view_height <= 1: # Not mapped yet
                return False
                
            region = self.canvas.cget("scrollregion").split()
            if region and len(region) >= 4:
                content_height = float(region[3])
                return content_height > view_height
        except Exception: 
            pass
        return False

        # Schedule update with a small delay to coalesce multiple calls
        self._scroll_after_id = self.after(50, _apply)

    def refresh_mousewheel_bindings(self):
        self._bind_mousewheel_recursive(self.container)

    def get_container(self):
        return self.container


class CollapsibleFrame(ttk.Frame):
    """A frame that can be collapsed/expanded with a toggle button."""

    def __init__(self, parent, text="", opened=True, show_clear=False, show_import=False, *args, **kwargs):
        super().__init__(parent, *args, **kwargs, style="Card.TFrame")
        self.columnconfigure(0, weight=1)
        self._text = text.upper() # Refactor 5: UPPERCASE
        self.pill_buttons = [] # Track for theme updates

        # Header frame with distinct styling - Refactor 1 & 3
        self._header = ttk.Frame(self, style="TFrame", padding=(15, 5))
        self._header.grid(row=0, column=0, sticky="ew")
        
        # Explicitly set background for the header frame if needed - Refactor 3
        # Use semantic theme lookups
        theme = {}
        try:
            tm = parent.winfo_toplevel().theme_manager
            theme = tm.themes.get(tm.current_theme, {})
            panel_bg = theme.get("panel_bg", theme.get("bg", "#1e1e1e"))
            accent = theme.get("accent", "#0078d7")
        except Exception:
            panel_bg = "#1e1e1e"
            accent = "#0078d7"

        self._header.columnconfigure(0, weight=1)

        self._toggle_btn = tk.Button(
            self._header, 
            text=("▼ " if opened else "▶ ") + self._text, 
            command=self._toggle_cb, 
            bg=panel_bg,
            fg=accent,
            font=("Lexend", 10, "bold"),
            relief="flat",
            anchor="w",
            padx=5,
            cursor="hand2",
            activebackground=panel_bg,
            activeforeground=accent
        )
        self._toggle_btn.grid(row=0, column=0, sticky="ew")
        self._toggle_btn._base_bg = panel_bg
        
        # Container for header actions (to prevent cut-off)
        self._actions = ttk.Frame(self._header, style="TFrame")
        self._actions.grid(row=0, column=1, sticky="e")

        # Helper for Pill buttons in widgets
        def add_pill(text, command, col):
            # Outer Frame (The Border)
            pill = tk.Frame(self._actions, bg=accent, padx=1, pady=1)
            pill.grid(row=0, column=col, padx=2)
            
            # Inner Label (The hollow center)
            lbl = tk.Label(
                pill, 
                text=text.upper(), 
                bg=panel_bg, 
                fg=accent,
                font=("Lexend", 8, "bold"),
                padx=10,
                pady=2,
                cursor="hand2"
            )
            lbl.pack()
            lbl._base_bg = panel_bg
            
            def on_enter(e, l=lbl):
                try:
                    tm = self.master.winfo_toplevel().theme_manager
                    theme = tm.themes.get(tm.current_theme, {})
                    hbg = theme.get("hover_bg", "#333333")
                except Exception:
                    hbg = "#333333"
                l.config(bg=hbg)
            def on_leave(e, l=lbl):
                l.config(bg=getattr(l, "_base_bg", "#1e1e1e"))
                
            lbl.bind("<Enter>", on_enter)
            lbl.bind("<Leave>", on_leave)
            lbl.bind("<Button-1>", lambda e: command() if command else None)
            
            self.pill_buttons.append((pill, lbl))
            return pill, lbl

        self._clear_btn_parts = None
        if show_clear:
            self._clear_btn_parts = add_pill("✕ CLEAR", None, 0)

        self._import_btn_parts = None
        if show_import:
            col = 1 if show_clear else 0
            self._import_btn_parts = add_pill("📥 IMPORT", None, col)

        # Content frame - Refactor 1
        self._content = ttk.Frame(self, style="TFrame", padding=(15, 10))
        self._content.grid(row=1, column=0, sticky="nsew")
        
        self._open = opened
        if not self._open:
            self._content.grid_remove()

    def _toggle_cb(self):
        self._open = not self._open
        self._update_state()
        
    def _update_state(self):
        if self._open:
            self._content.grid()
            self._toggle_btn.config(text="▼ " + self._text)
        else:
            self._content.grid_remove()
            self._toggle_btn.config(text="▶ " + self._text)
        
        # Trigger parent scroll region update if applicable
        try:
            # Look for a ScrollableCanvas in parents
            p = self.master
            while p:
                if isinstance(p, ScrollableCanvas):
                    p.update_scroll_region()
                    break
                p = p.master
        except Exception:
            pass

    def apply_theme(self, theme):
        """Update custom widgets with theme colors. (Refactor 3)"""
        accent = theme.get("accent", theme.get("fg", "#0078d7"))
        panel_bg = theme.get("panel_bg", theme.get("bg", "#1e1e1e"))
        
        self._toggle_btn.config(bg=panel_bg, fg=accent, activebackground=panel_bg, activeforeground=accent)
        self._toggle_btn._base_bg = panel_bg
        
        for frame, lbl in self.pill_buttons:
            frame.config(bg=accent)
            lbl._base_bg = panel_bg
            lbl.config(bg=panel_bg, fg=accent)

    def set_opened(self, opened):
        """Programmatically set the opened/collapsed state."""
        if self._open != opened:
            self._open = opened
            self._update_state()

    def set_clear_command(self, cmd):
        if self._clear_btn_parts:
            # Rebind label click
            self._clear_btn_parts[1].bind("<Button-1>", lambda e: cmd())

    def set_import_command(self, cmd):
        if self._import_btn_parts:
            # Rebind label click
            self._import_btn_parts[1].bind("<Button-1>", lambda e: cmd())

    def get_header_frame(self):
        """Return the header frame to allow adding custom widgets."""
        return self._header

    def get_content_frame(self):
        return self._content


class FlowFrame(ttk.Frame):
    """A simple flow/wrap frame that places children left-to-right and wraps naturally.

    Uses placement-based layout to avoid flicker when reflowing.
    """

    def __init__(self, parent, padding_x=10, padding_y=8, min_chip_width=0, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self._padx = padding_x
        self._pady = padding_y
        self._children = []
        self._reflow_after_id = None
        self._pending_reflow = False
        self._min_chip_width = min_chip_width
        self._last_width = 0
        self._reflow_retry_count = 0
        # Bind Configure to reflow when width changes
        self.bind("<Configure>", self._on_configure)

    def _on_configure(self, event):
        if hasattr(event, "width") and event.width > 1:
            if abs(event.width - self._last_width) > 10:
                self._last_width = event.width
                if self._reflow_after_id:
                    try:
                        self.after_cancel(self._reflow_after_id)
                    except Exception:
                        pass
                logger.debug(
                    f"FlowFrame._on_configure: width changed -> scheduling reflow (w={event.width})"
                )
                self._reflow_after_id = self.after(50, self._reflow)

    def _reflow(self):
        from .constants import FLOW_FRAME_REFLOW_DELAY_MS, WIDGET_REFLOW_RETRY_LIMIT

        try:
            # PERFORMANCE: Skip reflow if not visible or mapped
            if not self.winfo_exists() or not self.winfo_viewable():
                # If not viewable, we might want to schedule one for when it becomes visible
                # But for now, just skip to save CPU
                return
                
            self.update_idletasks()
        except Exception:
            pass

        if not self._children:
            return

        avail_width = self.winfo_width()
        if avail_width <= 1:
            try:
                parent_w = getattr(self.master, "winfo_width", lambda: 0)()
                if parent_w and parent_w > 1:
                    avail_width = parent_w - 8
            except Exception:
                parent_w = 0

        if avail_width <= 1:
            if not hasattr(self, "_reflow_retry_count"):
                self._reflow_retry_count = 0
            if self._reflow_retry_count < WIDGET_REFLOW_RETRY_LIMIT:
                self._reflow_retry_count += 1
                self.after(FLOW_FRAME_REFLOW_DELAY_MS, self._reflow)
            return

        self._reflow_retry_count = 0
        logger.debug(
            f"FlowFrame._reflow(place): avail_width={avail_width} children={len(self._children)}"
        )

        x = self._padx
        y = self._pady
        line_height = 0

        for btn in self._children:
            try:
                w_req = btn.winfo_reqwidth()
                h_req = btn.winfo_reqheight()
            except Exception:
                w_req = 100
                h_req = 24

            # enforce a minimum width for visual consistency
            chip_w = max(w_req, self._min_chip_width)
            total_w = chip_w + (2 * self._padx)
            if x + total_w > avail_width and x > self._padx:
                x = self._padx
                y += line_height + self._pady
                line_height = 0

            try:
                btn.place(in_=self, x=x, y=y, width=chip_w, height=h_req)
            except Exception:
                try:
                    btn.place(x=x, y=y)
                except Exception:
                    pass

            x += total_w
            if h_req > line_height:
                line_height = h_req

        try:
            total_height = y + line_height + self._pady
            self.config(height=total_height)
        except Exception:
            pass

    def add_button(self, text, style=None, command=None):
        btn = ttk.Button(self, text=text, style=style or "TButton", command=command)
        self._children.append(btn)
        logger.debug(f"FlowFrame.add_button: added '{text}' children={len(self._children)}")
        # Coalesce reflows so adding many buttons is fast
        self._schedule_reflow()
        return btn

    def _schedule_reflow(self, delay=16):
        if self._pending_reflow:
            return
        self._pending_reflow = True

        def _do_reflow():
            try:
                self._reflow()
            finally:
                self._pending_reflow = False

        try:
            self.after(delay, _do_reflow)
        except Exception:
            try:
                self.after_idle(_do_reflow)
            except Exception:
                _do_reflow()

    def clear(self):
        for child in list(self._children):
            try:
                child.place_forget()
                child.destroy()
            except Exception:
                pass
        self._children.clear()
