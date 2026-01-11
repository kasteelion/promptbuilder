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

    # Define tag aliases/groups to expand thematic matching
    TAG_ALIASES = {
        "athletic": ["sport", "sports", "active", "training", "gym"],
        "sport": ["sports", "athletic", "active"],
        "sports": ["sport", "athletic", "active"],
        "creative": ["art", "artistic"],
        "art": ["creative", "artistic"],
        "vintage": ["retro", "nostalgic", "old-school"],
        "retro": ["vintage", "nostalgic"],
        "soft": ["gentle", "calm", "pastel"],
        "edgy": ["alternative", "dark", "cool"],
        "luxury": ["rich", "expensive", "elegant", "fashion", "glamour"],
        "glamour": ["luxury", "fashion", "elegant", "style"],
        "western": ["rugged", "outdoorsy", "casual", "edgy"],
        "cottagecore": ["soft", "nature", "vintage", "calm"],
        "combat": ["action", "dynamic", "intense"],
        "action": ["combat", "dynamic", "intense"],
        "fantasy": ["magic", "mythology"],
        "intense": ["dramatic", "dynamic"],
        "dramatic": ["intense", "theatrical"],
        "anime": ["japanese", "2d"],
        "rugged": ["outdoor", "nature", "western", "action", "gritty"],
        "commanding": ["urban", "office", "luxury", "formal", "work"],
        "chic": ["fashion", "luxury", "urban", "modern", "city"],
        "minimalist": ["modern", "studio", "clean", "simple", "indoor"],
        "approachable": ["casual", "home", "cozy", "warm", "social"],
        "playful": ["fun", "colorful", "casual", "active", "outdoor"],
        "intellectual": ["library", "office", "quiet", "indoor", "school"],
        "outdoorsy": ["nature", "hiking", "adventure", "park", "forest"],
        "traditional": ["cultural", "history", "classic", "temple"],
        # Bridges for under-represented styles
        "japanese": ["anime", "manga"],
        "modern": ["realistic", "contemporary", "urban"],
        "casual": ["realistic", "everyday", "life"],
        "detailed": ["high definition", "realistic"],
        "portrait": ["photography", "realistic"],
        # Universal Realism (Make Photorealistic the default baseline)
        "female": ["realistic", "high definition", "photography"],
        "male": ["realistic", "high definition", "photography"],
    }

    def _expand_tags(self, tags):
        """Expand tags with aliases/groups."""
        expanded = set(tags)
        for t in tags:
            t_lower = t.lower()
            if t_lower in self.TAG_ALIASES:
                expanded.update(self.TAG_ALIASES[t_lower])
        return expanded

    def _check_color_support(self, char_name, outfit_name):
        """Check if an outfit supports color substitution or signature colors."""
        char_def = self.characters.get(char_name, {})
        outfit_data = char_def.get("outfits", {}).get(outfit_name, "")
        
        # Convert outfit data to a checkable string
        outfit_str = ""
        if isinstance(outfit_data, dict):
            # Check all values in the dict (Top, Bottom, etc.)
            outfit_str = " ".join(str(v) for k, v in outfit_data.items() if isinstance(v, str))
        else:
            outfit_str = str(outfit_data)
        
        # Check for color placeholders
        has_schemes = any(f"{{{k}}}" in outfit_str for k in ("primary_color", "secondary_color", "accent"))
        has_sig = "{signature_color}" in outfit_str or "(signature)" in outfit_str
        
        return has_schemes or has_sig

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
    def _extract_special_tags(self, tags):
        """Extract special tags (Mood:, Block:) from a list of tags.
        
        Args:
            tags: List/Set of tags.
            
        Returns:
            tuple: (normal_tags, mood_tags, blocked_tags)
        """
        normal = set()
        mood = set()
        blocked = set()
        
        for t in tags:
            t_str = str(t)
            if t_str.startswith("Mood:"):
                mood.add(t_str[5:].strip())
            elif t_str.startswith("Block:"):
                blocked.add(t_str[6:].strip().lower()) # Block tags are case-insensitive for matching
            else:
                normal.add(t_str)
                
        return normal, mood, blocked

    def randomize(self, num_characters=None, include_scene=False, include_notes=False, forced_base_prompt=None, candidates=10, match_outfits_prob=0.3):
        """Generate multiple candidates and return the highest scoring one."""
        best_config = None
        best_score = -float('inf')
        
        # If we are forcing a prompt or have specific constraints, we might want fewer candidates to save time?
        # But for quality, consistent N is better.
        
        # Debug: Print that we are running Monte Carlo
        # print(f"Generating {candidates} candidates...")
        
        for _ in range(candidates):
            config = self._generate_single_candidate(num_characters, include_scene, include_notes, forced_base_prompt, match_outfits_prob=match_outfits_prob)
            score = self._score_candidate(config)
            
            # print(f"Candidate score: {score}")
            
            if score > best_score:
                best_score = score
                best_config = config
        
        # Clean up metadata before returning if it's not needed for the consumer
        # But maybe it's useful? Let's leave it for now or explicitly remove it if strict schema needed.
        # best_config.pop("metadata", None)
        
        if best_config and "metadata" in best_config:
            best_config["metadata"]["score"] = best_score
            
        return best_config

    def _score_candidate(self, config):
        """Score a generated configuration based on heuristics for high-quality variety."""
        score = 0
        breakdown = {
            "mood_matches": 0,
            "style_matches": 0,
            "interaction_matches": 0,
            "tag_matches": 0,
            "diversity_bonus": 0,
            "repetitive_penalty": 0,
            "warnings": []
        }
        
        metadata = config.get("metadata", {})
        
        # Expand moods for broader matching
        raw_moods = metadata.get("moods", [])
        active_moods = self._expand_tags([m.lower() for m in raw_moods])
        
        if not active_moods:
            breakdown["warnings"].append("No active moods/context found for thematic scoring.")

        # 1. Base Structure (+5 each) - Always awarded for being a valid config
        if config.get("scene"): score += 5
        if config.get("notes"): score += 5
            
        # 2. Art Style Alignment (+25 per matching expanded mood) - INCREASED FROM +15
        base_prompt_name = config.get("base_prompt")
        if base_prompt_name and active_moods:
            base_style_data = self.base_prompts.get(base_prompt_name, {})
            style_tags = self._expand_tags([t.lower() for t in self._get_tags(base_style_data)])
            style_matches = len(style_tags.intersection(active_moods))
            points = style_matches * 25  # INCREASED FROM 15
            score += points
            breakdown["style_matches"] = points
            
            # NEW: Style-Scene Mismatch Penalty (-30 if style blocks scene theme)
            scene_tags = metadata.get("scene_tags", [])
            scene_themes = self._expand_tags([t.lower() for t in scene_tags])
            _, _, style_blocks = self._extract_special_tags(self._get_tags(base_style_data))
            
            for theme in scene_themes:
                if theme in style_blocks:
                    penalty = 30
                    score -= penalty
                    breakdown["mismatch_penalty"] = breakdown.get("mismatch_penalty", 0) - penalty
                    breakdown["warnings"].append(f"Style '{base_prompt_name}' blocks scene theme '{theme}'")

        # 3. Dynamic Thematic Character Alignment
        selected_chars = config.get("selected_characters", [])
        outfit_names = set()
        
        for char in selected_chars:
            char_name = char.get("name")
            char_def = self.characters.get(char_name, {})
            outfit_name = char.get("outfit")
            outfit_names.add(outfit_name)
            
            # A) Outfit Tags vs Scene Moods (+30 per match) - HIGHEST TIER, INCREASED FROM +20
            outfits_dict = char_def.get("outfits", {})
            outfit_data = outfits_dict.get(outfit_name)
            if outfit_data and active_moods:
                tags = self._expand_tags([t.lower() for t in self._get_tags(outfit_data)])
                matches = len(tags.intersection(active_moods))
                points = matches * 30  # INCREASED FROM 20
                score += points
                breakdown["mood_matches"] += points
            elif not outfit_data and active_moods:
                breakdown["warnings"].append(f"No outfit data found for {char_name}'s {outfit_name}")
            
            # B) Pose Alignment (+10 per category match) - MEDIUM TIER
            pose_cat = char.get("pose_category")
            if pose_cat and active_moods:
                if any(m in pose_cat.lower() for m in active_moods):
                    score += 10
                    breakdown["tag_matches"] += 10
                    
            # C) Character Trait Alignment (+5 per match) - LOW TIER
            char_tags = self._expand_tags([t.lower() for t in char_def.get("tags", [])])
            char_matches = len(char_tags.intersection(active_moods))
            points = char_matches * 5
            score += points
            breakdown["tag_matches"] += points

        # 4. Interaction Alignment (+10 per match)
        interaction_tags = self._expand_tags([t.lower() for t in metadata.get("interaction_tags", [])])
        if interaction_tags and active_moods:
            interaction_matches = len(interaction_tags.intersection(active_moods))
            points = interaction_matches * 10
            score += points
            breakdown["interaction_matches"] = points

        # 5. Group Diversity / Variety (+5 per unique outfit)
        if len(selected_chars) > 1:
            points = len(outfit_names) * 5
            score += points
            breakdown["diversity_bonus"] = points
            
        # 6. Repetitiveness Penalty (-2 per repeated word > 4 chars)
        text_content = f"{config.get('scene', '')} {config.get('notes', '')}".lower()
        clean_text = text_content.replace(',', ' ').replace('.', ' ').replace('!', ' ').replace('?', ' ')
        words = [w for w in clean_text.split() if len(w) > 4]
        seen_words = set()
        penalty = 0
        for w in words:
            if w in seen_words:
                penalty += 2
            seen_words.add(w)
        
        score -= penalty
        breakdown["repetitive_penalty"] = -penalty
            
        metadata["score_breakdown"] = breakdown
        return score

    def _generate_single_candidate(self, num_characters=None, include_scene=False, include_notes=False, forced_base_prompt=None, match_outfits_prob=0.3):
        """Generate a single random prompt configuration."""
        # Step 1: Resolve conflicts between Interactions and Poses
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

        # Step 2: Determine number of characters
        # If we want interaction, we prefer multi-character unless forced otherwise
        min_chars_needed = 2 if generate_interaction else 1
        
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
                "color_scheme": "Default (No Scheme)",
                "metadata": {"moods": set()}
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
        
        # Expand tags with aliases (e.g. athletic -> sport)
        combined_tags = self._expand_tags(combined_tags)

        # Maintain Context Sets
        context_moods = set()
        context_blocked = set()

        # Select Scene (Smart)
        scene_text = ""
        scene_category = ""
        scene_tags = []
        
        if include_scene:
            # Generate scene with metadata (Smart Selection)
            scene_text, scene_category, scene_tags = self._select_smart_scene(combined_tags)
            
            # Add scene tags to context (if any)
            if scene_tags:
                combined_tags.update([t.lower() for t in scene_tags])
                _, scene_moods, scene_blocked = self._extract_special_tags(scene_tags)
                context_moods.update(scene_moods)
                context_blocked.update(scene_blocked)
                
                # Treat high-level scene tags as moods for scoring
                CORE_THEMES = {"fantasy", "cyberpunk", "sci-fi", "noir", "sports", "western", "historical", "alternative"}
                for t in scene_tags:
                    if t.lower() in CORE_THEMES:
                        context_moods.add(t.strip())

        # Move Color Scheme selection down (after characters are randomized)
        color_scheme = "Default (No Scheme)"

        # Smart Framing Selection
        prompt_framing = ""
        # Check if scene had Frame tags?
        # If we are suppressing poses (Interaction Dominant), we MUST have framing to avoid blank section.
        framing_chance = 1.0 if not generate_poses else 0.7
        if self.framing and random.random() < framing_chance: 
            prompt_framing = self._select_smart_framing(num_to_select, context_tags=combined_tags, scene_category=scene_category)

        # Smart Base Prompt Selection (Override)
        if self.base_prompts and not forced_base_prompt:
             base_prompt = self._select_smart_base_prompt(self.base_prompts, combined_tags, scene_category)

        # Extract tags from the selected base prompt
        base_prompt_tags = set()
        if base_prompt and base_prompt in self.base_prompts:
            bp_data = self.base_prompts[base_prompt]
            if isinstance(bp_data, dict):
                tags = bp_data.get("tags", [])
                _, bp_mood, bp_blocked = self._extract_special_tags(tags)
                context_moods.update(bp_mood)
                context_blocked.update(bp_blocked)
                
                # Treat high-level art style tags as moods for scoring if they are significant
                CORE_THEMES = {"fantasy", "cyberpunk", "sci-fi", "noir", "sports", "western", "historical", "alternative"}
                for t in tags:
                    t_lower = t.lower()
                    base_prompt_tags.add(t_lower)
                    if t_lower in CORE_THEMES:
                        context_moods.add(t.strip())

        # Add Moods to Base Tags for theming
        # Moods act as strong theme drivers
        base_prompt_tags.update([m.lower() for m in context_moods])
        
        # Add base prompt tags to the context for character randomization
        character_context_tags = combined_tags.union(base_prompt_tags)

        # -- SMART LOGIC END --

        # For pairs, randomized chance to use matching outfits (default 30%)
        use_matching_outfits = num_to_select >= 2 and random.random() < match_outfits_prob
        matching_outfit = None

        if use_matching_outfits:
            matching_outfit = self._find_matching_outfit(
                selected_char_names, 
                context_tags=character_context_tags, 
                scene_category=scene_category,
                blocked_tags=context_blocked
            )

        selected_characters = []
        any_supports_color = False
        
        for char_name in selected_char_names:
            char_data = self._randomize_character(
                char_name, 
                forced_outfit=matching_outfit, 
                include_pose=generate_poses,
                scene_category=scene_category, # Pass scene context
                context_tags=character_context_tags, # Pass expanded context
                theme_tags=base_prompt_tags, # Pass base tags specifically as theme enforcers
                blocked_tags=context_blocked # Pass blocked tags
            )
            
            # Check if THIS specific character's outfit supports colors
            if self._check_color_support(char_name, char_data.get("outfit", "")):
                any_supports_color = True
                
            if random.random() < 0.25:
                char_data["use_signature_color"] = True
                
            selected_characters.append(char_data)

        # Smart Color Scheme Selection (Only if someone can use it)
        if any_supports_color and self.color_schemes and random.random() > 0.3:
            combined_search_tags = character_context_tags.union([m.lower() for m in context_moods])
            color_scheme = self._select_smart_color_scheme(combined_search_tags, scene_category)
        
        # Apply color scheme to all (for consistency across the group if they DO use it)
        for char in selected_characters:
            char["color_scheme"] = color_scheme
            if prompt_framing:
                char["framing_mode"] = prompt_framing

        # Generate notes
        notes_text = ""
        interaction_tags = []
        if generate_interaction:
            # Smart Interaction Selection
            notes_text, interaction_tags = self._generate_random_notes(
                selected_characters, 
                scene_category, 
                context_tags=character_context_tags,
                blocked_tags=context_blocked
            )
        
        if not notes_text and random.random() < 0.1:
            notes_text = random.choice([
                "Focus on cinematic lighting and texture.",
                "Wide angle shot showing the full environment.",
                "Emphasis on the characters' expressions.",
                "High contrast with deep shadows.",
                "Soft, dreamlike atmosphere."
            ])
            # Give generic notes some generic tags for scoring
            interaction_tags = ["cinematic", "lighting", "creative"]

        config = {
            "selected_characters": selected_characters,
            "base_prompt": base_prompt,
            "scene": scene_text,
            "notes": notes_text,
            "color_scheme": color_scheme,
            "metadata": {
                "moods": list(context_moods),
                "interaction_tags": interaction_tags
            }
        }

        return config

    def _select_smart_framing(self, num_characters, context_tags=None, scene_category=""):
        """Select a framing type appropriate for the number of characters and context.
        
        Args:
            num_characters: Number of characters in the scene.
            context_tags: Set of tags describing the content (optional).
            scene_category: Category of the scene (optional).
            
        Returns:
            str: Selected framing name.
        """
        if not self.framing:
            return ""

        all_framings = list(self.framing.keys())
        
        # Define mapping
        # Maps keywords in tags -> Preferred Framing Categories
        tag_map = {
            "portrait": ["Close-up"],
            "face": ["Close-up"],
            "makeup": ["Close-up"],
            "detail": ["Close-up"],
            "fashion": ["Full Body", "Cowboy Shot"],
            "outfit": ["Full Body", "Cowboy Shot"],
            "shoes": ["Full Body"],
            "action": ["Full Body", "Wide Shot", "Cowboy Shot"],
            "landscape": ["Wide Shot"],
            "scenic": ["Wide Shot"],
        }
        
        # 1. Check Tags
        preferred_framings = []
        if context_tags:
            for tag in context_tags:
                tag_lower = tag.lower()
                for key, targets in tag_map.items():
                    if key in tag_lower:
                        preferred_framings.extend(targets)
                        
        if preferred_framings and random.random() < 0.7:
             # Try to find valid names in our loaded framing dict
             valid_preferred = [f for f in preferred_framings if f in self.framing]
             if valid_preferred:
                 return random.choice(valid_preferred)
        
        # 2. Check Number of Characters (Fallback/Override)
        close_types = [f for f in all_framings if any(x in f.lower() for x in ["close", "portrait", "face", "head"])]
        wide_types = [f for f in all_framings if any(x in f.lower() for x in ["wide", "full", "long", "cinematic", "scenic", "group"])]
        
        if num_characters == 1:
            # Single character: Bias slightly towards close/mid unless tags said otherwise
            if close_types and random.random() < 0.4:
                return random.choice(close_types)
        elif num_characters >= 3:
            # Groups: Bias STRONGLY vs Close-ups (physically hard to fit)
            if wide_types:
                return random.choice(wide_types)
            # If no wide types found, return random but avoid close-ups if possible
            non_close = [f for f in all_framings if f not in close_types]
            if non_close:
                return random.choice(non_close)
        
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
        """Select a scene that matches the provided tags/themes.
        
        Returns:
            tuple: (scene_description, category_name, scene_tags)
        """
        if not self.scenes:
            # Fallback
            return self._generate_random_scene()

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
        # Reduced probability from 0.9 to 0.2 to prioritize variety/wholistic generation
        # relying on Outfit adaptation to maintain coherence (Scene-First approach)
        if matching_categories and random.random() < 0.2: 
            selected_category = random.choice(matching_categories)
        else:
            selected_category = random.choice(available_categories)

        # 4. Select preset from category
        presets = self.scenes.get(selected_category, {})
        if presets:
            preset_name = random.choice(list(presets.keys()))
            preset_data = presets[preset_name]
            return self._get_description(preset_data), selected_category, self._get_tags(preset_data)
        
        return "", "", []

    def _randomize_character(self, char_name, forced_outfit=None, include_pose=True, scene_category="", context_tags=None, theme_tags=None, blocked_tags=None):
        """Generate random outfit and pose for a character."""
        char_def = self.characters.get(char_name, {})
        outfits = char_def.get("outfits", {})
        categorized_outfits = char_def.get("outfits_categorized", {})
        tags = set(char_def.get("tags", []))
        
        # Merge with session context tags if provided
        if context_tags:
            tags = tags.union(context_tags)
            
        # Expand tags with aliases
        tags = self._expand_tags(tags)

        outfit_name = ""
        if forced_outfit and forced_outfit in outfits:
            outfit_name = forced_outfit
        elif outfits:
            # Smart Outfit Selection
            outfit_name = self._select_smart_outfit(outfits, categorized_outfits, tags, scene_category, blocked_tags)

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

        # Extract outfit tags to influence pose
        outfit_tags = []
        if isinstance(outfit_data, dict):
            outfit_tags = outfit_data.get("tags", [])
        
        # Add outfit tags to the context for pose selection
        pose_context_tags = tags.union(outfit_tags)

        # Random pose
        pose_category = ""
        pose_preset = ""
        
        if include_pose and self.poses:
            # Smart Pose Selection
            pose_category = self._select_smart_pose(self.poses, pose_context_tags, scene_category, char_def.get("personality", ""), theme_tags=theme_tags, blocked_tags=blocked_tags)
            
            pose_presets = self.poses.get(pose_category, {})
            # Filter Blocked Poses within category
            valid_pose_names = list(pose_presets.keys())
            
            # Context-Aware Blocking
            # Prevent "Satin Sheets" in public spaces
            # Ideally this should be tag-based, but for the specific recurring issue:
            if "satin sheets" in str(pose_presets).lower() and scene_category not in ["Bedroom", "Studio", "Indoors"]:
                 valid_pose_names = [
                     name for name in valid_pose_names 
                     if "satin sheets" not in name.lower() and "bed" not in name.lower()
                 ]

            if blocked_tags:
                 valid_pose_names = [
                     name for name in valid_pose_names 
                     if not any(
                         bt in (t.lower() for t in self._get_tags(pose_presets[name])) 
                         for bt in blocked_tags
                     )
                 ]
            
            if valid_pose_names:
                pose_preset = random.choice(valid_pose_names)

        # Random Character Traits (e.g. Glasses, Freckles)
        # 90% chance to include a trait if available
        selected_character_traits = []
        available_traits = char_def.get("traits", {})
        if available_traits and random.random() < 0.9:
            # Pick one random trait
            selected_character_traits.append(random.choice(list(available_traits.keys())))

        return {
            "name": char_name,
            "outfit": outfit_name,
            "outfit_traits": outfit_traits,
            "character_traits": selected_character_traits,
            "custom_modifiers": local_modifiers, # Pass localized modifier definitions to builder
            "pose_category": pose_category,
            "pose_preset": pose_preset,
            "framing_mode": "", 
            "action_note": "",
        }

    def _select_smart_outfit(self, all_outfits, categorized_outfits, char_tags, scene_category, blocked_tags=None):
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

        # -- CONTEXT-AWARE BLOCKING (Logic Update) --
        # Block specific categories based on scene
        blocked_categories = set()
        
        scene_lower = scene_category.lower()
        if any(x in scene_lower for x in ["gym", "sports", "training", "workout"]):
            blocked_categories.update(["Formal", "Business", "Evening", "Gala", "Elegant"])
        elif any(x in scene_lower for x in ["office", "street", "winter", "city", "urban"]):
            blocked_categories.update(["Swimwear", "Bikini", "Lingerie"])
        
        # Filter available and matching categories
        available_categories = [c for c in available_categories if c not in blocked_categories]
        matching_categories = [c for c in matching_categories if c not in blocked_categories]
        
        # If we blocked everything, revert to available (safety net)
        if not available_categories:
             available_categories = list(categorized_outfits.keys())

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
        
        # -- BLOCKING LOGIC --
        if blocked_tags and outfits_in_cat:
            # Filter out blocked outfits
            valid_outfits = []
            for name, data in outfits_in_cat.items():
                 item_tags = [t.lower() for t in self._get_tags(data)]
                 
                 if not any(bt in item_tags for bt in blocked_tags):
                     valid_outfits.append(name)
            
            # If we filtered everything, try falling back to all available outfits (minus blocked)
            if not valid_outfits:
                # Emergency fallback: Search GLOBAL list
                for name, data in all_outfits.items():
                     item_tags = [t.lower() for t in self._get_tags(data)]
                     if not any(bt in item_tags for bt in blocked_tags):
                         valid_outfits.append(name)
            
            if valid_outfits:
                return random.choice(valid_outfits)
            
            # If STILL no valid outfits (everything blocked?), return basic fallback
            # Ideally this shouldn't happen unless "Block:Clothing" exists
            # Just return something random and hope for the best
            return random.choice(list(outfits_in_cat.keys()))

        if outfits_in_cat:
            return random.choice(list(outfits_in_cat.keys()))
        
        return random.choice(list(all_outfits.keys()))

    def _select_smart_pose(self, all_poses, char_tags, scene_category, personality, theme_tags=None, blocked_tags=None):
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
        target_category = ""
        if matching_categories and random.random() < 0.95:
             target_category = random.choice(matching_categories)
        else:
             target_category = random.choice(available_categories)
             
        # -- BLOCKING LOGIC --
        # Ideally we should check if the category ITSELF is blocked?
        # Or just let the subsequent preset filtering handle it?
        # Let's check if the category name contains a blocked tag
        if blocked_tags:
            # If target category name contains a blocked tag, try to pick another
            cat_lower = target_category.lower()
            if any(bt in cat_lower for bt in blocked_tags):
                # Try to find a safe category
                safe_categories = [
                    c for c in available_categories 
                    if not any(bt in c.lower() for bt in blocked_tags)
                ]
                if safe_categories:
                    target_category = random.choice(safe_categories)
        
        return target_category

    def _find_matching_outfit(self, char_names, context_tags=None, scene_category="", blocked_tags=None):
        """Find a common outfit name that exists for all characters.

        Args:
            char_names: List of character names
            context_tags: Context tags for smart selection
            scene_category: Scene category for smart selection
            blocked_tags: Tags to excluding

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

        # Return smart choice from common outfits
        if common_outfits:
            candidates = list(common_outfits)
            
            # 1. Filter Blocked Tags (if we can inspect outfit tags)
            # This is tricky because we need to check the outfit definition for EACH character.
            # But usually if they share the name, the tags are similar?
            # Let's check the first character's definition of this outfit.
            final_candidates = []
            
            first_char = self.characters.get(char_names[0], {})
            first_char_outfits = first_char.get("outfits", {})
            
            for outfit_name in candidates:
                # Check for blocking
                is_blocked = False
                outfit_data = first_char_outfits.get(outfit_name)
                outfit_tags = [t.lower() for t in self._get_tags(outfit_data)]
                
                if blocked_tags and any(bt in outfit_tags for bt in blocked_tags):
                    is_blocked = True
                    
                if not is_blocked:
                    final_candidates.append(outfit_name)
            
            if not final_candidates:
                return None
                
            # 2. Smart Selection (Match Scene/Context)
            # Prioritize outfits that match context tags
            preferred = []
            search_tags = set()
            if context_tags:
                search_tags.update(t.lower() for t in context_tags)
            if scene_category:
                search_tags.add(scene_category.lower())
                
            for outfit_name in final_candidates:
                outfit_data = first_char_outfits.get(outfit_name)
                outfit_tags = [t.lower() for t in self._get_tags(outfit_data)]
                outfit_name_lower = outfit_name.lower()
                
                # Check match
                # Name match
                if any(t in outfit_name_lower for t in search_tags):
                    preferred.append(outfit_name)
                    continue
                # Tag match
                if any(t in outfit_tags for t in search_tags):
                    preferred.append(outfit_name)
                    
            if preferred and random.random() < 0.8:
                return random.choice(preferred)
                
            return random.choice(final_candidates)
        return None

    def _generate_random_scene(self):
        """Generate a random scene description from scene presets.
        
        Returns:
             tuple: (description, category, tags)
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
            return random.choice(scene_elements), "Fallback", []

        # Pick random category and preset
        category = random.choice(list(self.scenes.keys()))
        presets = self.scenes[category]
        if presets:
            preset_name = random.choice(list(presets.keys()))
            data = presets[preset_name]
            desc = self._get_description(data)
            tags = self._get_tags(data)
            return desc, category, tags
            
        return "", "", []

    def _generate_random_notes(self, selected_characters, scene_category="", context_tags=None, blocked_tags=None):
        """Generate random interaction template filled with character names.

        Args:
            selected_characters: List of selected character dicts with 'name' key
            scene_category: Category of the scene
            context_tags: Set of context tags (e.g. from characters, scene, base prompt)
            blocked_tags: Set of tags to block (e.g. from scene)

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
        
        context_tags_lower = {t.lower() for t in context_tags} if context_tags else set()

        for category, templates in self.interactions.items():
            for name, data in templates.items():
                # Handle both new structured format and legacy string format
                tags = []
                if isinstance(data, dict):
                    desc = data.get("description", "")
                    min_chars = data.get("min_chars", 1)
                    tags = data.get("tags", [])
                else:
                    desc = data
                    min_chars = 1
                    
                # Check if we have enough characters
                if num_chars >= min_chars:
                    # TAG FILTERING logic (Interaction Pairs)
                    # If template has tags, we check for compatibility.
                    # Rule: If template has specific tags (e.g. "Basketball"), AT LEAST ONE must be present in context.
                    # Exception: "Sport" is generic. If templates only have "Sport", maybe we allow?
                    # Better Rule: If template has tags, INTERSECTION with context must be > 0.
                    
                    if tags:
                        template_tags_lower = {t.lower() for t in tags}
                        
                        # BLOCKING logic
                        if blocked_tags:
                            blocked_lower = {b.lower() for b in blocked_tags}
                            # Check for "Block:Tag" format
                            raw_blocked = {b.split(":", 1)[1].lower() for b in blocked_lower if b.startswith("block:")}
                            if template_tags_lower.intersection(raw_blocked):
                                continue

                        # SMART FILTERING logic
                        if not template_tags_lower.intersection(context_tags_lower):
                            continue
                            
                    eligible_templates.append((desc, tags))

        if eligible_templates:
            # Pick a random template and its tags
            template_text, template_tags = random.choice(eligible_templates)

            # Fill template with character names
            char_names = [char["name"] for char in selected_characters]
            return fill_template(template_text, char_names), template_tags
            
        return "", []

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
        
        # DRASTIC MEASURE: Explicitly favor Photorealism if it is a valid match
        # This ensures it becomes the "Default" style as requested by user.
        photo_match = next((k for k in matching if "Photorealistic" in k), None)
        if photo_match and random.random() < 0.5:
            return photo_match

        # Probability 0.65: Selection from matching pool
        if matching and random.random() < 0.65:
             return random.choice(matching)
             
        # Fallback to completely random
        return random.choice(available_prompts)
