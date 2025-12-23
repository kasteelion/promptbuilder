"""Randomizer for generating random prompt configurations."""

import random

from utils.interaction_helpers import fill_template


class PromptRandomizer:
    """Generates random character, outfit, and pose combinations."""

    def __init__(self, characters, base_prompts, poses, scenes=None, interactions=None, color_schemes=None, modifiers=None):
        """Initialize randomizer with data.

        Args:
            characters: Character definitions dict
            base_prompts: Base style prompts dict
            poses: Pose presets dict
            scenes: Scene presets dict (category -> preset -> description)
            interactions: Interaction templates dict (category -> template -> description)
            color_schemes: Color schemes dict
            modifiers: Outfit modifiers dict
        """
        self.characters = characters
        self.base_prompts = base_prompts
        self.poses = poses
        self.scenes = scenes or {}
        self.interactions = interactions or {}
        self.color_schemes = color_schemes or {}
        self.modifiers = modifiers or {}

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
                - color_scheme: Random color scheme name
        """
        # Step 0: Resolve conflicts between Interactions and Poses
        # If both are requested/available, we want to avoid cluttering both.
        # Modes:
        # - Interaction Dominant (40%): Notes/Interaction active, Poses disabled
        # - Pose Dominant (40%): Poses active, Interaction disabled (Notes empty)
        # - Mixed (20%): Both active
        
        generate_interaction = include_notes
        generate_poses = True
        
        if include_notes and self.interactions and self.poses:
            roll = random.random()
            if roll < 0.4:
                # Interaction Dominant
                generate_poses = False
            elif roll < 0.8:
                # Pose Dominant
                generate_interaction = False
            # else: Mixed (keep both True)

        # Step 1: Select Interaction first (if requested) to determine min characters
        selected_interaction_template = None
        min_chars_needed = 1
        
        if generate_interaction and self.interactions:
            # Flatten interactions to list of (template_str, min_chars)
            all_templates = []
            for category, templates in self.interactions.items():
                for name, data in templates.items():
                    if isinstance(data, dict):
                        all_templates.append((data.get("description", ""), data.get("min_chars", 1)))
                    else:
                        all_templates.append((data, 1))
            
            if all_templates:
                selected_interaction_template, min_chars_needed = random.choice(all_templates)

        # Step 2: Determine number of characters
        if num_characters is None or num_characters == 0:
            # Randomize 1-3, but at least min_chars_needed
            # If min_chars_needed > 3, we must respect it (up to 5)
            lower_bound = max(1, min_chars_needed)
            upper_bound = max(3, lower_bound)
            # Cap at 5 total
            upper_bound = min(5, upper_bound)
            lower_bound = min(5, lower_bound)
            
            num_characters = random.randint(lower_bound, upper_bound)
        else:
            # User specified a number. We should respect it, but if it's less than needed for the interaction,
            # we might have a problem. The user's explicit choice should probably override,
            # but getting a broken interaction is bad. 
            # Strategy: If user asks for 2 chars but interaction needs 3, bump it to 3.
            num_characters = max(num_characters, min_chars_needed)
            num_characters = max(1, min(num_characters, 5))

        # Get random base prompt
        base_prompt = random.choice(list(self.base_prompts.keys())) if self.base_prompts else ""
        
        # Get random color scheme
        color_scheme = "Default (No Scheme)"
        if self.color_schemes:
            # Filter out "Default" to make randomization more interesting, or keep it?
            # Let's keep it as a valid option but maybe weighted less? Simple random choice for now.
            color_scheme = random.choice(list(self.color_schemes.keys()))

        # Get random characters
        available_chars = list(self.characters.keys())
        if not available_chars:
            return {
                "selected_characters": [], 
                "base_prompt": base_prompt, 
                "scene": "", 
                "notes": "",
                "color_scheme": color_scheme
            }

        # Sample without replacement if possible
        num_to_select = min(num_characters, len(available_chars))
        selected_char_names = random.sample(available_chars, num_to_select)

        # For pairs, 70% chance to use matching outfits
        use_matching_outfits = num_to_select >= 2 and random.random() < 0.7
        matching_outfit = None

        if use_matching_outfits:
            # Find a common outfit across both characters
            matching_outfit = self._find_matching_outfit(selected_char_names)

        selected_characters = []
        for char_name in selected_char_names:
            char_data = self._randomize_character(
                char_name, 
                forced_outfit=matching_outfit, 
                include_pose=generate_poses
            )
            # Apply color scheme to character data so UI can pick it up
            char_data["color_scheme"] = color_scheme
            selected_characters.append(char_data)

        # Generate notes string from the pre-selected template
        notes_text = ""
        if selected_interaction_template:
            char_names = [char["name"] for char in selected_characters]
            notes_text = fill_template(selected_interaction_template, char_names)
        elif generate_interaction:
             # Fallback if no interactions loaded or something went wrong
            notes_text = self._generate_random_notes(selected_characters)

        config = {
            "selected_characters": selected_characters,
            "base_prompt": base_prompt,
            "scene": self._generate_random_scene() if include_scene else "",
            "notes": notes_text,
            "color_scheme": color_scheme
        }

        return config

    def _randomize_character(self, char_name, forced_outfit=None, include_pose=True):
        """Generate random outfit and pose for a character.

        Args:
            char_name: Name of character
            forced_outfit: Specific outfit name to use (for matching outfits)
            include_pose: Whether to generate a random pose

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

        # Random outfit modifier if applicable
        outfit_modifier = ""
        outfit_desc = str(outfits.get(outfit_name, ""))
        if "{modifier}" in outfit_desc and self.modifiers:
            # 50% chance to apply a modifier if the outfit supports it
            if random.random() < 0.5:
                outfit_modifier = random.choice(list(self.modifiers.keys()))

        # Random pose (category + preset)
        pose_category = ""
        pose_preset = ""
        
        if include_pose and self.poses:
            pose_category = random.choice(list(self.poses.keys()))
            pose_presets = self.poses.get(pose_category, {})
            if pose_presets:
                pose_preset = random.choice(list(pose_presets.keys()))

        return {
            "name": char_name,
            "outfit": outfit_name,
            "outfit_modifier": outfit_modifier,
            "pose_category": pose_category,
            "pose_preset": pose_preset,
            "action_note": "",
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
                "A minimalist studio setting",
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
                "Focus on facial expression and emotion",
            ]
            return random.choice(notes_options)

        num_chars = len(selected_characters)
        
        # Collect all eligible templates across all categories
        eligible_templates = []
        
        for category, templates in self.interactions.items():
            for name, data in templates.items():
                # Handle both new structured format and legacy string format
                if isinstance(data, dict):
                    desc = data.get("description", "")
                    min_chars = data.get("min_chars", 1)
                else:
                    desc = data
                    min_chars = 1
                    
                # Check if we have enough characters
                if num_chars >= min_chars:
                    eligible_templates.append(desc)

        if eligible_templates:
            template = random.choice(eligible_templates)

            # Fill template with character names
            char_names = [char["name"] for char in selected_characters]
            return fill_template(template, char_names)
            
        return ""
