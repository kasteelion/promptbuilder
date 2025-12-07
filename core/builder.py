from .renderers import OutfitRenderer, PoseRenderer, SceneRenderer, NotesRenderer, CharacterRenderer

class PromptBuilder:
    def __init__(self, characters, base_prompts, poses):
        self.characters = characters
        self.base_prompts = base_prompts
        self.poses = poses

    def generate(self, config):
        parts = []

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
            pose = char.get("action_note") or self.poses.get(char.get("pose_category"), {}).get(char.get("pose_preset"), "")
            parts.append(CharacterRenderer.render(idx, char["name"], data.get("appearance", ""), OutfitRenderer.render(outfit), PoseRenderer.render(pose)))

        notes = config.get("notes", "")
        if notes:
            parts.append(NotesRenderer.render(notes))

        return "\n\n".join([p for p in parts if p]).strip()
