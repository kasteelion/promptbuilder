"""Renderers for converting prompt data into formatted text.

This module provides specialized renderers for different prompt components:
- OutfitRenderer: Formats outfit dictionaries into text, handling color substitutions and modifiers.
- PoseRenderer: Formats pose descriptions, including framing.
- SceneRenderer: Formats scene/setting information.
- NotesRenderer: Formats additional notes with character name replacement.
- CharacterRenderer: Formats complete character information, coordinating other renderers.
- ColorSchemeRenderer: Resolves and formats color schemes.
- ModifierRenderer: Resolves and formats outfit modifiers.

Each renderer follows a consistent interface with a static render() method.
"""

import re
import copy
import random
from typing import Any, Dict, List, Optional, Union
from .models import SelectedCharacterConfig, CharacterDetails, OutfitItem

# Pre-compiled regex for performance
RE_MODIFIER = re.compile(r"\{modifier\}")


def strip_html_comments(text: str) -> str:
    """Remove HTML comment blocks from text.

    Args:
        text: Input text potentially containing HTML comments

    Returns:
        Text with all <!-- ... --> blocks removed
    """
    if not text:
        return text
    # Remove HTML comments (including multiline)
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL).strip()


class OutfitRenderer:
    """Renders outfit data into formatted text.

    Supports both detailed (multi-line) and compact (single-line) output modes.
    Handles structured outfit dictionaries and string descriptions.
    """

    @staticmethod
    def render(
        outfit: Union[str, Dict[str, Any]], 
        mode: str = "detailed",
        modifier_text: str = "",
        scheme: Dict[str, str] = None,
        sig_color: str = None,
        use_sig: bool = False
    ) -> str:
        """Render outfit data to formatted text with substitutions.

        Args:
            outfit: Outfit string or dictionary.
            mode: Output mode ("detailed" or "compact").
            modifier_text: Resolved modifier text to substitute.
            scheme: Color scheme dictionary for substitutions.
            sig_color: Character's signature color.
            use_sig: Whether to use the signature color.

        Returns:
            Formatted and substituted outfit text.
        """
        from utils.color_scheme import substitute_colors, substitute_signature_color

        if not outfit:
            return ""

        # Deepcopy to prevent mutation leakage if it's a dict
        data = copy.deepcopy(outfit) if isinstance(outfit, dict) else outfit

        # 1. Substitution Logic
        if isinstance(data, str):
            data = RE_MODIFIER.sub(modifier_text, data)
            data = substitute_signature_color(data, sig_color, use_sig)
            if scheme:
                data = substitute_colors(data, scheme)
        elif isinstance(data, dict):
            # Known metadata keys to exclude from prompt rendering
            meta_keys = {"tags", "modifiers", "_expanded_tags", "one_piece"}
            
            for k, v in data.items():
                if isinstance(v, str) and k not in meta_keys:
                    v = RE_MODIFIER.sub(modifier_text, v)
                    v = substitute_signature_color(v, sig_color, use_sig)
                    if scheme:
                        v = substitute_colors(v, scheme)
                    data[k] = v

        # 2. Formatting Logic
        if isinstance(data, dict):
            keys = ["Top", "Bottom", "Footwear", "Accessories", "Hair", "Makeup"]
            # Filter standard keys that exist
            present = [f"- {k}: {data[k]}" for k in keys if data.get(k)]
            
            # Additional keys that aren't metadata or standard keys
            extras = []
            for k, v in data.items():
                if k in meta_keys or k in keys:
                    continue
                if k == "description":
                    extras.append(str(v))
                else:
                    extras.append(f"- {k}: {v}")
                    
            lines = present + extras
            if mode == "detailed":
                return "\n".join(lines)
            else:
                return "; ".join([entry.split(": ", 1)[1] if ": " in entry else entry for entry in lines])
        
        return str(data)


class PoseRenderer:
    """Renders pose/action descriptions, including framing."""

    @staticmethod
    def render(pose_description: str, framing_text: str = "") -> str:
        """Render pose description with optional framing.

        Args:
            pose_description: Text description of the pose or action.
            framing_text: Optional framing/shot type text to prepend.

        Returns:
            Formatted pose text.
        """
        pose = pose_description or ""
        if framing_text:
            pose = f"{framing_text} {pose}"
        return pose.strip()


class SceneRenderer:
    """Renders scene/setting information with formatting.

    Adds markdown-style headers and separators to scene descriptions.
    """

    @staticmethod
    def render(scene: str) -> str:
        """Render scene description with header and separator.

        Args:
            scene: Text description of the scene/setting

        Returns:
            Formatted scene text with **SCENE/SETTING:** header and separator.
            Empty string if scene is empty or whitespace-only.

        Example:
            >>> SceneRenderer.render("Coffee shop interior")
            '**SCENE/SETTING:**\\nCoffee shop interior\\n---'
        """
        if not scene.strip():
            return ""
        return f"**SCENE/SETTING:**\n{scene}\n---"


class NotesRenderer:
    """Renders additional notes with formatting and character replacement."""

    @staticmethod
    def render(notes: str, character_names: List[str] = None) -> str:
        """Render additional notes with character identifier replacement.

        Args:
            notes: Additional notes or instructions text.
            character_names: List of character names for {charN} replacement.

        Returns:
            Formatted notes text.
        """
        if not notes.strip():
            return ""

        text = notes
        if character_names and "{char" in text:
            for i, name in enumerate(character_names):
                text = text.replace(f"{{char{i+1}}}", name)

        return f"**Additional Notes:**\n{text}"


class CharacterRenderer:
    """Renders complete character information, coordinating other renderers."""

    @staticmethod
    def render(
        idx: int, 
        config: SelectedCharacterConfig, 
        data: CharacterDetails,
        shared_modifiers: Dict[str, str],
        shared_poses: Dict[str, Dict[str, str]],
        shared_framing: Dict[str, str],
        shared_schemes: Dict[str, Dict[str, str]],
        active_team_scheme: Optional[Dict[str, str]] = None
    ) -> str:
        """Render a single character block by coordinating sub-renderers."""
        
        # 1. Resolve Outfits & Modifiers
        outfit_raw = data.outfits.get(config.outfit, "")
        modifier_text = ModifierRenderer.render(config, outfit_raw, shared_modifiers)
        
        # 2. Resolve Poses & Framing
        pose_raw = config.action_note or shared_poses.get(config.pose_category, {}).get(config.pose_preset, "")
        if isinstance(pose_raw, dict):
            pose_raw = pose_raw.get("description", "")
        
        framing_text = shared_framing.get(config.framing_mode, "")
        pose = PoseRenderer.render(pose_raw, framing_text)
        
        # 3. Resolve Color Schemes
        scheme = ColorSchemeRenderer.resolve(config, outfit_raw, shared_schemes, active_team_scheme)
        
        # 4. Substitution and Outfit Rendering
        sig_color = data.signature_color
        use_sig = config.use_signature_color
        
        rendered_outfit = OutfitRenderer.render(
            outfit_raw, 
            modifier_text=modifier_text, 
            scheme=scheme, 
            sig_color=sig_color, 
            use_sig=use_sig
        )
        
        # 5. Appearance
        appearance = CharacterRenderer._build_appearance_text(config, data)
        
        # 6. Final Assembly
        header = f"**CHARACTER {idx+1}: {data.name}**" if idx > 0 else f"**CHARACTER: {data.name}**"
        parts = [header]

        if appearance:
            clean_appearance = strip_html_comments(appearance)
            if clean_appearance:
                parts.append(f"**Appearance:**\n{clean_appearance}")

        if rendered_outfit:
            parts.append(f"**Outfit:**\n{rendered_outfit}")
        if pose:
            parts.append(f"**Pose/Action:**\n{pose}")
            
        parts.append("---")
        return "\n".join(parts)

    @staticmethod
    def _build_appearance_text(config: SelectedCharacterConfig, data: CharacterDetails) -> str:
        """Combine base appearance, traits, and tier-based descriptors."""
        appearance = data.appearance or ""
        
        # Character-level traits
        char_traits = config.character_traits or []
        trait_texts = [data.traits[ct] for ct in char_traits if ct in data.traits]
        
        if trait_texts:
            if appearance and not appearance.endswith((".", ";")):
                appearance += ";"
            appearance += " " + "; ".join(trait_texts)

        # Tier-based descriptors
        tier_info = []
        for field in ["age_presentation", "vibe", "bearing"]:
            val = getattr(data, field, None)
            if val:
                label = field.replace("_", " ").title()
                tier_info.append(f"{label}: {val}")
        
        if tier_info:
            if appearance and not appearance.endswith((".", ";")):
                appearance += "."
            appearance += " " + "; ".join(tier_info) + "."
            
        return appearance


class ModifierRenderer:
    """Resolves and combinations outfit modifiers."""

    @staticmethod
    def render(config: SelectedCharacterConfig, outfit_data: Any, shared_modifiers: Dict[str, str]) -> str:
        """Resolve and combine outfit traits/modifiers."""
        traits = config.outfit_traits or []
        if not traits and config.outfit_modifier:
            traits = [config.outfit_modifier]
        
        local_modifiers = {}
        if isinstance(outfit_data, dict) and "modifiers" in outfit_data:
            local_modifiers = outfit_data.get("modifiers", {})
        
        custom_modifiers = config.custom_modifiers or {}
        
        modifier_parts = []
        for t in traits:
            if t in local_modifiers:
                modifier_parts.append(local_modifiers[t])
            elif t in custom_modifiers:
                modifier_parts.append(custom_modifiers[t])
            elif t in shared_modifiers:
                modifier_parts.append(shared_modifiers[t])
        
        return "".join(modifier_parts).strip()


class ColorSchemeRenderer:
    """Resolves color schemes for outfits."""

    @staticmethod
    def resolve(
        config: SelectedCharacterConfig, 
        outfit_data: Any, 
        shared_schemes: Dict[str, Dict[str, str]],
        active_team_scheme: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """Auto-detect or resolve the color scheme."""
        scheme_name = config.color_scheme
        scheme = shared_schemes.get(
            scheme_name, shared_schemes.get("The Standard", {})
        )

        requires_team = False
        if isinstance(outfit_data, str):
            requires_team = "{team}" in outfit_data
        elif isinstance(outfit_data, dict):
            for v in outfit_data.values():
                if isinstance(v, str) and "{team}" in v:
                    requires_team = True
                    break
        
        if requires_team and (not scheme_name or scheme_name == "The Standard"):
            if active_team_scheme:
                scheme = active_team_scheme
            else:
                # Logic for picking team scheme usually belongs in the coordinator/builder
                # but we return standard as fallback here.
                pass
        
        return scheme if isinstance(scheme, dict) else {}
