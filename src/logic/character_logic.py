from typing import Dict, Any, List

class CharacterLogic:
    def __init__(self, ctx, state: Dict[str, Any]):
        self.ctx = ctx # AppContext
        self.state = state # AppState.state dict

    def toggle_character(self, name: str) -> bool:
        """Toggle character by name. Picks valid defaults based on character data.
        Returns True if added, False if removed.
        """
        existing_idx = next((i for i, c in enumerate(self.state["selected_characters"]) if c["name"] == name), -1)
        if existing_idx > -1:
            self.state["selected_characters"].pop(existing_idx)
            return False
        else:
            self._add_character_internal(name)
            return True

    def _add_character_internal(self, name: str):
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

    def update_character(self, index: int, updates: Dict[str, Any]):
        if 0 <= index < len(self.state["selected_characters"]):
            self.state["selected_characters"][index].update(updates)

    def move_character(self, index: int, direction: int):
        """Move character up or down in the list."""
        chars = self.state["selected_characters"]
        new_idx = index + direction
        if 0 <= new_idx < len(chars):
            chars[index], chars[new_idx] = chars[new_idx], chars[index]
            
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
