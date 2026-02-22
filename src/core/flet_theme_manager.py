import flet as ft
import os
from utils.theme_loader import load_themes_from_markdown

class ThemeManager:
    """Adapts legacy theme configurations for Flet and provides semantic styling."""
    
    _themes = None
    
    # Semantic Palette (Elite Standard)
    colors = {
        "surface": "#1e1e1e",
        "panel_bg": "#252526",
        "outline": "#3e3e42",
        "active_item": "#37373d",
        "accent": "#0078d7",
        "text_primary": "#ffffff",
        "text_secondary": "#cccccc",
        "success": "#4caf50",
        "warning": "#ff9800",
        "error": "#f44336",
    }
    
    styles = {
        "padding": 10,
        "radius": 8,
        "spacing": 10,
    }

    @classmethod
    def get_themes(cls):
        if cls._themes is None:
            # Current file: src/core/flet_theme_manager.py
            # Resolve project root: .../src/core -> .../src -> .../promptbuilder
            current_dir = os.path.dirname(os.path.abspath(__file__))
            src_dir = os.path.dirname(current_dir)
            root_dir = os.path.dirname(src_dir)
            
            themes_path = os.path.join(root_dir, "assets", "data", "lists", "themes.md")
            if not os.path.exists(themes_path):
                 print(f"DEBUG: Themes file not found at {themes_path}")
            cls._themes = load_themes_from_markdown(themes_path)
        return cls._themes

    @classmethod
    def get_available_themes(cls):
        return sorted(list(cls.get_themes().keys()))

    @classmethod
    def apply_theme(cls, page: ft.Page, theme_name: str = "Dark"):
        """Apply a theme from loaded themes to the Flet page and update semantic palette."""
        themes = cls.get_themes()
        
        if theme_name not in themes:
            theme_name = "Dark"
            if theme_name not in themes:
                 theme_name = next(iter(themes)) if themes else None

        if not theme_name: return

        theme_data = themes[theme_name]
        
        # 1. Update Semantic Palette
        cls.colors["surface"] = theme_data.get("bg", "#1e1e1e")
        cls.colors["panel_bg"] = theme_data.get("panel_bg", "#252526")
        cls.colors["text_primary"] = theme_data.get("fg", "#ffffff")
        cls.colors["accent"] = theme_data.get("accent", "#0078d7")
        
        # Extended Elite Mappings
        cls.colors["outline"] = theme_data.get("border", "#3e3e42")
        cls.colors["active_item"] = theme_data.get("selected_bg", "#37373d")
        cls.colors["input_bg"] = theme_data.get("text_bg", cls.colors["panel_bg"])
        cls.colors["accent_hover"] = theme_data.get("accent_hover", cls.colors["accent"])
        
        # Infer consistent variations
        
        # 2. Page Theme Mode
        bg_color = cls.colors["surface"].lower()
        is_light = "light" in theme_name.lower() or "white" in bg_color or "f0" in bg_color
        page.theme_mode = ft.ThemeMode.LIGHT if is_light else ft.ThemeMode.DARK
            
        # 3. Create Flet Theme
        if theme_name == "High Contrast":
            color_scheme = ft.ColorScheme(
                primary=cls.colors["accent"],
                on_primary=cls.colors["surface"],
                surface=cls.colors["panel_bg"],
                background=cls.colors["surface"],
                on_background=cls.colors["text_primary"],
            )
            page.theme = ft.Theme(color_scheme=color_scheme)
        else:
            page.theme = ft.Theme(
                color_scheme_seed=cls.colors["accent"],
                visual_density=ft.VisualDensity.COMFORTABLE
            )
            
        # 4. Direct overrides
        page.bgcolor = cls.colors["surface"]
        
        page.update()
