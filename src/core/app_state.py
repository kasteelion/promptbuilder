import flet as ft
from typing import Dict, Any, List, Optional
from core.builder import PromptBuilder
from logic.data_loader import DataLoader
from logic.randomizer import PromptRandomizer

class AppState:
    def __init__(self, page: ft.Page):
        self.page = page
        self.data_loader = DataLoader()
        self.ctx: Any = type('Context', (), {})() # Simple object to hold context
        self.ctx.characters = {}
        self.ctx.base_prompts = {}
        self.ctx.scenes = {}
        self.ctx.poses = {}
        self.ctx.interactions = {}
        self.ctx.color_schemes = {}
        self.ctx.modifiers = {}
        self.ctx.framing = {}
        self.ctx.randomizer = None
        self.ctx.automation_controller = None
        
        self.state = {
            "selected_characters": [],
            "base_prompt": "Detailed",
            "scene": "",
            "notes": "",
            "scene_category": None,
            "scene_preset": None,
            "interaction_category": None,
            "interaction_preset": None,
        }
        
        self.builder: Optional[PromptBuilder] = None
        self.current_theme = "Dark"

    def load_data(self):
        loader = self.data_loader
        self.ctx.characters = loader.load_characters()
        self.ctx.base_prompts = loader.load_base_prompts()
        self.ctx.scenes = loader.load_presets("scenes.md")
        self.ctx.interactions = loader.load_interactions()
        self.ctx.color_schemes = loader.load_color_schemes()
        self.ctx.framing = loader.load_framing()
        self.ctx.poses = loader.load_presets("poses.md")
        self.ctx.modifiers = loader.load_modifiers()
        
        # [NEW] Load External Configs
        self.ctx.scene_constraints = loader.load_scene_constraints()
        self.ctx.tag_rules = loader.load_tag_rules()
        
        # Load AutomationController
        try:
            from logic.automation_controller import AutomationController
            self.ctx.automation_controller = AutomationController(self.ctx, app_state=self)
        except Exception as e:
            print(f"DEBUG: AutomationController load fail: {e}")

        # Initialize Randomizer
        self.ctx.randomizer = PromptRandomizer(
            self.ctx.characters,
            self.ctx.base_prompts,
            self.ctx.poses,
            self.ctx.scenes,
            self.ctx.interactions,
            self.ctx.color_schemes,
            self.ctx.modifiers,
            self.ctx.framing,
            # [NEW] Inject Configs
            scene_constraints=self.ctx.scene_constraints,
            tag_rules=self.ctx.tag_rules
        )
        # Trigger UI population (handled in main.py)
        
        # NOW initialize PromptBuilder (Safe after data is loaded)
        self.builder = PromptBuilder(
            self.ctx.characters,
            self.ctx.base_prompts,
            self.ctx.poses,
            self.ctx.color_schemes,
            self.ctx.modifiers,
            self.ctx.framing
        )

    def refresh_data(self):
        """Force clear cache and reload all data."""
        self.data_loader.clear_cache()
        self.load_data()

    # Character logic moved to logic/character_logic.py

    def get_prompt(self) -> str:
        if not self.builder: return ""
        return self.builder.generate(self.state)

    def get_summary(self) -> str:
        if not self.builder: return ""
        return self.builder.generate_summary(self.state)


