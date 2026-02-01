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
        
        # Load AutomationController
        try:
            from logic.automation_controller import AutomationController
            self.ctx.automation_controller = AutomationController(self.ctx)
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
            self.ctx.framing
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

    def add_character(self, name: str):
        """Toggle character by name. Picks valid defaults based on character data."""
        existing_idx = next((i for i, c in enumerate(self.state["selected_characters"]) if c["name"] == name), -1)
        if existing_idx > -1:
            self.state["selected_characters"].pop(existing_idx)
        else:
            char_info = self.ctx.characters.get(name, {})
            
            # Smart defaults: prioritize 'Personal' category and 'Base' outfit
            outfit_cats = char_info.get("outfits_categorized", {})
            cat = "Personal" if "Personal" in outfit_cats else (sorted(outfit_cats.keys())[0] if outfit_cats else "Casual Wear")
            
            outfits = outfit_cats.get(cat, {})
            if "Base" in outfits:
                outfit = "Base"
            elif outfits:
                outfit = sorted(outfits.keys())[0]
            else:
                outfit = "Base"
                
            p_cats = sorted(self.ctx.poses.keys())
            # Prioritize "Standing" or "Default" category if available
            p_cat = next((c for c in p_cats if c in ["Standing", "Default", "Generic"]), p_cats[0] if p_cats else "Standing")
            
            p_presets = sorted(self.ctx.poses.get(p_cat, {}).keys())
            # Prioritize "Default" preset if available
            p_preset = next((p for p in p_presets if p in ["Default", "Standard", "Idle"]), p_presets[0] if p_presets else "Default")
            
            char_data = {
                "name": name,
                "outfit": outfit,
                "outfit_category": cat,
                "pose_category": p_cat,
                "pose_preset": p_preset,
                "framing_mode": "Portrait",
                "color_scheme": "The Standard",
                "use_signature_color": False,
                "character_traits": [],
                "outfit_traits": [],
                "action_note": "",
                "_expanded": True
            }
            self.state["selected_characters"].append(char_data)

    def remove_character(self, name: str):
        """Alias for add_character to prevent crashes from legacy UI calls."""
        self.add_character(name)

    def update_character(self, index: int, updates: Dict[str, Any]):
        if 0 <= index < len(self.state["selected_characters"]):
            self.state["selected_characters"][index].update(updates)

    def get_prompt(self) -> str:
        if not self.builder: return ""
        return self.builder.generate(self.state)

    def get_summary(self) -> str:
        if not self.builder: return ""
        return self.builder.generate_summary(self.state)

    def get_character_summary(self, index: int) -> str:
        """Get condensed summary for header: 'OUTFIT | POSE'."""
        if not (0 <= index < len(self.state["selected_characters"])):
            return "UNKNOWN"
        char = self.state["selected_characters"][index]
        outfit = char.get("outfit", "Base")
        pose = char.get("action_note") or char.get("pose_preset", "Default")
        if len(outfit) > 15: outfit = outfit[:12] + "..."
        if len(pose) > 15: pose = pose[:12] + "..."
        return f"{outfit} | {pose}".upper()

    def move_character(self, index: int, direction: int):
        """Move character up or down in the list."""
        chars = self.state["selected_characters"]
        new_idx = index + direction
        if 0 <= new_idx < len(chars):
            chars[index], chars[new_idx] = chars[new_idx], chars[index]
