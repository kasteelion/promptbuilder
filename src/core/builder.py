import re
import random
from typing import Any, Dict, List, Union


from utils.text_utils import normalize_blank_lines

from .renderers import (
    CharacterRenderer,
    ColorSchemeRenderer,
    ModifierRenderer,
    NotesRenderer,
    OutfitRenderer,
    PoseRenderer,
    SceneRenderer,
    strip_html_comments,
)
from .models import PromptConfig, CharacterDetails, SelectedCharacterConfig

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
        global_outfits: Dict[str, Any] = None,
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
        self.global_outfits = global_outfits or {}
        self._active_team_scheme = None

    def generate(self, config: Union[Dict[str, Any], PromptConfig], format_type: str = "markdown") -> str:
        """Generate a formatted prompt from configuration.

        Args:
            config: Configuration (dictionary or PromptConfig model).
            format_type: 'markdown' for structured format, 'prose' for Nanobanana cinematic prose.

        Returns:
            Formatted prompt string
        """
        # Ensure config is a PromptConfig model
        if isinstance(config, dict):
            config = PromptConfig(**config)

        if format_type == "prose":
            return self.generate_prose(config)
        elif format_type == "midjourney":
            return self.generate_midjourney(config)
        elif format_type == "sdxl":
            return self.generate_sdxl(config)

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
                self._active_team_scheme,
                self.global_outfits # Pass for fallbacks
            ))

        # 4. Notes
        if config.notes:
            parts.append(NotesRenderer.render(config.notes, char_names))

        out = "\n\n".join([p for p in parts if p])
        return normalize_blank_lines(out)

    def generate_prose(self, config: Union[Dict[str, Any], PromptConfig]) -> str:
        """Generate a continuous, rich cinematic prose prompt optimized for Nanobanana / Google AI Studio.

        Translates structured characters, outfits, poses, lighting, and scene details into
        uninterrupted, highly descriptive prose without technical markdown punctuation.
        """
        if isinstance(config, dict):
            config = PromptConfig(**config)

        prose_paragraphs: List[str] = []

        # 1. Visual Medium & Art Style Foundation
        base_data = self.base_prompts.get(config.base_prompt, "")
        base_desc = base_data.get("description", "") if isinstance(base_data, dict) else str(base_data)

        # 2. Scene Setting & Atmosphere
        scene_raw = config.scene.strip()

        opening_sentences = []
        if base_desc:
            clean_base = base_desc.strip().rstrip(".")
            opening_sentences.append(f"{clean_base}.")

        if scene_raw:
            clean_scene = scene_raw.replace("\n", " ").strip()
            clean_scene = re.sub(r"^\*\*SCENE/SETTING:\*\*\s*", "", clean_scene, flags=re.IGNORECASE)
            clean_scene = re.sub(r"^\*\*.*?\*\*\s*", "", clean_scene)
            if not clean_scene.endswith("."):
                clean_scene += "."
            opening_sentences.append(f"Set in {clean_scene[0].lower() + clean_scene[1:] if clean_scene else clean_scene}")

        if opening_sentences:
            prose_paragraphs.append(" ".join(opening_sentences))

        # 3. Characters & Attire & Contrast
        self._active_team_scheme = None
        self._resolve_active_team_scheme(config)
        char_paragraphs = []

        for idx, char_config in enumerate(config.selected_characters):
            char_data = self.characters.get(char_config.name)
            if not char_data:
                continue
            if isinstance(char_data, dict):
                char_data = CharacterDetails(**char_data)

            # Resolve Outfit
            outfit_name = char_config.outfit
            variant_name = "base"
            if outfit_name and " - " in outfit_name:
                outfit_name, variant_name = outfit_name.split(" - ", 1)

            outfit_raw = char_data.outfits.get(outfit_name)
            if not outfit_raw and outfit_name:
                fuzzy_name = CharacterRenderer._fuzzy_match_outfit(outfit_name, char_data.outfits.keys())
                if fuzzy_name:
                    outfit_raw = char_data.outfits.get(fuzzy_name)
            if not outfit_raw:
                outfit_raw = ""

            if isinstance(outfit_raw, dict) and "variants" in outfit_raw:
                variants = outfit_raw.get("variants", {})
                outfit_raw = variants.get(variant_name, variants.get("base", outfit_raw))

            modifier_text = ModifierRenderer.render(char_config, outfit_raw, self.modifiers)
            scheme = ColorSchemeRenderer.resolve(char_config, outfit_raw, self.color_schemes, self._active_team_scheme)

            rendered_outfit = OutfitRenderer.render(
                outfit_raw,
                mode="compact",
                modifier_text=modifier_text,
                scheme=scheme,
                sig_color=char_data.signature_color,
                use_sig=char_config.use_signature_color,
            )

            # Appearance
            appearance = CharacterRenderer._build_appearance_text(char_config, char_data)
            appearance = strip_html_comments(appearance).strip().rstrip(".")

            # Pose & Framing
            pose_raw = char_config.action_note or self.poses.get(char_config.pose_category, {}).get(char_config.pose_preset, "")
            if isinstance(pose_raw, dict):
                pose_raw = pose_raw.get("description", "")
            framing_text = self.framing.get(char_config.framing_mode, "")
            pose = PoseRenderer.render(pose_raw, framing_text).strip()

            # Construct prose description for character
            sentences = []
            prefix = f"{char_data.name}" if idx == 0 else f"Alongside, {char_data.name}"

            if appearance:
                clean_app = appearance.lower() if not appearance.startswith(("A ", "An ")) else appearance
                sentences.append(f"{prefix}, a {clean_app}.")
            else:
                sentences.append(f"{prefix} is present in the scene.")

            if pose:
                pose_clean = pose.rstrip(".")
                sentences.append(f"{char_data.name} is {pose_clean[0].lower() + pose_clean[1:] if pose_clean else ''}.")

            if rendered_outfit:
                clean_outfit = rendered_outfit.replace("\n", ", ").strip().rstrip(".")
                sentences.append(f"{char_data.name} is dressed in {clean_outfit}.")

            if char_config.color_scheme and char_config.color_scheme not in ("Default (No Scheme)", "The Standard"):
                sentences.append(f"The wardrobe features a coordinated {char_config.color_scheme} palette.")

            if char_config.use_signature_color and char_data.signature_color:
                sentences.append(f"Accented with a signature {char_data.signature_color} flourish.")

            char_paragraphs.append(" ".join(sentences))

        if char_paragraphs:
            prose_paragraphs.append("\n\n".join(char_paragraphs))

        # 4. Narrative Dynamics & Notes
        if config.notes:
            notes_clean = config.notes.strip()
            char_names = [c.name for c in config.selected_characters]
            for i, name in enumerate(char_names):
                notes_clean = notes_clean.replace(f"{{char{i+1}}}", name)
            notes_clean = re.sub(r"^\*\*.*?\*\*\s*", "", notes_clean)
            if notes_clean:
                prose_paragraphs.append(f"Scene Dynamics & Interaction: {notes_clean}")

        out = "\n\n".join([p for p in prose_paragraphs if p])
        return normalize_blank_lines(out)

    def _resolve_rendered_outfit(
        self,
        char_config: SelectedCharacterConfig,
        char_data: CharacterDetails,
        mode: str = "compact"
    ) -> str:
        """Resolve and render the outfit string for a character."""
        outfit_name = char_config.outfit
        variant_name = "base"
        if outfit_name and " - " in outfit_name:
            outfit_name, variant_name = outfit_name.split(" - ", 1)

        outfit_raw = char_data.outfits.get(outfit_name)
        if not outfit_raw and outfit_name:
            fuzzy_name = CharacterRenderer._fuzzy_match_outfit(outfit_name, char_data.outfits.keys())
            if fuzzy_name:
                outfit_raw = char_data.outfits.get(fuzzy_name)

        if not outfit_raw and self.global_outfits and outfit_name:
            gender = char_data.gender or "F"
            gender_outfits = self.global_outfits.get(gender, {})
            for cat_outfits in gender_outfits.values():
                if outfit_name in cat_outfits:
                    outfit_raw = cat_outfits[outfit_name]
                    break
                fuzzy_name = CharacterRenderer._fuzzy_match_outfit(outfit_name, cat_outfits.keys())
                if fuzzy_name:
                    outfit_raw = cat_outfits[fuzzy_name]
                    break

        if not outfit_raw:
            outfit_raw = ""

        if isinstance(outfit_raw, dict) and "variants" in outfit_raw:
            variants = outfit_raw.get("variants", {})
            outfit_raw = variants.get(variant_name, variants.get("base", outfit_raw))

        modifier_text = ModifierRenderer.render(char_config, outfit_raw, self.modifiers)
        scheme = ColorSchemeRenderer.resolve(char_config, outfit_raw, self.color_schemes, self._active_team_scheme)

        return OutfitRenderer.render(
            outfit_raw,
            mode=mode,
            modifier_text=modifier_text,
            scheme=scheme,
            sig_color=char_data.signature_color,
            use_sig=char_config.use_signature_color,
        )

    def _resolve_pose(self, char_config: SelectedCharacterConfig) -> str:
        """Resolve and render pose and framing for a character."""
        pose_raw = char_config.action_note or self.poses.get(char_config.pose_category, {}).get(char_config.pose_preset, "")
        if isinstance(pose_raw, dict):
            pose_raw = pose_raw.get("description", "")
        framing_text = self.framing.get(char_config.framing_mode, "")
        return PoseRenderer.render(pose_raw, framing_text).strip()

    def generate_midjourney(self, config: Union[Dict[str, Any], PromptConfig]) -> str:
        """Generate a Midjourney v6-optimized prompt (comma-separated tokens, parameters appended)."""
        if isinstance(config, dict):
            config = PromptConfig(**config)

        self._active_team_scheme = None
        self._resolve_active_team_scheme(config)

        elements: List[str] = []

        # 1. Art Style Foundation
        base_data = self.base_prompts.get(config.base_prompt, "")
        base_desc = base_data.get("description", "") if isinstance(base_data, dict) else str(base_data)
        if base_desc:
            clean_base = re.sub(r"[\r\n]+", ", ", base_desc).strip(" .,;")
            elements.append(clean_base)

        # 2. Scene / Setting
        if config.scene:
            clean_scene = re.sub(r"^\*\*SCENE/SETTING:\*\*\s*", "", config.scene, flags=re.IGNORECASE)
            clean_scene = re.sub(r"^\*\*.*?\*\*\s*", "", clean_scene)
            clean_scene = re.sub(r"[\r\n]+", ", ", clean_scene).strip(" .,;")
            if clean_scene:
                elements.append(clean_scene)

        # 3. Characters
        for char_config in config.selected_characters:
            char_data = self.characters.get(char_config.name)
            if not char_data:
                continue
            if isinstance(char_data, dict):
                char_data = CharacterDetails(**char_data)

            char_tokens = []
            appearance = CharacterRenderer._build_appearance_text(char_config, char_data)
            appearance = strip_html_comments(appearance).strip()
            if appearance:
                clean_app = re.sub(r"[\r\n;]+", ", ", appearance).strip(" .,;")
                char_tokens.append(f"{char_data.name}, {clean_app}")
            else:
                char_tokens.append(char_data.name)

            rendered_outfit = self._resolve_rendered_outfit(char_config, char_data)
            if rendered_outfit:
                clean_outfit = re.sub(r"[\r\n;]+", ", ", rendered_outfit).strip(" .,;")
                char_tokens.append(f"wearing {clean_outfit}")

            pose = self._resolve_pose(char_config)
            if pose:
                clean_pose = re.sub(r"[\r\n;]+", ", ", pose).strip(" .,;")
                char_tokens.append(clean_pose)

            if char_tokens:
                elements.append(", ".join(char_tokens))

        # 4. Notes / Interactions
        if config.notes:
            notes_clean = config.notes.strip()
            char_names = [c.name for c in config.selected_characters]
            for i, name in enumerate(char_names):
                notes_clean = notes_clean.replace(f"{{char{i+1}}}", name)
            notes_clean = re.sub(r"^\*\*.*?\*\*\s*", "", notes_clean)
            notes_clean = re.sub(r"[\r\n]+", ", ", notes_clean).strip(" .,;")
            if notes_clean:
                elements.append(notes_clean)

        raw_prompt = ", ".join(e for e in elements if e)
        clean_prompt = re.sub(r"[*#_~`]", "", raw_prompt)
        clean_prompt = re.sub(r"\s*,\s*", ", ", clean_prompt)
        clean_prompt = re.sub(r",(\s*,)+", ",", clean_prompt).strip(" ,")

        return f"{clean_prompt} --ar 16:9 --v 6.1 --stylize 250"

    def generate_sdxl(self, config: Union[Dict[str, Any], PromptConfig]) -> str:
        """Generate SDXL / ComfyUI weighted tag prompt with positive and negative sections."""
        if isinstance(config, dict):
            config = PromptConfig(**config)

        self._active_team_scheme = None
        self._resolve_active_team_scheme(config)

        pos_parts: List[str] = []

        # 1. Base Prompt / Art Style Weighting
        base_data = self.base_prompts.get(config.base_prompt, "")
        base_desc = base_data.get("description", "") if isinstance(base_data, dict) else str(base_data)
        base_lower = (config.base_prompt + " " + base_desc).lower()

        if base_desc:
            clean_base = re.sub(r"[*#_~`]", "", base_desc)
            clean_base = re.sub(r"[\r\n]+", ", ", clean_base).strip(" .,;")
            pos_parts.append(f"({clean_base}:1.15)")

        # 2. Characters
        for char_config in config.selected_characters:
            char_data = self.characters.get(char_config.name)
            if not char_data:
                continue
            if isinstance(char_data, dict):
                char_data = CharacterDetails(**char_data)

            appearance = CharacterRenderer._build_appearance_text(char_config, char_data)
            appearance = strip_html_comments(appearance).strip()
            clean_app = re.sub(r"[*#_~`]", "", appearance)
            clean_app = re.sub(r"[\r\n;]+", ", ", clean_app).strip(" .,;")

            rendered_outfit = self._resolve_rendered_outfit(char_config, char_data)
            clean_outfit = re.sub(r"[*#_~`]", "", rendered_outfit) if rendered_outfit else ""
            clean_outfit = re.sub(r"[\r\n;]+", ", ", clean_outfit).strip(" .,;")

            pose = self._resolve_pose(char_config)
            clean_pose = re.sub(r"[*#_~`]", "", pose) if pose else ""
            clean_pose = re.sub(r"[\r\n;]+", ", ", clean_pose).strip(" .,;")

            char_chunk = []
            if clean_app:
                char_chunk.append(f"({char_data.name}, {clean_app}:1.1)")
            else:
                char_chunk.append(f"({char_data.name}:1.1)")
            if clean_outfit:
                char_chunk.append(f"({clean_outfit}:1.0)")
            if clean_pose:
                char_chunk.append(f"({clean_pose}:0.95)")

            pos_parts.append(", ".join(char_chunk))

        # 3. Scene Setting
        if config.scene:
            clean_scene = re.sub(r"^\*\*SCENE/SETTING:\*\*\s*", "", config.scene, flags=re.IGNORECASE)
            clean_scene = re.sub(r"^\*\*.*?\*\*\s*", "", clean_scene)
            clean_scene = re.sub(r"[*#_~`]", "", clean_scene)
            clean_scene = re.sub(r"[\r\n]+", ", ", clean_scene).strip(" .,;")
            if clean_scene:
                pos_parts.append(f"({clean_scene}:1.0)")

        # 4. Notes / Dynamic interaction
        if config.notes:
            notes_clean = config.notes.strip()
            char_names = [c.name for c in config.selected_characters]
            for i, name in enumerate(char_names):
                notes_clean = notes_clean.replace(f"{{char{i+1}}}", name)
            notes_clean = re.sub(r"^\*\*.*?\*\*\s*", "", notes_clean)
            notes_clean = re.sub(r"[*#_~`]", "", notes_clean)
            notes_clean = re.sub(r"[\r\n]+", ", ", notes_clean).strip(" .,;")
            if notes_clean:
                pos_parts.append(f"({notes_clean}:0.9)")

        positive_prompt = ",\nBREAK\n".join(pos_parts)

        # 5. Determine auto-derived negative prompt based on base style
        neg_tokens = ["bad anatomy", "blurry", "low quality", "deformed hands", "extra digits", "missing fingers", "watermark", "signature", "cropped", "jpeg artifacts"]
        if any(w in base_lower for w in ("photo", "cinematic", "realistic", "hyperrealistic", "raw", "dslr", "35mm")):
            neg_tokens = ["illustration", "3d render", "cartoon", "anime", "painting", "drawing"] + neg_tokens
        elif any(w in base_lower for w in ("anime", "manga", "cel", "illustration", "vector", "comic")):
            neg_tokens = ["photorealistic", "photograph", "hyperrealistic", "3d render", "film grain", "lens flare"] + neg_tokens
        else:
            neg_tokens = ["worst quality", "low quality", "illustration", "3d render"] + neg_tokens

        negative_prompt = ", ".join(neg_tokens)

        return f"{positive_prompt}\n\nNEGATIVE:\n{negative_prompt}"

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
            
            # Add scene tags if available
            scene_tags = ""
            # TODO: Add scene tags to PromptConfig metadata so we can show them here without ctx
            
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
                
                char_def = self.characters.get(name)
                if char_def:
                    # Add Outfit Tags for clarity
                    if isinstance(char_def, CharacterDetails):
                        outfit_data = char_def.outfits.get(outfit, {})
                        if isinstance(outfit_data, dict):
                            o_tags = outfit_data.get("tags", [])
                            if o_tags:
                                parts[0] = f"{outfit} [{', '.join(o_tags[:2])}]"

                    outfit_data = char_def.outfits.get(outfit, "")
                    outfit_str = str(outfit_data) if not isinstance(outfit_data, dict) else " ".join(str(v) for v in outfit_data.values() if isinstance(v, str))
                    
                    supports_schemes = any(f"{{{k}}}" in outfit_str for k in ("primary_color", "secondary_color", "accent"))
                    supports_sig = "{signature_color}" in outfit_str or "(signature)" in outfit_str
                    
                    if char_config.color_scheme and char_config.color_scheme not in ("Default (No Scheme)", "The Standard") and supports_schemes:
                        parts.append(char_config.color_scheme)
                    
                    if char_config.use_signature_color and supports_sig:
                        if char_def.signature_color:
                            parts.append("✨")

                parts.append(pose)
                char_summaries.append(f"   👤 **{name}**: {' • '.join(parts)}")
            
            summary_parts.append("👥 **Characters**:")
            summary_parts.extend(char_summaries)
            
        # 5. Interaction/Notes
        notes = config.notes.strip()
        if notes:
            is_interaction = "(" in notes and ")" in notes and ":" in notes
            icon = "🤝" if is_interaction else "📝"
            label = "Interaction" if is_interaction else "Action"
            
            # Use the full notes for the auditor, or at least a much larger window
            summary_parts.append(f"{icon} **{label}**: {notes}")
            
        return "\n".join(summary_parts) if summary_parts else "No characters or scene selected."
