"""Randomizer for generating random prompt configurations."""

import random


class PromptRandomizer:
    """Generates random character, outfit, and pose combinations."""
    
    def __init__(self, characters, base_prompts, poses):
        """Initialize randomizer with data.
        
        Args:
            characters: Character definitions dict
            base_prompts: Base style prompts dict
            poses: Pose presets dict
        """
        self.characters = characters
        self.base_prompts = base_prompts
        self.poses = poses
    
    def randomize(self, num_characters=1, include_scene=False, include_notes=False):
        """Generate random prompt configuration.
        
        Args:
            num_characters: Number of random characters to select (1-5)
            include_scene: Whether to generate a random scene description
            include_notes: Whether to generate random notes
            
        Returns:
            dict: Configuration dict with keys:
                - selected_characters: List of character dicts
                - base_prompt: Random base prompt name
                - scene: Random scene text (if include_scene=True)
                - notes: Random notes text (if include_notes=True)
        """
        num_characters = max(1, min(num_characters, 5))
        
        # Get random base prompt
        base_prompt = random.choice(list(self.base_prompts.keys())) if self.base_prompts else ""
        
        # Get random characters
        available_chars = list(self.characters.keys())
        if not available_chars:
            return {
                "selected_characters": [],
                "base_prompt": base_prompt,
                "scene": "",
                "notes": ""
            }
        
        # Sample without replacement if possible
        num_to_select = min(num_characters, len(available_chars))
        selected_char_names = random.sample(available_chars, num_to_select)
        
        selected_characters = []
        for char_name in selected_char_names:
            char_data = self._randomize_character(char_name)
            selected_characters.append(char_data)
        
        config = {
            "selected_characters": selected_characters,
            "base_prompt": base_prompt,
            "scene": self._generate_random_scene() if include_scene else "",
            "notes": self._generate_random_notes() if include_notes else ""
        }
        
        return config
    
    def _randomize_character(self, char_name):
        """Generate random outfit and pose for a character.
        
        Args:
            char_name: Name of character
            
        Returns:
            dict: Character data with random outfit and pose
        """
        char_def = self.characters.get(char_name, {})
        outfits = char_def.get("outfits", {})
        
        # Random outfit
        outfit_name = random.choice(list(outfits.keys())) if outfits else ""
        
        # Random pose (category + preset)
        pose_category = ""
        pose_preset = ""
        if self.poses:
            pose_category = random.choice(list(self.poses.keys()))
            pose_presets = self.poses.get(pose_category, {})
            if pose_presets:
                pose_preset = random.choice(list(pose_presets.keys()))
        
        return {
            "name": char_name,
            "outfit": outfit_name,
            "pose_category": pose_category,
            "pose_preset": pose_preset,
            "action_note": ""
        }
    
    def _generate_random_scene(self):
        """Generate a random scene description.
        
        Returns:
            str: Random scene text
        """
        scene_elements = [
            "A sunlit garden at golden hour",
            "A moody urban rooftop at dusk",
            "A cozy interior with warm lighting",
            "A dramatic outdoor landscape",
            "A minimalist studio setting",
            "A vintage-inspired setting",
            "A futuristic environment",
            "A natural woodland setting",
            "A luxurious interior space",
            "A gritty industrial setting"
        ]
        return random.choice(scene_elements)
    
    def _generate_random_notes(self):
        """Generate random additional notes.
        
        Returns:
            str: Random notes text
        """
        notes_options = [
            "Emphasis on natural lighting and soft shadows",
            "High detail and sharp focus",
            "Soft, dreamy aesthetic",
            "Dynamic composition and movement",
            "Intimate close-up perspective",
            "Wide-angle environmental shot",
            "Focus on facial expression and emotion",
            "Showcase full body and surroundings"
        ]
        return random.choice(notes_options)
