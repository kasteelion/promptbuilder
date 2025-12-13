from typing import Any, Dict, List

from .renderers import CharacterRenderer, NotesRenderer, OutfitRenderer, PoseRenderer, SceneRenderer
from utils.text_utils import normalize_blank_lines


class PromptBuilder:
    """Builds formatted prompts from character, scene, and style data."""

    def __init__(
        self,
        characters: Dict[str, Any],
        base_prompts: Dict[str, str],
        poses: Dict[str, Dict[str, str]],
    ):
        """Initialize the prompt builder.

        Args:
            characters: Dictionary of character data
            base_prompts: Dictionary of base art style prompts
            poses: Dictionary of pose categories and presets
        """
        self.characters = characters
        self.base_prompts = base_prompts
        self.poses = poses

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
