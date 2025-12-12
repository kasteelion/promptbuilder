"""Notification helper: prefer toasts, then status bar, then modal dialog.

Provides a single `notify` function to centralize non-blocking notifications
across the UI. Use `level` in ('info', 'success', 'warning', 'error').
"""

import tkinter as tk
from tkinter import messagebox
from typing import Optional


def notify(root: Optional[tk.Misc], title: Optional[str], message: str, level: str = 'info', duration: int = 3000, parent: Optional[tk.Misc] = None):
    """Send a notification using preferred mechanism.

    Order:
    1. `root.toasts.notify(message, level, duration)` if available
    2. `root._update_status(message)` if available
    3. Fallback to modal messagebox (type depends on `level`)

    Args:
        root: The application root or a toplevel widget (used to access `toasts`/`_update_status`).
        title: Dialog title for modal fallback (can be None).
        message: Message text to display.
        level: One of 'info', 'success', 'warning', 'error'.
        duration: Milliseconds for toast duration (if supported).
        parent: Parent for modal messagebox if desired.
    """
    try:
        if root is not None and hasattr(root, 'toasts'):
            try:
                root.toasts.notify(message, level, duration)
                return
            except Exception:
                pass
        if root is not None and hasattr(root, '_update_status'):
            try:
                root._update_status(message)
                return
            except Exception:
                pass
    except Exception:
        # Defensive: if accessing root fails, fall through to modal
        pass

    # Fallback to modal depending on level
    if level == 'error':
        messagebox.showerror(title or 'Error', message, parent=parent)
    elif level == 'warning':
        messagebox.showwarning(title or 'Warning', message, parent=parent)
    else:
        messagebox.showinfo(title or 'Info', message, parent=parent)
