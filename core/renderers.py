class OutfitRenderer:
    @staticmethod
    def render(outfit: dict, mode="detailed"):
        if not outfit:
            return ""
        if isinstance(outfit, dict):
            keys = ["Top", "Bottom", "Footwear", "Accessories", "Hair", "Makeup"]
            present = [f"- {k}: {outfit[k]}" for k in keys if outfit.get(k)]
            extras = [f"- {k}: {v}" for k, v in outfit.items() if k not in keys]
            lines = present + extras
            return "\n".join(lines) if mode == "detailed" else "; ".join([l.split(": ")[1] for l in lines])
        return outfit

class PoseRenderer:
    @staticmethod
    def render(pose_description: str):
        return pose_description or ""

class SceneRenderer:
    @staticmethod
    def render(scene: str):
        if not scene.strip():
            return ""
        return f"**SCENE/SETTING:**\n{scene}\n---"

class NotesRenderer:
    @staticmethod
    def render(notes: str):
        return f"**Additional Notes:**\n{notes}" if notes.strip() else ""

class CharacterRenderer:
    @staticmethod
    def render(idx, character_name, appearance, outfit, pose):
        header = f"**CHARACTER {idx+1}: {character_name}**" if idx > 0 else f"**CHARACTER: {character_name}**"
        parts = [header]
        if appearance:
            parts.append(f"**Appearance:**\n{appearance}")
        if outfit:
            parts.append(f"**Outfit:**\n{outfit}")
        if pose:
            parts.append(f"**Pose/Action:**\n{pose}")
        parts.append("---")
        return "\n".join(parts)
