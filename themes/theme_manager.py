"""Theme management for the application."""

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk
from config import THEMES, DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE


class ThemeManager:
    """Manages application themes and applies them to widgets."""
    
    def __init__(self, root, style):
        """Initialize theme manager.
        
        Args:
            root: Tkinter root window
            style: ttk.Style instance
        """
        self.root = root
        self.style = style
        self.current_theme = None
        self.themes = THEMES
        self.default_font_family = DEFAULT_FONT_FAMILY
        self.default_font_size = DEFAULT_FONT_SIZE
        
        # Set base theme
        try:
            self.style.theme_use("clam")
        except:
            pass
    
    def apply_theme(self, theme_name):
        """Apply a theme to all ttk styles and return theme colors.
        
        Args:
            theme_name: Name of theme from THEMES dict
            
        Returns:
            dict: Theme color dictionary
        """
        if theme_name not in self.themes:
            theme_name = "Dark"
        
        self.current_theme = theme_name
        theme = self.themes[theme_name]
        
        # Update all ttk styles
        self._update_ttk_styles(theme)
        
        # Apply background to root window
        self.root.config(bg=theme["bg"])
        
        return theme
    
    def _update_ttk_styles(self, theme):
        """Update all ttk widget styles with theme colors."""
        bg = theme["bg"]
        fg = theme["fg"]
        text_bg = theme["text_bg"]
        accent = theme["accent"]
        accent_hover = theme.get("accent_hover", accent)
        border = theme["border"]
        selected_bg = theme.get("selected_bg", text_bg)

        # General Layout Elements
        self.style.configure("TFrame", background=bg)
        self.style.configure("TLabel", background=bg, foreground=fg)
        self.style.configure("TCheckbutton", background=bg, foreground=fg)
        
        # Custom widget styles
        self.style.configure("Collapsible.TFrame", background=bg)
        self.style.configure("Title.TLabel", font=(None, 14, "bold"), 
                           background=bg, foreground=accent)
        
        # Notebook tabs with better selection contrast
        self.style.configure("TNotebook", background=bg, bordercolor=border, borderwidth=1)
        self.style.configure("TNotebook.Tab", background=bg, foreground=fg, 
                           bordercolor=border, padding=[10, 2])
        self.style.map("TNotebook.Tab", 
                      background=[("selected", selected_bg), ("active", text_bg)],
                      foreground=[("selected", accent), ("active", fg)])
        
        # Combobox/Entry with better contrast
        self.style.configure("TCombobox", fieldbackground=text_bg, 
                           foreground=fg, background=bg, 
                           selectbackground=accent, selectforeground=text_bg,
                           bordercolor=border, borderwidth=1)
        self.style.map("TCombobox", 
                      fieldbackground=[("readonly", text_bg)], 
                      selectbackground=[("readonly", text_bg)])

        # Buttons with improved hover states
        self.style.configure("TButton", background=text_bg, 
                           foreground=fg, bordercolor=border, borderwidth=1,
                           padding=[6, 3])
        self.style.map("TButton", 
                      background=[("active", accent), ("pressed", accent_hover)], 
                      foreground=[("active", text_bg), ("pressed", text_bg)],
                      bordercolor=[("active", accent), ("pressed", accent_hover)])

        # Accent Button for primary actions
        self.style.configure("Accent.TButton", background=accent, 
                           foreground=text_bg, bordercolor=accent, borderwidth=1,
                           padding=[6, 3])
        self.style.map("Accent.TButton", 
                      background=[("active", accent_hover), ("pressed", border)], 
                      foreground=[("active", text_bg), ("pressed", fg)],
                      bordercolor=[("active", accent_hover), ("pressed", border)])
                       
        # Label Frames with more visible borders
        self.style.configure("TLabelframe", background=bg, 
                           foreground=fg, bordercolor=border, borderwidth=2,
                           relief="solid")
        self.style.configure("TLabelframe.Label", background=bg, foreground=accent,
                           font=(None, 9, "bold"))

        # Scrollbar with better visibility
        self.style.configure("Vertical.TScrollbar", background=text_bg, 
                           troughcolor=bg, bordercolor=border, arrowcolor=fg)
    
    def apply_text_widget_theme(self, widget, theme):
        """Apply theme colors to a tk.Text widget.
        
        Args:
            widget: tk.Text widget to style
            theme: Theme color dictionary
        """
        widget.config(
            bg=theme["text_bg"],
            fg=theme["text_fg"],
            insertbackground=theme["text_fg"],
            selectbackground=theme["accent"],
            selectforeground=theme["text_fg"]
        )
    
    def apply_preview_theme(self, widget, theme):
        """Apply theme colors to preview widget with formatted tags.
        
        Args:
            widget: scrolledtext.ScrolledText widget
            theme: Theme color dictionary
        """
        # Base widget colors
        widget.config(
            bg=theme["preview_bg"],
            fg=theme["preview_fg"],
            insertbackground=theme["preview_fg"],
            selectbackground=theme["accent"],
            selectforeground=theme["preview_fg"]
        )
        
        # Get current font size safely
        font_family = self.default_font_family
        try:
            font_size = tkfont.Font(font=widget.cget('font')).cget('size')
        except:
            font_size = self.default_font_size
        
        # Configure text tags
        widget.tag_config("bold", font=(font_family, font_size, "bold"))
        widget.tag_config("title", 
            font=(font_family, font_size + 2 if font_size > 0 else 14, "bold"),
            foreground=theme.get("accent", "#66d9ef")
        )
        widget.tag_config("separator", foreground=theme.get("border", "#49483e"))
        widget.tag_config("error", 
            foreground="red",
            background=theme["text_bg"],
            font=(font_family, font_size, "bold")
        )
        # Section labels (smaller than title, bold). Use accent if available, fall back to preview_fg
        widget.tag_config("section_label",
            font=(font_family, font_size, "bold"),
            foreground=theme.get("accent", theme.get("preview_fg", theme.get("fg")))
        )
    
    def apply_canvas_theme(self, canvas, theme):
        """Apply theme background to a tk.Canvas widget.
        
        Args:
            canvas: tk.Canvas widget
            theme: Theme color dictionary
        """
        # Use text_bg for better contrast with content
        canvas.config(bg=theme.get("text_bg", theme["bg"]))
