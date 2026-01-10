import re
from typing import Any, Dict, List

from utils.color_scheme import substitute_colors, substitute_signature_color
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
        framing: Dict[str, str] = None,
    ):
        """Initialize the prompt builder.

        Args:
            characters: Dictionary of character data
            base_prompts: Dictionary of base art style prompts
            poses: Dictionary of pose categories and presets
            color_schemes: Dictionary of color schemes
            modifiers: Dictionary of outfit modifiers
            framing: Dictionary of framing modifiers
        """
        self.characters = characters
        self.base_prompts = base_prompts
        self.poses = poses
        self.color_schemes = color_schemes or {}
        self.modifiers = modifiers or {}
        self.framing = framing or {}

    def generate(self, config: Dict[str, Any]) -> str:
        """Generate a formatted prompt from configuration.

        Args:
            config: Configuration dictionary with selected characters, scene, notes, etc.

        Returns:
            Formatted prompt string
        """
        parts: List[str] = []

        base_data = self.base_prompts.get(config.get("base_prompt"), "")
        if isinstance(base_data, dict):
            base = base_data.get("description", "")
        else:
            base = base_data

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
            
            # Apply framing modifier if selected
            framing_name = char.get("framing_mode")
            framing_text = self.framing.get(framing_name, "")
            if framing_text:
                pose = f"{framing_text} {pose}"
            
            # Apply outfit modifiers/traits if selected
            traits = char.get("outfit_traits", [])
            if not traits and char.get("outfit_modifier"):
                traits = [char.get("outfit_modifier")]
            
            # Local modifiers defined within the outfit file itself
            local_modifiers = {}
            if isinstance(outfit, dict) and "modifiers" in outfit:
                local_modifiers = outfit.get("modifiers", {})
            
            # Global/legacy custom modifiers from character data
            custom_modifiers = char.get("custom_modifiers", {})
            
            modifier_parts = []
            for t in traits:
                # Priority: 1. Local (Outfit-specific), 2. Custom (Char-specific), 3. Global
                if t in local_modifiers:
                    modifier_parts.append(local_modifiers[t])
                elif t in custom_modifiers:
                    modifier_parts.append(custom_modifiers[t])
                elif t in self.modifiers:
                    modifier_parts.append(self.modifiers[t])
            
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
                        # Skip metadata keys during substitution to be safe
                        if k in ("tags", "modifiers"): continue
                        
                        v = re.sub(r"\{modifier\}", modifier_text, v)
                        v = substitute_signature_color(v, sig_color, use_sig)
                        outfit[k] = substitute_colors(v, scheme)
            # Apply character-level traits if selected
            char_traits = char.get("character_traits", [])
            char_traits_def = data.get("traits", {})
            appearance = data.get("appearance", "")
            
            trait_texts = []
            for ct in char_traits:
                if ct in char_traits_def:
                    trait_texts.append(char_traits_def[ct])
            
            if trait_texts:
                # Append traits to appearance, ensuring proper punctuation
                if appearance and not appearance.endswith((".", ";")):
                    appearance += ";"
                appearance += " " + "; ".join(trait_texts)

            parts.append(
                CharacterRenderer.render(
                    idx,
                    char["name"],
                    appearance,
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
