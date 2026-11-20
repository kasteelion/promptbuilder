import random
from typing import Dict, Any, List
from utils.color_scheme import substitute_colors

class InteractionLogic:
    """Encapsulates business logic for scene and interaction generation."""
    
    def __init__(self, app_state):
        self.app_state = app_state
        # Lazily access color schemes from context when needed to avoid issues if data isn't loaded yet
        # self.color_schemes = parse_color_schemes("assets/data/lists/color_schemes.md")
        
    def resolve_interaction(self, text: str, characters: List[Any]) -> str:
        """Replace placeholders in interaction text with character names."""
        if not text:
            return ""
            
        resolved_text = text
        for i, char in enumerate(characters):
            # Replace {char1}, {char2}, etc.
            placeholder = f"{{char{i+1}}}"
            name = char.name if hasattr(char, "name") else char.get("name", "Unknown")
            resolved_text = resolved_text.replace(placeholder, name)
            
        return resolved_text
        
    def sync_poses_from_interaction(self, interaction_data: Dict[str, Any], characters: List[Any]) -> List[Any]:
        """
        Updates character action notes based on required poses defined in the interaction.
        Returns a list of updated character objects.
        """
        required_poses = interaction_data.get("required_poses", [])
        
        updated_chars = []
        for i, char in enumerate(characters):
            # If interaction has required poses, apply them
            if required_poses:
                # Use the pose for this index, or the last one if fewer poses than chars
                pose_val = required_poses[i] if i < len(required_poses) else required_poses[-1]
                
                # Check if we should actually update
                current_note = char.action_note if hasattr(char, "action_note") else char.get("action_note")
                if current_note != pose_val:
                    if hasattr(char, "action_note"):
                        char.action_note = pose_val
                    else:
                        char["action_note"] = pose_val
                    updated_chars.append(char)
            else:
                pass
                
        return updated_chars

    def process_scene_selection(self, category: str, preset: str) -> str:
        """Resolve scene text from category and preset."""
        scenes = self.app_state.ctx.scenes
        val = scenes.get(category, {}).get(preset, "")
        if isinstance(val, dict):
            return val.get("description", "")
        return str(val)

    def process_interaction_selection(self, category: str, preset: str) -> Dict[str, Any]:
        """Get interaction data object."""
        interactions = self.app_state.ctx.interactions
        data = interactions.get(category, {}).get(preset, {})
        
        # Normalize to dict if string
        if isinstance(data, str):
            data = {"description": data, "required_poses": []}
            
        return data

    def resolve_outfit(self, outfit_name: str, char_name: str) -> str:
        """Resolve outfit string, populating placeholders like {team} or {primary_color}."""
        characters = self.app_state.ctx.characters
        char_def = characters.get(char_name)
        if not char_def: return outfit_name
        
        outfits = char_def.outfits if hasattr(char_def, "outfits") else char_def.get("outfits", {})
        outfit_data = outfits.get(outfit_name, "")
        
        # Convert dict to string (simplified for now, ideally handle dict structure)
        if isinstance(outfit_data, dict):
            # If outfit data is a dict (components), we usually return the name or a combined string.
            # For now, let's assume we want to process the raw values if known, or just return name if dynamic.
            # But the user specifically asked for "color schemes file" which applies to the templates.
            # If the outfit *itself* is "{team} jersey", we need to know the string.
            # Assuming 'description' or similar exists, or if it's component based.
            # Wait, randomizer uses components. Roster usually just shows the NAME.
            # But if the user says "add back logic", they imply the prompt generation needs it.
            # So this method should return the *resolved description* or MUTATE the character state?
            
            # Use Randomizer-like logic: Check components for placeholders.
            parts = []
            for k, v in outfit_data.items():
                if isinstance(v, str):
                    parts.append(v)
            raw_text = " ".join(parts)
        else:
            raw_text = str(outfit_data)

        # Check for placeholders
        if "{team}" in raw_text or "{primary_color}" in raw_text:
            # Pick a random team
            schemes = self.app_state.ctx.color_schemes
            if schemes:
                team_name = random.choice(list(schemes.keys()))
                scheme = schemes[team_name]
                # Substitute
                resolved = substitute_colors(raw_text, scheme)
                # Color resolution logged at debug level if needed
                return resolved
                
        return raw_text
