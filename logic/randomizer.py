"""Randomizer for generating random prompt configurations."""

import random


class PromptRandomizer:
    """Generates random character, outfit, and pose combinations."""
    
    def __init__(self, characters, base_prompts, poses, scenes=None, interactions=None):
        """Initialize randomizer with data.
        
        Args:
            characters: Character definitions dict
            base_prompts: Base style prompts dict
            poses: Pose presets dict
            scenes: Scene presets dict (category -> preset -> description)
            interactions: Interaction templates dict (category -> template -> description)
        """
        self.characters = characters
        self.base_prompts = base_prompts
        self.poses = poses
        self.scenes = scenes or {}
        self.interactions = interactions or {}
    
    def randomize(self, num_characters=None, include_scene=False, include_notes=False):
        """Generate random prompt configuration.
        
        Args:
            num_characters: Number of random characters to select (1-5), or None to randomize 1-3
            include_scene: Whether to generate a random scene description
            include_notes: Whether to generate random notes/interaction
            
        Returns:
            dict: Configuration dict with keys:
                - selected_characters: List of character dicts
                - base_prompt: Random base prompt name
                - scene: Random scene text (if include_scene=True)
                - notes: Random notes text (if include_notes=True)
        """
        # If no number specified or 0, randomize to 1-3 characters
        if num_characters is None or num_characters == 0:
            num_characters = random.randint(1, 3)
        else:
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
        
        # For pairs, 70% chance to use matching outfits
        use_matching_outfits = (num_to_select == 2 and random.random() < 0.7)
        matching_outfit = None
        
        if use_matching_outfits:
            # Find a common outfit across both characters
            matching_outfit = self._find_matching_outfit(selected_char_names)
        
        selected_characters = []
        for char_name in selected_char_names:
            char_data = self._randomize_character(char_name, forced_outfit=matching_outfit)
            selected_characters.append(char_data)
        
        config = {
            "selected_characters": selected_characters,
            "base_prompt": base_prompt,
            "scene": self._generate_random_scene() if include_scene else "",
            "notes": self._generate_random_notes(selected_characters) if include_notes else ""
        }
        
        return config
    
    def _randomize_character(self, char_name, forced_outfit=None):
        """Generate random outfit and pose for a character.
        
        Args:
            char_name: Name of character
            forced_outfit: Specific outfit name to use (for matching outfits)
            
        Returns:
            dict: Character data with random outfit and pose
        """
        char_def = self.characters.get(char_name, {})
        outfits = char_def.get("outfits", {})
        
        # Use forced outfit if provided and available, otherwise random
        if forced_outfit and forced_outfit in outfits:
            outfit_name = forced_outfit
        else:
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
    
    def _find_matching_outfit(self, char_names):
        """Find a common outfit name that exists for all characters.
        
        Args:
            char_names: List of character names
            
        Returns:
            str: Name of a matching outfit, or None if no common outfit found
        """
        if not char_names:
            return None
        
        # Get outfit sets for each character
        outfit_sets = []
        for char_name in char_names:
            char_def = self.characters.get(char_name, {})
            outfits = set(char_def.get("outfits", {}).keys())
            outfit_sets.append(outfits)
        
        # Find intersection of all outfit sets
        common_outfits = outfit_sets[0]
        for outfit_set in outfit_sets[1:]:
            common_outfits &= outfit_set
        
        # Return random outfit from common outfits, or None
        if common_outfits:
            return random.choice(list(common_outfits))
        return None
    
    def _generate_random_scene(self):
        """Generate a random scene description from scene presets.
        
        Returns:
            str: Random scene text
        """
        if not self.scenes:
            # Fallback if no scenes loaded
            scene_elements = [
                "A sunlit garden at golden hour",
                "A moody urban rooftop at dusk",
                "A cozy interior with warm lighting",
                "A dramatic outdoor landscape",
                "A minimalist studio setting"
            ]
            return random.choice(scene_elements)
        
        # Pick random category and preset
        category = random.choice(list(self.scenes.keys()))
        presets = self.scenes[category]
        if presets:
            preset_name = random.choice(list(presets.keys()))
            return presets[preset_name]
        return ""
    
    def _generate_random_notes(self, selected_characters):
        """Generate random interaction template filled with character names.
        
        Args:
            selected_characters: List of selected character dicts with 'name' key
            
        Returns:
            str: Random interaction text with character names filled in
        """
        if not self.interactions or not selected_characters:
            # Fallback if no interactions loaded
            notes_options = [
                "Emphasis on natural lighting and soft shadows",
                "High detail and sharp focus",
                "Dynamic composition and movement",
                "Focus on facial expression and emotion"
            ]
            return random.choice(notes_options)
        
        # Pick random category and template
        category = random.choice(list(self.interactions.keys()))
        templates = self.interactions[category]
        if templates:
            template_name = random.choice(list(templates.keys()))
            template = templates[template_name]
            
            # Fill template with character names
            char_names = [char['name'] for char in selected_characters]
            filled = template
            for i, name in enumerate(char_names, 1):
                filled = filled.replace(f"{{char{i}}}", name)
            
            return filled
        return ""
