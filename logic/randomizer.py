"""Randomizer for generating random prompt configurations."""

import random

from utils.interaction_helpers import fill_template

class PromptRandomizer:
    """Generates random character, outfit, and pose combinations."""

    def __init__(self, characters, base_prompts, poses, scenes=None, interactions=None, color_schemes=None, modifiers=None, framing=None):
        """Initialize randomizer with data.

        Args:
            characters: Character definitions dict
            base_prompts: Base style prompts dict
            poses: Pose presets dict
            scenes: Scene presets dict (category -> preset -> {description, tags})
            interactions: Interaction templates dict (category -> template -> description)
            color_schemes: Color schemes dict
            modifiers: Outfit modifiers dict
            framing: Framing modifiers dict
        """
        self.characters = characters
        self.base_prompts = base_prompts
        self.poses = poses
        self.scenes = scenes or {}
        self.interactions = interactions or {}
        self.color_schemes = color_schemes or {}
        self.modifiers = modifiers or {}
        self.framing = framing or {}

    def _get_description(self, item_data):
        """Helper to safely extract description from string or new dict format."""
        if isinstance(item_data, dict):
            return item_data.get("description", "")
        return str(item_data)

    def _get_tags(self, item_data):
        """Helper to extract tags from new dict format."""
        if isinstance(item_data, dict):
            return item_data.get("tags", [])
        return []

    def _filter_items_by_tags(self, items_dict, target_tags, threshold=1):
        """Filter a dictionary of items (name -> data) by matching tags.
        
        Args:
            items_dict: Dictionary of items (e.g., poses in a category)
            target_tags: List/Set of tags to match against
            threshold: Min number of tag matches required (default 1)
            
        Returns:
            list: List of item names that match
        """
        matching_names = []
        target_tags_lower = {t.lower() for t in target_tags}
        
        for name, data in items_dict.items():
            item_tags = self._get_tags(data)
            # Also check if the item name itself counts as a tag? Maybe.
            
            match_count = 0
            for t in item_tags:
                if t.lower() in target_tags_lower:
                    match_count += 1
            
            if match_count >= threshold:
                matching_names.append(name)
                
        return matching_names

    def randomize(self, num_characters=None, include_scene=False, include_notes=False, forced_base_prompt=None):
        """Generate random prompt configuration.

        Args:
            num_characters: Number of random characters to select (1-5), or None to randomize 1-3
            include_scene: Whether to generate a random scene description
            include_notes: Whether to generate random notes/interaction
            forced_base_prompt: Optional name of base prompt to force use

        Returns:
            dict: Configuration dict with keys:
                - selected_characters: List of character dicts
                - base_prompt: Random base prompt name
                - scene: Random scene text (if include_scene=True)
                - notes: Random notes text (if include_notes=True)
                - color_scheme: Random color scheme name
        """
        # Step 0: Resolve conflicts between Interactions and Poses
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

        # Step 1: Select Interaction first (if requested)
        selected_interaction_template = None
        min_chars_needed = 1
        
        if generate_interaction and self.interactions:
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
            lower_bound = max(1, min_chars_needed)
            upper_bound = max(3, lower_bound)
            upper_bound = min(5, upper_bound)
            lower_bound = min(5, lower_bound)
            num_characters = random.randint(lower_bound, upper_bound)
        else:
            num_characters = max(num_characters, min_chars_needed)
            num_characters = max(1, min(num_characters, 5))

        # Get random base prompt
        # Get random base prompt (fallback/initial)
        base_prompt = ""
        if forced_base_prompt and self.base_prompts and forced_base_prompt in self.base_prompts:
            base_prompt = forced_base_prompt
        elif self.base_prompts:
             base_prompt = random.choice(list(self.base_prompts.keys()))
        
        # Get random characters
        available_chars = list(self.characters.keys())
        if not available_chars:
            return {
                "selected_characters": [], 
                "base_prompt": base_prompt, 
                "scene": "", 
                "notes": "",
                "color_scheme": "Default (No Scheme)"
            }

        num_to_select = min(num_characters, len(available_chars))
        selected_char_names = random.sample(available_chars, num_to_select)

        # -- SMART LOGIC START --
        # Collect tags from selected characters to drive theme
        combined_tags = set()
        for name in selected_char_names:
            char_def = self.characters.get(name, {})
            tags = char_def.get("tags", [])
            for t in tags:
                combined_tags.add(t.lower())

        # Select Scene (Smart)
        scene_text = ""
        scene_category = ""
        if include_scene:
            scene_category, scene_text = self._select_smart_scene(combined_tags)

        # Smart Color Scheme Selection
        color_scheme = "Default (No Scheme)"
        if self.color_schemes and random.random() > 0.3:
            color_scheme = self._select_smart_color_scheme(combined_tags, scene_category)

        # Smart Framing Selection
        prompt_framing = ""
        if self.framing and random.random() < 0.25:
            prompt_framing = self._select_smart_framing(num_to_select)

        # Smart Base Prompt Selection (Override)
        if self.base_prompts and not forced_base_prompt:
             base_prompt = self._select_smart_base_prompt(self.base_prompts, combined_tags, scene_category)

        # Extract tags from the selected base prompt to influence Pose/Outfit
        base_prompt_tags = set()
        if base_prompt and base_prompt in self.base_prompts:
            bp_data = self.base_prompts[base_prompt]
            if isinstance(bp_data, dict):
                tags = bp_data.get("tags", [])
                for t in tags:
                    base_prompt_tags.add(t.lower())
        
        # Add base prompt tags to the context for character randomization
        # We don't modify combined_tags directly to keep debugging clean, 
        # but we pass a union to the character randomizer
        character_context_tags = combined_tags.union(base_prompt_tags)

        # -- SMART LOGIC END --

        # For pairs, 70% chance to use matching outfits
        use_matching_outfits = num_to_select >= 2 and random.random() < 0.7
        matching_outfit = None

        if use_matching_outfits:
            matching_outfit = self._find_matching_outfit(selected_char_names)

        selected_characters = []
        for char_name in selected_char_names:
            char_data = self._randomize_character(
                char_name, 
                forced_outfit=matching_outfit, 
                include_pose=generate_poses,
                scene_category=scene_category, # Pass scene context
                context_tags=character_context_tags, # Pass expanded context
                theme_tags=base_prompt_tags # Pass base tags specifically as theme enforcers
            )
            char_data["color_scheme"] = color_scheme
            
            if prompt_framing:
                char_data["framing_mode"] = prompt_framing
                
            if random.random() < 0.25:
                char_data["use_signature_color"] = True
                
            selected_characters.append(char_data)

        # Generate notes
        notes_text = ""
        if selected_interaction_template:
            char_names = [char["name"] for char in selected_characters]
            notes_text = fill_template(selected_interaction_template, char_names)
        elif generate_interaction:
            # Smart Interaction Selection
            notes_text = self._generate_random_notes(selected_characters, scene_category)
        
        if not notes_text and random.random() < 0.1:
            notes_text = random.choice([
                "Focus on cinematic lighting and texture.",
                "Wide angle shot showing the full environment.",
                "Emphasis on the characters' expressions.",
                "High contrast with deep shadows.",
                "Soft, dreamlike atmosphere."
            ])

        config = {
            "selected_characters": selected_characters,
            "base_prompt": base_prompt,
            "scene": scene_text,
            "notes": notes_text,
            "color_scheme": color_scheme
        }

        return config

    def _select_smart_framing(self, num_characters):
        """Select a framing type appropriate for the number of characters.
        
        Args:
            num_characters: Number of characters in the scene.
            
        Returns:
            str: Selected framing name.
        """
        if not self.framing:
            return ""

        all_framings = list(self.framing.keys())
        
        # Define categories conceptually
        close_types = [f for f in all_framings if any(x in f.lower() for x in ["close", "portrait", "face", "head"])]
        wide_types = [f for f in all_framings if any(x in f.lower() for x in ["wide", "full", "long", "cinematic", "scenic"])]
        
        if num_characters == 1:
            # Single character: Bias towards close-ups/portraits (60%), regular random (40%)
            if close_types and random.random() < 0.6:
                return random.choice(close_types)
        elif num_characters >= 3:
            # Groups: Bias strongly towards wide/full shots (80%)
            if wide_types and random.random() < 0.8:
                return random.choice(wide_types)
        
        # Default fallback
        return random.choice(all_framings)

    def _select_smart_color_scheme(self, tags, scene_category):
        """Select a color scheme that matches character tags or scene mood.
        
        Args:
            tags: Set of character tags.
            scene_category: Selected scene category.
            
        Returns:
            str: Selected color scheme name.
        """
        if not self.color_schemes:
            return "Default (No Scheme)"

        matching_schemes = []
        all_schemes = list(self.color_schemes.keys())
        
        # Check against tags and scene
        search_terms = list(tags)
        if scene_category:
            search_terms.append(scene_category.lower())

        for scheme in all_schemes:
            scheme_lower = scheme.lower()
            for term in search_terms:
                if term in scheme_lower:
                    matching_schemes.append(scheme)
        
        # 50% chance to pick a matching scheme if found
        if matching_schemes and random.random() < 0.5:
            return random.choice(matching_schemes)
            
        return random.choice(all_schemes)

    def _select_smart_scene(self, tags):
        """Select a scene that matches the provided tags/themes."""
        if not self.scenes:
            # Fallback
            return "", self._generate_random_scene()

        # 1. Identify preferred scene categories based on tags
        # Logic: We match tag strings against category names roughly
        preferred_categories = set()
        
        # Tags driven matching
        for tag in tags:
            tag_clean = tag.lower()
            
            # Simple substring match against category names
            for cat_name in self.scenes.keys():
                if tag_clean in cat_name.lower():
                    preferred_categories.add(cat_name)
                    
                # Also check tags on scenes within category
                # If ANY scene in this category has the tag, the category is a candidate
                category_items = self.scenes[cat_name]
                matched_scenes = self._filter_items_by_tags(category_items, [tag_clean])
                if matched_scenes:
                    preferred_categories.add(cat_name)

        # 2. Find matching available categories in self.scenes
        available_categories = list(self.scenes.keys())
        matching_categories = list(preferred_categories)
        
        # If no strict match, fallback to broader name matching
        if not matching_categories:
            matching_categories = []
            for avail in available_categories:
                avail_lower = avail.lower()
                for t in tags:
                    if t.lower() in avail_lower:
                        matching_categories.append(avail)
                        break

        # 3. Select category
        selected_category = ""
        # Boosted smart chance 
        if matching_categories and random.random() < 0.9: 
            selected_category = random.choice(matching_categories)
        else:
            selected_category = random.choice(available_categories)

        # 4. Select preset from category
        presets = self.scenes.get(selected_category, {})
        if presets:
            preset_name = random.choice(list(presets.keys()))
            return selected_category, self._get_description(presets[preset_name])
        
        return "", ""

    def _randomize_character(self, char_name, forced_outfit=None, include_pose=True, scene_category="", context_tags=None, theme_tags=None):
        """Generate random outfit and pose for a character."""
        char_def = self.characters.get(char_name, {})
        outfits = char_def.get("outfits", {})
        categorized_outfits = char_def.get("outfits_categorized", {})
        tags = set(char_def.get("tags", []))
        
        # Merge with session context tags if provided
        if context_tags:
            tags = tags.union(context_tags)

        outfit_name = ""
        if forced_outfit and forced_outfit in outfits:
            outfit_name = forced_outfit
        elif outfits:
            # Smart Outfit Selection
            outfit_name = self._select_smart_outfit(outfits, categorized_outfits, tags, scene_category)

        # Random outfit modifier
        outfit_traits = []
        
        # New: Get structured data which might contain local modifiers
        outfit_data = outfits.get(outfit_name, "")
        outfit_desc = self._get_description(outfit_data)
        
        # Check for local modifiers
        local_modifiers = {}
        if isinstance(outfit_data, dict):
            local_modifiers = outfit_data.get("modifiers", {})

        if "{modifier}" in outfit_desc:
            # Prioritize local modifiers if they exist
            # If local modifiers are defined for this outfit, ONLY use those.
            # This ensures thematic coherence (no boxing headgear on volleyball players).
            available_modifiers = local_modifiers if local_modifiers else self.modifiers
            
            if available_modifiers and random.random() < 0.4:
                random_trait = random.choice(list(available_modifiers.keys()))
                outfit_traits.append(random_trait)

        # Random pose
        pose_category = ""
        pose_preset = ""
        
        if include_pose and self.poses:
            # Smart Pose Selection
            pose_category = self._select_smart_pose(self.poses, tags, scene_category, char_def.get("personality", ""), theme_tags=theme_tags)
            
            pose_presets = self.poses.get(pose_category, {})
            # Filter poses within category if we want deep tagging?
            # For now just pick random within category, maybe improve later to use _filter_items_by_tags here too
            if pose_presets:
                pose_preset = random.choice(list(pose_presets.keys()))

        return {
            "name": char_name,
            "outfit": outfit_name,
            "outfit_traits": outfit_traits,
            "custom_modifiers": local_modifiers, # Pass localized modifier definitions to builder
            "pose_category": pose_category,
            "pose_preset": pose_preset,
            "framing_mode": "", 
            "action_note": "",
        }

    def _select_smart_outfit(self, all_outfits, categorized_outfits, char_tags, scene_category):
        """Select an outfit that matches character tags or scene context."""
        if not categorized_outfits:
            return random.choice(list(all_outfits.keys()))

        # 1. Identify preferred outfit categories using Tags
        preferred_categories = set()
        
        # Collect context tags (Character Tags + Scene Name)
        context_tags = set(t.lower() for t in char_tags)
        if scene_category:
            context_tags.add(scene_category.lower())

        # Check which outfit categories match our context tags
        for cat_name, items in categorized_outfits.items():
            cat_lower = cat_name.lower()
            
            # 1. Category name match
            for t in context_tags:
                if t in cat_lower or cat_lower in t:
                    preferred_categories.add(cat_name)
                    break
                    
            # 2. Item tag match (deep check)
            # If any outfit in this category has a matching tag, the category is a candidate
            if cat_name not in preferred_categories:
                matched_items = self._filter_items_by_tags(items, context_tags)
                if matched_items:
                    preferred_categories.add(cat_name)

        # 2. Find matching available categories
        available_categories = list(categorized_outfits.keys())
        matching_categories = list(preferred_categories)

        # 3. Selection
        target_category = ""
        # Boosted smart chance 
        if matching_categories and random.random() < 0.95:
            target_category = random.choice(matching_categories)
        else:
            # Fallback: Just pick any category (weighted slightly away from 'Common' if possible?)
            target_category = random.choice(available_categories)

        # Pick outfit from category
        outfits_in_cat = categorized_outfits.get(target_category, {})
        if outfits_in_cat:
            return random.choice(list(outfits_in_cat.keys()))
        
        return random.choice(list(all_outfits.keys()))

    def _select_smart_pose(self, all_poses, char_tags, scene_category, personality, theme_tags=None):
        """Select a pose category that matches character or scene."""
        available_categories = list(all_poses.keys())
        if not available_categories:
            return ""

        preferred_categories = set()
        
        context_tags = set(t.lower() for t in char_tags)
        if scene_category:
            context_tags.add(scene_category.lower())
            
        # Match Categories and Items within categories
        for cat_name, items in all_poses.items():
            cat_lower = cat_name.lower()
            
            # Simple name match
            if any(t in cat_lower for t in context_tags):
                preferred_categories.add(cat_name)
                continue
                
            # Deep tag match
            matched_items = self._filter_items_by_tags(items, context_tags)
            if matched_items:
                preferred_categories.add(cat_name)

        matching_categories = list(preferred_categories)
        
        # Filter matching categories by theme_tags if provided (Strict Mode)
        if theme_tags and matching_categories:
            strict_matches = []
            for cat_name in matching_categories:
                cat_lower = cat_name.lower()
                items = all_poses.get(cat_name, {})
                
                # Check if this category matches the theme
                matches_theme = False
                
                # 1. Name match against theme
                if any(t in cat_lower for t in theme_tags):
                    matches_theme = True
                else:
                    # 2. Item tag match against theme
                    if self._filter_items_by_tags(items, theme_tags):
                        matches_theme = True
                
                if matches_theme:
                    strict_matches.append(cat_name)
            
            # If we found strict matches, use ONLY them
            if strict_matches:
                matching_categories = strict_matches
        
        # Boosted smart chance (was 0.6)
        if matching_categories and random.random() < 0.95:
            return random.choice(matching_categories)
            
        return random.choice(available_categories)

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
        """Generate a random scene description from scene presets."""
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
            return self._get_description(presets[preset_name])
        return ""

    def _generate_random_notes(self, selected_characters, scene_category=""):
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
                    # Smart filtering based on scene
                    if scene_category:
                        # Simple heuristic: prioritize templates that might match the scene?
                        # For now, we rely on random chance, maybe improve later.
                        # But we can filter by interaction key words if we had them.
                        eligible_templates.append(desc)
                    else:
                        eligible_templates.append(desc)

        if eligible_templates:
            template = random.choice(eligible_templates)

            # Fill template with character names
            char_names = [char["name"] for char in selected_characters]
            return fill_template(template, char_names)
            
        return ""

    def _select_smart_base_prompt(self, base_prompts, char_tags, scene_category):
        """Select a base prompt that matches character tags or scene context.
        
        Args:
           base_prompts: Dictionary of base prompts
           char_tags: Set of character tags
           scene_category: Selected scene category
           
        Returns:
            str: Selected base prompt name
        """
        if not base_prompts:
             return ""
             
        available_prompts = list(base_prompts.keys())
        preferred_prompts = set()
        
        # Collect context tags
        context_tags = set(t.lower() for t in char_tags)
        if scene_category:
            context_tags.add(scene_category.lower())
            
        # Check against tags in base prompt definition (now that we support structured dicts)
        for name, data in base_prompts.items():
            # If data is a dict (new format), check its tags
            prompt_tags = []
            if isinstance(data, dict):
                prompt_tags = [t.lower() for t in data.get("tags", [])]
            
            # Match if any context tag matches a prompt tag
            # or if context tag matches name
            if any(t in name.lower() for t in context_tags):
                preferred_prompts.add(name)
                continue
                
            if prompt_tags:
                if any(t in prompt_tags for t in context_tags):
                    preferred_prompts.add(name)
                    
        matching = list(preferred_prompts)
        if matching and random.random() < 0.7:
             return random.choice(matching)
             
        # Fallback to completely random
        return random.choice(available_prompts)
