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
    """A reusable scrollable canvas with mousewheel support and auto scroll region updates.

    Handles common scrolling patterns:
    - Mousewheel binding to canvas and all child widgets
    - Automatic scroll region updates
    - Canvas window width syncing for proper wrapping
    """

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # Configure grid
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview, style="Vertical.TScrollbar"
        )
        self.container = ttk.Frame(self.canvas, style="TFrame")

        # Create canvas window and sync width
        self._window = self.canvas.create_window((0, 0), window=self.container, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Bind canvas width to window width for proper wrapping and filling
        def update_window_width(event):
            # Ensure the inner container fills the canvas width
            self.canvas.itemconfig(self._window, width=event.width)
            # Update scroll region when canvas resizes
            self.update_scroll_region()

        self.canvas.bind("<Configure>", update_window_width)

        # Grid layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        # Bind mousewheel
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self._bind_mousewheel_recursive(self.container)

    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling with smooth pixel-based movement."""
        # Calculate scroll amount
        # On Windows, delta is typically 120 or -120 per notch
        # We'll scroll by a fixed pixel amount for more consistent feel
        scroll_pixels = 40  # pixels per notch
        
        direction = -1 if event.delta > 0 else 1
        amount = direction * scroll_pixels
        
        # Get current scroll position and total height
        try:
            # yview returns (top, bottom) as fractions of total height
            # we need to convert pixels to fraction
            bbox = self.canvas.bbox("all")
            if not bbox:
                return "break"
            
            total_height = bbox[3] - bbox[1]
            if total_height <= 0:
                return "break"
                
            # Current top fraction
            current_top = self.canvas.yview()[0]
            
            # New top fraction
            new_top = current_top + (amount / total_height)
            
            # Clamp to [0, 1]
            new_top = max(0, min(1, new_top))
            
            # Apply scroll
            self.canvas.yview_moveto(new_top)
        except Exception:
            # Fallback to standard scroll if calculation fails
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            
        return "break"

    def _bind_mousewheel_recursive(self, widget):
        widget.bind("<MouseWheel>", self._on_mousewheel)
        for child in widget.winfo_children():
            self._bind_mousewheel_recursive(child)

    def update_scroll_region(self):
        # Defer the actual bbox calculation until the event loop is idle so that
        # geometry managers have a chance to settle. This avoids computing an
        # incomplete bbox when widgets are still being laid out which can cause
        # the scrollbar to not reach the bottom of the content.
        def _apply_scrollregion():
            try:
                self.canvas.update_idletasks()
                # Make the canvas window's height match the container's requested
                # height so bbox('all') reflects the full content. This helps
                # when children are positioned with place/grid and the window
                # item hasn't picked up the final height yet.
                try:
                    req_h = int(self.container.winfo_reqheight() or 0)
                    if req_h > 1:
                        try:
                            self.canvas.itemconfig(self._window, height=req_h)
                        except Exception:
                            pass
                except Exception:
                    pass
                # Compute desired scrollregion from container/requested height
                # and from measured child extents, since canvas.bbox('all') may
                # only include the canvas window item and not reflect inner
                # children's final placed extents.
                try:
                    # Container requested size is the best single source of truth
                    cont_req_h = int(self.container.winfo_reqheight() or 0)
                except Exception:
                    cont_req_h = 0

                # Compute the max bottom among container children (y + height)
                max_child_bottom = 0
                try:
                    for c in self.container.winfo_children():
                        try:
                            y = int(c.winfo_y())
                            h = int(c.winfo_height())
                            if y + h > max_child_bottom:
                                max_child_bottom = y + h
                        except Exception:
                            continue
                except Exception:
                    max_child_bottom = 0

                # Prefer the largest measurement we have
                bottom_padding = 32
                measured_bottom = max(cont_req_h, max_child_bottom)
                try:
                    canvas_h = int(self.canvas.winfo_height() or 0)
                except Exception:
                    canvas_h = 0

                desired_bottom = max(measured_bottom + bottom_padding, canvas_h)

                try:
                    cont_req_w = int(self.container.winfo_reqwidth() or 0)
                except Exception:
                    cont_req_w = 0

                # Set scrollregion explicitly using container extents so the
                # scrollbar covers all inner widgets.
                try:
                    self.canvas.config(scrollregion=(0, 0, cont_req_w or 1, desired_bottom))
                except Exception:
                    try:
                        # Fallback to using bbox if available
                        bbox = self.canvas.bbox("all")
                        if bbox:
                            self.canvas.config(scrollregion=bbox)
                    except Exception:
                        pass
            except Exception as e:
                logger.debug(f"Failed to update scroll region: {e}")

        try:
            # Schedule after_idle to ensure all widgets report correct sizes first
            self.canvas.after_idle(_apply_scrollregion)
        except Exception:
            # Best-effort immediate attempt if after_idle isn't available
            try:
                _apply_scrollregion()
            except Exception:
                pass

        # Retry loop: attempt several times with increasing delays to handle
        # widgets that perform layout asynchronously (FlowFrame reflows, image
        # loading, etc.). This makes the scrollregion robust against late
        # geometry changes.
        max_retries = 5
        delays = [60, 150, 300, 600, 1000]

        def _retry_attempt(attempt=0):
            try:
                bbox = self.canvas.bbox("all")
                if not bbox:
                    # Nothing yet — schedule next attempt
                    if attempt + 1 < max_retries:
                        self.canvas.after(
                            delays[min(attempt, len(delays) - 1)],
                            lambda: _retry_attempt(attempt + 1),
                        )
                    return

                # Compute maximum bottom extent from children (in container coords)
                max_child_h = 0
                for c in self.container.winfo_children():
                    try:
                        y = int(c.winfo_y() + c.winfo_height())
                        if y > max_child_h:
                            max_child_h = y
                    except Exception:
                        continue

                # If any child's bottom extends below bbox bottom, expand scrollregion
                if max_child_h and bbox[3] < max_child_h:
                    try:
                        new_bottom = max_child_h + 32
                        self.canvas.config(scrollregion=(bbox[0], bbox[1], bbox[2], new_bottom))
                    except Exception:
                        pass
                else:
                    # If bbox seems smaller than canvas height, ensure a small padding
                    try:
                        canvas_h = int(self.canvas.winfo_height() or 0)
                        if bbox[3] < canvas_h:
                            self.canvas.config(
                                scrollregion=(
                                    bbox[0],
                                    bbox[1],
                                    bbox[2],
                                    max(bbox[3] + 24, canvas_h),
                                )
                            )
                    except Exception:
                        pass

                # If we're not yet satisfied and we have retries left, schedule another attempt
                if attempt + 1 < max_retries:
                    # If the bbox hasn't grown significantly, we can stop early
                    next_delay = delays[min(attempt, len(delays) - 1)]
                    self.canvas.after(next_delay, lambda: _retry_attempt(attempt + 1))
            except Exception:
                # Swallow exceptions in retry attempts to avoid noisy failures
                if attempt + 1 < max_retries:
                    try:
                        self.canvas.after(
                            delays[min(attempt, len(delays) - 1)],
                            lambda: _retry_attempt(attempt + 1),
                        )
                    except Exception:
                        pass

        try:
            # Start retries
            self.canvas.after(delays[0], lambda: _retry_attempt(0))
        except Exception:
            pass

    def refresh_mousewheel_bindings(self):
        self._bind_mousewheel_recursive(self.container)

    def get_container(self):
        return self.container


class CollapsibleFrame(ttk.Frame):
    """A frame that can be collapsed/expanded with a toggle button."""

    def __init__(self, parent, text="", opened=True, show_clear=False, *args, **kwargs):
        super().__init__(parent, *args, **kwargs, style="Collapsible.TFrame")
        self.columnconfigure(0, weight=1)
        self._text = text

        # Header frame with toggle button and optional clear button
        self._header = ttk.Frame(self, style="Collapsible.TFrame")
        self._header.grid(row=0, column=0, sticky="ew")

        self._toggle_btn = ttk.Button(
            self._header, 
            text=("▾ " if opened else "▸ ") + text, 
            command=self._toggle_cb, 
            style="Accent.TButton"
        )
        self._toggle_btn.pack(side="left", anchor="w")

        self._clear_btn = None
        if show_clear:
            self._clear_btn = ttk.Button(self._header, text="Clear", style="TButton")
            self._clear_btn.pack(side="right")

        # Content frame
        self._content = ttk.Frame(self, style="Collapsible.TFrame")
        self._content.grid(row=1, column=0, sticky="nsew")
        
        self._open = opened
        if not self._open:
            self._content.grid_remove()

    def _toggle_cb(self):
        self._open = not self._open
        if self._open:
            self._content.grid()
            self._toggle_btn.config(text="▾ " + self._text)
        else:
            self._content.grid_remove()
            self._toggle_btn.config(text="▸ " + self._text)

    def set_clear_command(self, cmd):
        if self._clear_btn:
            self._clear_btn.config(command=cmd)

    def get_header_frame(self):
        """Return the header frame to allow adding custom widgets."""
        return self._header

    def get_content_frame(self):
        return self._content


class FlowFrame(ttk.Frame):
    """A simple flow/wrap frame that places children left-to-right and wraps naturally.

    Uses placement-based layout to avoid flicker when reflowing.
    """

    def __init__(self, parent, padding_x=6, padding_y=4, min_chip_width=64, *args, **kwargs):
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
