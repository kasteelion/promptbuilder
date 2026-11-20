import flet as ft
from typing import Dict, Any, Optional
from utils import logger
from dataclasses import dataclass, field
from core.builder import PromptBuilder
from logic.data_loader import DataLoader
from logic.randomizer import PromptRandomizer
from core.models import CharacterDetails, CharacterMetadata, PromptConfig

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
    gemma_client: Optional[Any] = None

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

    def load_metadata_fast(self):
        """Pre-load character metadata immediately (30ms) for instant gallery rendering."""
        if not self.ctx.characters_metadata:
            self.ctx.characters_metadata = self.data_loader.load_characters_metadata()

    def load_data(self):
        loader = self.data_loader
        
        # 1. Load Metadata (Fast, for Gallery)
        if not self.ctx.characters_metadata:
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
        self.ctx.outfits = loader.load_outfits()
        
        # 3. [LAZY] Pre-load characters that are already in state (if any from session)
        for char_conf in self.state.get("selected_characters", []):
            name = char_conf.get("name") if isinstance(char_conf, dict) else char_conf.name
            self.ensure_character_loaded(name)

        # 4. Initialize Automation/Randomizer/Builder/Gemma
        try:
            from logic.automation import AutomationOrchestrator
            self.ctx.automation_controller = AutomationOrchestrator(self.ctx, app_state=self)
        except Exception as e:
            logger.warning(f"AutomationOrchestrator failed to load: {e}")
            
        try:
            from utils.gemma_client import GemmaClient
            from utils.preferences import PreferencesManager
            prefs = PreferencesManager()
            ai_provider = prefs.get("ai_provider", "auto")
            gemini_model = prefs.get("gemini_model", "gemini-2.5-flash")
            gemini_api_key = prefs.get("gemini_api_key") or None
            ollama_model = prefs.get("ollama_model", "gemma2")
            ollama_base = prefs.get("ollama_base_url", "http://localhost:11434")

            self.ctx.gemma_client = GemmaClient(
                mode=ai_provider,
                api_key=gemini_api_key,
                cloud_model=gemini_model,
                ollama_model=ollama_model,
                ollama_base=ollama_base,
            )
        except Exception as e:
            logger.warning(f"GemmaClient failed to load: {e}")

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
            self.ctx.framing,
            self.ctx.outfits # Pass global outfits for fallbacks
        )
        
        # Check for missing character portraits in background
        if self.ctx.automation_controller:
            self._check_missing_portraits()

    def _check_missing_portraits(self):
        if getattr(self, '_portraits_scanned', False):
            return
        self._portraits_scanned = True

        from utils.preferences import PreferencesManager
        prefs = PreferencesManager()
        if not prefs.get("auto_generate_missing_portraits", False):
            return
        
        import pathlib
        import re

        async def _scan():
            data_dir = pathlib.Path("assets/data/characters")
            for char_name, meta in self.ctx.characters_metadata.items():
                if hasattr(meta, "photo") and meta.photo:
                    photo_path = data_dir / meta.photo
                    has_photo = photo_path.exists() or photo_path.with_suffix(".webp").exists()
                    if not has_photo:
                        logger.info(f"Missing photo for {char_name}, queueing generation...")
                        self.ctx.automation_controller.generate_character_portrait(char_name)
                else:
                    filename = char_name.lower().replace(" ", "_")
                    filename = re.sub(r'[^a-z0-9_]', '', filename) + "_photo.png"
                    photo_path = data_dir / filename
                    has_photo = photo_path.exists() or photo_path.with_suffix(".webp").exists()
                    if not has_photo:
                        logger.info(f"Missing photo for {char_name}, queueing generation...")
                        self.ctx.automation_controller.generate_character_portrait(char_name)

        if self.page:
            self.page.run_task(_scan)

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

    def get_prompt(self, format_type: str = "markdown") -> str:
        if not self.builder: return ""
        # Convert state to PromptConfig model for builder
        config = PromptConfig(**self.state)
        return self.builder.generate(config, format_type=format_type)

    def get_summary(self) -> str:
        if not self.builder: return ""
        config = PromptConfig(**self.state)
        return self.builder.generate_summary(config)


