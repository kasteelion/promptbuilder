import flet as ft
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from core.builder import PromptBuilder
from logic.data_loader import DataLoader
from logic.randomizer import PromptRandomizer
from core.models import CharacterDetails, CharacterMetadata, PromptConfig, SelectedCharacterConfig

@dataclass
class AppContext:
    characters: Dict[str, CharacterDetails] = field(default_factory=dict)
    characters_metadata: Dict[str, CharacterMetadata] = field(default_factory=dict)
    base_prompts: Dict[str, Any] = field(default_factory=dict)
    scenes: Dict[str, Any] = field(default_factory=dict)
    poses: Dict[str, Any] = field(default_factory=dict)
    interactions: Dict[str, Any] = field(default_factory=dict)
    color_schemes: Dict[str, Any] = field(default_factory=dict)
    modifiers: Dict[str, str] = field(default_factory=dict)
    framing: Dict[str, str] = field(default_factory=dict)
    scene_constraints: Dict[str, Any] = field(default_factory=dict)
    tag_rules: Dict[str, Any] = field(default_factory=dict)
    scoring_config: Dict[str, Any] = field(default_factory=dict)
    randomizer: Optional[PromptRandomizer] = None
    automation_controller: Optional[Any] = None

class AppState:
    def __init__(self, page: ft.Page):
        self.page = page
        self.data_loader = DataLoader()
        self.ctx = AppContext()
        
        self.state = {
            "selected_characters": [], # List of SelectedCharacterConfig
            "base_prompt": "Detailed",
            "scene": "",
            "notes": "",
            "scene_category": None,
            "scene_preset": None,
            "interaction_category": None,
            "interaction_preset": None,
            "metadata": {}
        }
        
        self.builder: Optional[PromptBuilder] = None
        self.current_theme = "Dark"

    def load_data(self):
        loader = self.data_loader
        
        # 1. Load Metadata (Fast, for Gallery)
        self.ctx.characters_metadata = loader.load_characters_metadata()
        
        # 2. Load other presets
        self.ctx.base_prompts = loader.load_base_prompts()
        self.ctx.scenes = loader.load_presets("scenes.md")
        self.ctx.interactions = loader.load_interactions()
        self.ctx.color_schemes = loader.load_color_schemes()
        self.ctx.framing = loader.load_framing()
        self.ctx.poses = loader.load_presets("poses.md")
        self.ctx.modifiers = loader.load_modifiers()
        self.ctx.scene_constraints = loader.load_scene_constraints()
        self.ctx.tag_rules = loader.load_tag_rules()
        self.ctx.scoring_config = loader.load_scoring_config()
        
        # 3. [LAZY] Pre-load characters that are already in state (if any from session)
        for char_conf in self.state.get("selected_characters", []):
            name = char_conf.get("name") if isinstance(char_conf, dict) else char_conf.name
            self.ensure_character_loaded(name)

        # 4. Initialize Automation/Randomizer/Builder
        try:
            from logic.automation_controller import AutomationController
            self.ctx.automation_controller = AutomationController(self.ctx, app_state=self)
        except Exception as e:
            print(f"DEBUG: AutomationController load fail: {e}")

        # Initialize Randomizer (Will need full characters for tag matching, so we might still need to load some)
        # For now, we'll let Randomizer load what it needs or handle error gracefully
        self.ctx.randomizer = PromptRandomizer(
            self.ctx.characters,
            self.ctx.base_prompts,
            self.ctx.poses,
            self.ctx.scenes,
            self.ctx.interactions,
            self.ctx.color_schemes,
            self.ctx.modifiers,
            self.ctx.framing,
            scene_constraints=self.ctx.scene_constraints,
            tag_rules=self.ctx.tag_rules,
            scoring_config=self.ctx.scoring_config
        )
        
        self.builder = PromptBuilder(
            self.ctx.characters,
            self.ctx.base_prompts,
            self.ctx.poses,
            self.ctx.color_schemes,
            self.ctx.modifiers,
            self.ctx.framing
        )

    def ensure_character_loaded(self, name: str) -> bool:
        """Loads full character details if not already in memory."""
        if name in self.ctx.characters:
            return True
        try:
            details = self.data_loader.get_character_details(name)
            self.ctx.characters[name] = details
            
            # Pre-compute tags for the new character if randomizer exists
            if self.ctx.randomizer:
                self.ctx.randomizer._precompute_character_tags(name, details)
                
            return True
        except Exception as e:
            print(f"Error lazy loading character {name}: {e}")
            return False

    def refresh_data(self):
        """Force clear cache and reload all data."""
        self.data_loader.clear_cache()
        self.ctx.characters.clear() # Clear full data cache
        self.load_data()

    def get_prompt(self) -> str:
        if not self.builder: return ""
        # Convert state to PromptConfig model for builder
        config = PromptConfig(**self.state)
        return self.builder.generate(config)

    def get_summary(self) -> str:
        if not self.builder: return ""
        config = PromptConfig(**self.state)
        return self.builder.generate_summary(config)


