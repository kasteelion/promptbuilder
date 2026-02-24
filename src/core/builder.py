import re
import random
import copy
from typing import Any, Dict, List, Optional


from utils.color_scheme import substitute_colors, substitute_signature_color
from utils.text_utils import normalize_blank_lines

from .renderers import CharacterRenderer, NotesRenderer, OutfitRenderer, PoseRenderer, SceneRenderer
from .definitions import PromptConfig, SelectedCharacterConfig

# Pre-compiled regex for performance
RE_MODIFIER = re.compile(r"\{modifier\}")


from .renderers import CharacterRenderer, NotesRenderer, OutfitRenderer, PoseRenderer, SceneRenderer, ColorSchemeRenderer
from .models import PromptConfig, SelectedCharacterConfig, CharacterDetails

# Pre-compiled regex for performance
RE_MODIFIER = re.compile(r"\{modifier\}")


class PromptBuilder:
    """Builds formatted prompts from character, scene, and style data."""

    def __init__(
        self,
        characters: Dict[str, Any],
        base_prompts: Dict[str, str],
        poses: Dict[str, Dict[str, str]],
        color_schemes: Dict[str, Dict[str, str]] = None,
        modifiers: Dict[str, str] = None,
        framing: Dict[str, str] = None,
    ):
        """Initialize the prompt builder.

        Args:
            characters: Dictionary of character data (will be converted to CharacterDetails)
            base_prompts: Dictionary of base art style prompts
            poses: Dictionary of pose categories and presets
            color_schemes: Dictionary of color schemes
            modifiers: Dictionary of outfit modifiers
            framing: Dictionary of framing modifiers
        """
        # Store reference to the shared character dictionary to ensure lazy loading updates are visible
        self.characters = characters
        self.base_prompts = base_prompts
        self.poses = poses
        self.color_schemes = color_schemes or {}
        self.modifiers = modifiers or {}
        self.framing = framing or {}

    def generate(self, config: Union[Dict[str, Any], PromptConfig]) -> str:
        """Generate a formatted prompt from configuration.

        Args:
            config: Configuration (dictionary or PromptConfig model).

        Returns:
            Formatted prompt string
        """
        # Ensure config is a PromptConfig model
        if isinstance(config, dict):
            config = PromptConfig(**config)

        parts: List[str] = []
        
        # Reset ephemeral generation state
        self._active_team_scheme = None

        # 1. Base Prompt
        base_data = self.base_prompts.get(config.base_prompt, "")
        base = base_data.get("description", "") if isinstance(base_data, dict) else base_data
        if base:
            parts.append(base)
        parts.append("---")

        # 2. Scene
        scene = config.scene.strip()
        if scene:
            parts.append(SceneRenderer.render(scene))

        # 3. Characters
        char_names = [c.name for c in config.selected_characters]
        
        # Pre-resolve team scheme if needed for multi-character consistency
        self._resolve_active_team_scheme(config)

        for idx, char_config in enumerate(config.selected_characters):
            char_data = self.characters.get(char_config.name)
            if not char_data:
                continue
            
            # Ensure char_data is a Pydantic model
            if isinstance(char_data, dict):
                char_data = CharacterDetails(**char_data)
                # Cache the conversion back in the source dict if possible, 
                # but for generate it's safer to just use it.

            parts.append(CharacterRenderer.render(
                idx, 
                char_config, 
                char_data,
                self.modifiers,
                self.poses,
                self.framing,
                self.color_schemes,
                self._active_team_scheme
            ))

        # 4. Notes
        if config.notes:
            parts.append(NotesRenderer.render(config.notes, char_names))

        out = "\n\n".join([p for p in parts if p])
        return normalize_blank_lines(out)

    def _resolve_active_team_scheme(self, config: PromptConfig):
        """Pick a consistent team scheme if any character requires it."""
        requires_team = False
        for char_config in config.selected_characters:
            char_data = self.characters.get(char_config.name)
            if not char_data: continue
            
            outfit_data = char_data.outfits.get(char_config.outfit, "")
            
            # Check for {team} placeholder
            if isinstance(outfit_data, str) and "{team}" in outfit_data:
                requires_team = True
            elif isinstance(outfit_data, dict):
                for v in outfit_data.values():
                    if isinstance(v, str) and "{team}" in v:
                        requires_team = True
                        break
            
            if requires_team:
                # Only pick if one isn't explicitly set in config (first one wins for now)
                if not char_config.color_scheme or char_config.color_scheme == "The Standard":
                    team_schemes = [s for s in self.color_schemes.values() if isinstance(s, dict) and "team" in s]
                    if team_schemes:
                        self._active_team_scheme = random.choice(team_schemes)
                break

    def generate_summary(self, config: Union[Dict[str, Any], PromptConfig]) -> str:
        """Generate a condensed summary of the prompt."""
        if isinstance(config, dict):
            config = PromptConfig(**config)

        summary_parts = []
        
        # 1. Art Style
        if config.base_prompt and config.base_prompt != "Default":
            summary_parts.append(f"🎨 **{config.base_prompt}**")
        
        # 2. Scene
        scene = config.scene.strip()
        if scene:
            short_scene = scene.split("\n")[0]
            if len(short_scene) > 60:
                short_scene = short_scene[:57] + "..."
            summary_parts.append(f"🎬 {short_scene}")
            
        # 3. Moods
        moods = config.metadata.get("moods")
        if moods:
            moods_list = sorted(list(moods))
            summary_parts.append(f"✨ **Moods**: {', '.join(moods_list)}")

        # 4. Characters
        if config.selected_characters:
            char_summaries = []
            for char_config in config.selected_characters:
                name = char_config.name
                outfit = char_config.outfit or "Base"
                pose = char_config.pose_preset or "Default"
                if char_config.action_note:
                    pose = "Custom Action"
                
                parts = [outfit]
                scheme_name = char_config.color_scheme
                
                char_def = self.characters.get(name)
                if char_def:
                    outfit_data = char_def.outfits.get(outfit, "")
                    outfit_str = str(outfit_data) if not isinstance(outfit_data, dict) else " ".join(str(v) for v in outfit_data.values() if isinstance(v, str))
                    
                    supports_schemes = any(f"{{{k}}}" in outfit_str for k in ("primary_color", "secondary_color", "accent"))
                    supports_sig = "{signature_color}" in outfit_str or "(signature)" in outfit_str
                    
                    if scheme_name and scheme_name not in ("Default (No Scheme)", "The Standard") and supports_schemes:
                        scheme = self.color_schemes.get(scheme_name)
                        if scheme:
                            team_name = scheme.get("team", scheme_name)
                            parts.append(team_name)
                    
                    if char_config.use_signature_color and supports_sig:
                        if char_def.signature_color:
                            parts.append(f"Sig: {char_def.signature_color}")

                parts.append(pose)
                char_summaries.append(f"   **{name}** ({' • '.join(parts)})")
            
            summary_parts.append("👥 **Characters**:")
            summary_parts.extend(char_summaries)
            
        # 5. Interaction/Notes
        notes = config.notes.strip()
        if notes:
            is_interaction = "(" in notes and ")" in notes and ":" in notes
            icon = "🤝" if is_interaction else "📝"
            label = "Interaction" if is_interaction else "Action"
            
            short_notes = notes.split("\n")[0]
            if len(short_notes) > 70:
                short_notes = short_notes[:67] + "..."
            summary_parts.append(f"{icon} **{label}**: {short_notes}")
            
        return "\n".join(summary_parts) if summary_parts else "No characters or scene selected."
