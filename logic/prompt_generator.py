"""Prompt generation logic."""

import re


class PromptGenerator:
    """Generates formatted prompts from character and scene data."""
    
    def __init__(self, characters, base_prompts, poses):
        """Initialize with data dictionaries.
        
        Args:
            characters: Character definitions dict
            base_prompts: Base style prompts dict
            poses: Pose presets dict
        """
        self.characters = characters
        self.base_prompts = base_prompts
        self.poses = poses
    
    def generate(self, selected_characters, base_prompt_name, scene_text, notes_text, outfit_mode='detailed'):
        """Generate a formatted prompt from the given data.
        
        Args:
            selected_characters: List of character dicts with outfit/pose/action data
            base_prompt_name: Name of the base prompt to use
            scene_text: Scene/setting description
            notes_text: Additional notes
            
        Returns:
            str: Formatted prompt text
        """
        base = self.base_prompts.get(base_prompt_name, "")
        prompt_parts = []
        
        if base:
            prompt_parts.append(base)
        prompt_parts.append("---")

        scene = scene_text.strip()
        if scene:
            prompt_parts.append("**SCENE/SETTING:**")
            prompt_parts.append(scene)
            prompt_parts.append("---")

        for idx, c in enumerate(selected_characters):
            char_def = self.characters.get(c["name"], {})
            appearance = char_def.get("appearance", "")
            outfit_name = c.get("outfit", "")
            
            # Use Base outfit as default if none selected, otherwise first available
            if not outfit_name:
                outfits = char_def.get("outfits", {})
                if "Base" in outfits:
                    outfit_name = "Base"
                else:
                    available_outfits = list(outfits.keys())
                    outfit_name = available_outfits[0] if available_outfits else ""
            
            outfit_raw = char_def.get("outfits", {}).get(outfit_name, "")

            def format_outfit(outfit, mode='detailed'):
                """Format outfit dict or string into either detailed multi-line
                or compact single-line summary depending on `mode`.
                """
                if isinstance(outfit, dict):
                    # prefer these keys in order
                    ordered_keys = ["Top", "Bottom", "Footwear", "Accessories", "Hair/Makeup", "Hair", "Makeup"]
                    parts = []
                    for k in ordered_keys:
                        if k in outfit and outfit[k]:
                            parts.append(f"{outfit[k]}")
                    # include any extra keys
                    for k in outfit.keys():
                        if k not in ordered_keys and outfit[k]:
                            parts.append(f"{outfit[k]}")

                    if mode == 'detailed':
                        lines = []
                        # Use the key labels for detailed
                        for k in ordered_keys + [k for k in outfit.keys() if k not in ordered_keys]:
                            if k in outfit and outfit[k]:
                                lines.append(f"- {k}: {outfit[k]}")
                        return "\n".join(lines)
                    else:
                        # compact: join first few meaningful parts with semicolons
                        if parts:
                            return "; ".join(parts)
                        return ""
                else:
                    # outfit is a raw string; compact joins lines, detailed preserves paragraphs
                    if not outfit:
                        return ""
                    if mode == 'detailed':
                        return outfit
                    else:
                        return " ".join([ln.strip() for ln in str(outfit).splitlines() if ln.strip()])

            outfit_desc = format_outfit(outfit_raw, mode=('compact' if outfit_mode == 'compact' else 'detailed'))
            
            pose_cat = c.get("pose_category", "")
            pose_preset = c.get("pose_preset", "")
            action_note = c.get("action_note", "")
            
            pose_description = ""
            if action_note:
                pose_description = action_note
            elif pose_cat and pose_preset:
                pose_description = self.poses.get(pose_cat, {}).get(pose_preset, "")
            
            if len(selected_characters) > 1:
                prompt_parts.append(f"**CHARACTER {idx + 1}: {c['name']}**")
            else:
                prompt_parts.append(f"**CHARACTER: {c['name']}**")
                
            if appearance:
                prompt_parts.append("**Appearance:**")
                prompt_parts.append(appearance)
                
            if outfit_desc:
                prompt_parts.append("**Outfit:**")
                prompt_parts.append(outfit_desc)
            
            if pose_description:
                prompt_parts.append("**Pose/Action:**")
                prompt_parts.append(pose_description)
                
            prompt_parts.append("---")

        notes = notes_text.strip()
        if notes:
            prompt_parts.append("**Additional Notes:**")
            prompt_parts.append(notes)

        prompt = "\n\n".join([p for p in prompt_parts if p is not None and p != ""])
        prompt = re.sub(r"(\n\n---\n\n)+$", "", prompt).strip()
        return prompt
