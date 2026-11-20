import flet as ft
import os
from utils.theme_loader import load_themes_from_markdown

class ThemeManager:
    """Adapts legacy theme configurations for Flet and provides semantic styling."""
    
    _themes = None
    
    # Semantic Palette (Premium HSL-based)
    colors = {
        "surface": "#121212",       # Deeper Dark
        "panel_bg": "#1e1e1e",      # Subtle elevation
        "outline": "#2c2c2e",       # Crisp borders
        "active_item": "#2a2a2d",    # Selection highlight
        "accent": "#3ea6ff",        # Modern blue
        "accent_hover": "#65b8ff",
        "text_primary": "#f8f8f2",   # Off-white for less eye strain
        "text_secondary": "#a9a9b3", # Muted grey
        "success": "#4cd964",
        "warning": "#ffcc00",
        "error": "#ff3b30",
        "surface_variant": "#1a1a1c",
        "header_bg": "#121212",      # Default header bg
        "header_fg": "#f8f8f2",      # Default header fg
        "input_border": "#2c2c2e",   # Default input border
    }
    
    styles = {
        "padding": 12,
        "radius": 12,
        "spacing": 12,
        "elevation": 4, # Target elevation for containers
        "shadow_sm": ft.BoxShadow(spread_radius=0, blur_radius=4, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK), offset=ft.Offset(0, 2)),
        "shadow_md": ft.BoxShadow(spread_radius=1, blur_radius=8, color=ft.Colors.with_opacity(0.25, ft.Colors.BLACK), offset=ft.Offset(0, 4)),
        "shadow_lg": ft.BoxShadow(spread_radius=2, blur_radius=15, color=ft.Colors.with_opacity(0.4, ft.Colors.BLACK), offset=ft.Offset(0, 8)),
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
                 from utils import logger
                 logger.warning(f"Themes file not found at {themes_path}")
            cls._themes = load_themes_from_markdown(themes_path)
        return cls._themes

    @classmethod
    def get_available_themes(cls):
        return sorted(list(cls.get_themes().keys()))

    @classmethod
    def get_theme_accent(cls, theme_name: str) -> str:
        """Get the accent color for a specific theme name."""
        themes = cls.get_themes()
        if theme_name in themes:
            return themes[theme_name].get("accent", "#3ea6ff")
        return "#3ea6ff"

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
        cls.colors["input_border"] = theme_data.get("border", cls.colors["outline"])
        
        # Header Styling
        cls.colors["header_bg"] = theme_data.get("header_bg", cls.colors["surface"])
        cls.colors["header_fg"] = theme_data.get("header_fg", cls.colors["text_primary"])
        
        # 2. Auto-Tone Deduction
        def adjust_color(hex_color, amount):
            """Simple light/dark shift for hex colors."""
            hex_color = hex_color.lstrip('#')
            if len(hex_color) == 3:
                hex_color = ''.join([c*2 for c in hex_color])
            
            try:
                rgb = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
                # Move towards white or black
                new_rgb = [max(0, min(255, c + amount)) for c in rgb]
                return f"#{new_rgb[0]:02x}{new_rgb[1]:02x}{new_rgb[2]:02x}"
            except Exception:
                return f"#{hex_color}"

        # Deduce Hover
        if "accent_hover" in theme_data:
            cls.colors["accent_hover"] = theme_data["accent_hover"]
        else:
            # Shift accent slightly brighter if it's a dark theme, or darker if it's light
            cls.colors["accent_hover"] = adjust_color(cls.colors["accent"], 20)

        # Deduce Surface Variant (slightly lighter than surface for dark, darker for light)
        if "surface_variant" in theme_data:
            cls.colors["surface_variant"] = theme_data["surface_variant"]
        else:
            cls.colors["surface_variant"] = adjust_color(cls.colors["surface"], 10)
        
        # Infer consistent variations
        
        # 2. Page Theme Mode
        bg_color = cls.colors["surface"].lower()
        is_light = "light" in theme_name.lower() or "white" in bg_color or "f8" in bg_color or "fa" in bg_color
        page.theme_mode = ft.ThemeMode.LIGHT if is_light else ft.ThemeMode.DARK
            
        # 3. Create Flet Theme
        if theme_name == "High Contrast":
            color_scheme = ft.ColorScheme(
                primary=cls.colors["accent"],
                on_primary=cls.colors["surface"],
                surface=cls.colors["panel_bg"],
                on_surface=cls.colors["text_primary"],
            )
            page.theme = ft.Theme(font_family="Inter", color_scheme=color_scheme)
        else:
            page.theme = ft.Theme(
                font_family="Inter",
                color_scheme_seed=cls.colors["accent"],
                visual_density=ft.VisualDensity.COMFORTABLE
            )
            
        # 4. Direct overrides
        page.bgcolor = cls.colors["surface"]
        
        page.update()
