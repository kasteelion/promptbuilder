import re
from typing import Any, Dict, List

from utils.color_scheme import parse_color_schemes, substitute_colors, substitute_signature_color
from utils.text_utils import normalize_blank_lines

from .renderers import CharacterRenderer, NotesRenderer, OutfitRenderer, PoseRenderer, SceneRenderer


class PromptBuilder:
    """Builds formatted prompts from character, scene, and style data."""

    def __init__(
        self,
        characters: Dict[str, Any],
        base_prompts: Dict[str, str],
        poses: Dict[str, Dict[str, str]],
        color_schemes: Dict[str, Dict[str, str]] = None,
        modifiers: Dict[str, str] = None,
    ):
        """Initialize the prompt builder.

        Args:
            characters: Dictionary of character data
            base_prompts: Dictionary of base art style prompts
            poses: Dictionary of pose categories and presets
            color_schemes: Dictionary of color schemes
            modifiers: Dictionary of outfit modifiers
        """
        self.characters = characters
        self.base_prompts = base_prompts
        self.poses = poses
        self.color_schemes = color_schemes or {}
        self.modifiers = modifiers or {}

    def generate(self, config: Dict[str, Any]) -> str:
        """Generate a formatted prompt from configuration.

        Args:
            config: Configuration dictionary with selected characters, scene, notes, etc.

        Returns:
            Formatted prompt string
        """
        parts: List[str] = []

        base = self.base_prompts.get(config.get("base_prompt"), "")
        if base:
            parts.append(base)
        parts.append("---")

        scene = config.get("scene", "").strip()
        if scene:
            parts.append(SceneRenderer.render(scene))

        for idx, char in enumerate(config.get("selected_characters", [])):
            data = self.characters.get(char["name"], {})
            outfit = data.get("outfits", {}).get(char.get("outfit", ""), "")
            pose = char.get("action_note") or self.poses.get(char.get("pose_category"), {}).get(
                char.get("pose_preset"), ""
            )
            
            # Apply outfit modifiers/traits if selected
            # Support both single string (legacy) and list of traits
            traits = char.get("outfit_traits", [])
            if not traits and char.get("outfit_modifier"):
                traits = [char.get("outfit_modifier")]
            
            modifier_parts = [self.modifiers.get(t, "") for t in traits if t in self.modifiers]
            # Filter out empty strings and join with space (since text usually includes its own commas)
            modifier_text = "".join(modifier_parts).strip()
            
            scheme_name = char.get("color_scheme")
            scheme = self.color_schemes.get(
                scheme_name, self.color_schemes.get("The Standard", {})
            )
            
            # Apply signature color substitution if applicable
            sig_color = data.get("signature_color")
            use_sig = char.get("use_signature_color", False)
            
            if isinstance(outfit, str):
                # Replace {modifier} placeholder before color substitution
                outfit = re.sub(r"\{modifier\}", modifier_text, outfit)
                # Apply signature color logic
                outfit = substitute_signature_color(outfit, sig_color, use_sig)
                outfit = substitute_colors(outfit, scheme)
            elif isinstance(outfit, dict):
                # Work on a copy to avoid mutating the source data
                outfit = outfit.copy()
                for k, v in outfit.items():
                    if isinstance(v, str):
                        v = re.sub(r"\{modifier\}", modifier_text, v)
                        v = substitute_signature_color(v, sig_color, use_sig)
                        outfit[k] = substitute_colors(v, scheme)
            parts.append(
                CharacterRenderer.render(
                    idx,
                    char["name"],
                    data.get("appearance", ""),
                    OutfitRenderer.render(outfit),
                    PoseRenderer.render(pose),
                )
            )

        notes = config.get("notes", "")
        if notes:
            parts.append(NotesRenderer.render(notes))
        out = "\n\n".join([p for p in parts if p])
        return normalize_blank_lines(out)

    def generate_summary(self, config: Dict[str, Any]) -> str:
        """Generate a condensed summary of the prompt.

        Args:
            config: Configuration dictionary.

        Returns:
            Condensed summary string.
        """
        summary_parts = []
        
        scene = config.get("scene", "").strip()
        if scene:
            # First line of scene or first 50 chars
            short_scene = scene.split("\n")[0]
            if len(short_scene) > 60:
                short_scene = short_scene[:57] + "..."
            summary_parts.append(f"🎬 {short_scene}")
            
        chars = config.get("selected_characters", [])
        if chars:
            char_summaries = []
            for char in chars:
                name = char["name"]
                outfit = char.get("outfit", "Base")
                pose = char.get("pose_preset") or "Default"
                if char.get("action_note"):
                    pose = "Custom"
                
                parts = [outfit]
                scheme_name = char.get("color_scheme")
                if scheme_name:
                    scheme = self.color_schemes.get(scheme_name, {})
                    if "team" in scheme:
                        parts.append(scheme["team"])
                
                # Add signature color info if active
                if char.get("use_signature_color"):
                    char_def = self.characters.get(name, {})
                    sig_color = char_def.get("signature_color")
                    if sig_color:
                        parts.append(f"Sig: {sig_color}")

                parts.append(pose)
                
                char_summaries.append(f"{name} ({', '.join(parts)})")
            summary_parts.append("👥 " + ", ".join(char_summaries))
            
        notes = config.get("notes", "").strip()
        if notes:
            short_notes = notes.split("\n")[0]
            if len(short_notes) > 60:
                short_notes = short_notes[:57] + "..."
            summary_parts.append(f"📝 {short_notes}")
            
        return "\n".join(summary_parts) if summary_parts else "No characters or scene selected."
