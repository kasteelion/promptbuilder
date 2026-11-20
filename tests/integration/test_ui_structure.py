import sys
import os
import unittest
from unittest.mock import MagicMock

# Allow imports from project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import flet as ft

# Import modular sections
# Note: These imports require 'ui' and 'core' keys in sys.modules or similar if they have specific dependencies
# But since we appended root to sys.path, promptbuilder.ui... should resolve if we import as ui.sections...

from ui.sections.toolbar import ToolbarSection
from ui.sections.gallery import GallerySection
from ui.sections.roster import RosterSection
from ui.sections.sidebar import SidebarSection
from ui.sections.console import ConsoleSection

from core.flet_theme_manager import ThemeManager

class TestUIStructure(unittest.TestCase):
    
    def setUp(self):
        # Mock the main application instance
        self.app = MagicMock()
        # Mock specific handlers accessed in __init__
        self.app.handle_ui_change = MagicMock()
        self.app.handle_scene_cat_change = MagicMock()
        self.app.handle_scene_preset_change = MagicMock()
        self.app.handle_interaction_cat_change = MagicMock()
        self.app.handle_interaction_preset_change = MagicMock()
        self.app.close_gallery_overlay = MagicMock()
        self.app.handle_copy = MagicMock()
        self.app.handle_generate = MagicMock()
        
        # Disable dropdown syncing to avoid Mock comparisons
        self.app.base_prompt_dd = None
        self.app.output_field = None
        
        # Mock Context
        self.app.ctx = MagicMock()
        self.app.ctx.characters = {}
        self.app.ctx.poses = {}
        
        ThemeManager.colors = {"surface": "b", "panel_bg": "g", "outline": "w", "text_primary": "w", "text_secondary": "g", "active_item": "b", "accent": "c", "surface_variant": "black", "error": "r", "header_fg": "w", "bg_gradient_start": "g", "bg_gradient_end": "b", "success": "g"}
        ThemeManager.styles = {"radius": 5, "padding": 10}

    def test_sidebar_instantiation(self):
        sidebar = SidebarSection(self.app)
        self.assertIsInstance(sidebar, ft.Container)

    def test_console_instantiation(self):
        console = ConsoleSection(self.app)
        self.assertIsInstance(console, ft.Column) # ConsoleSection inherits Column

    def test_gallery_instantiation(self):
        gallery = GallerySection(self.app)
        self.assertIsInstance(gallery, ft.Container)
        
    def test_toolbar_instantiation(self):
        toolbar = ToolbarSection(self.app)
        self.assertIsInstance(toolbar, ft.Container)

    def test_roster_instantiation(self):
        roster = RosterSection(self.app)
        self.assertIsInstance(roster, ft.Container)

if __name__ == '__main__':
    unittest.main()
