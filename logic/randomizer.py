"""Randomizer for generating random prompt configurations."""

import random

from utils.interaction_helpers import fill_template

class PromptRandomizer:
    """Generates random character, outfit, and pose combinations."""

    # Define hard strict blocks to prevent "Outfit Salad"
    # Key: Tag found in Scene
    # Value: List of tags to BLOCK in Outfits/Poses
    SCENE_RESTRICTIONS = {
        "office": ["swimwear", "bikini", "lingerie", "armor", "fantasy", "medieval", "costume", "pajamas", "bed", "sleep"],
        "library": ["swimwear", "bikini", "lingerie", "armor", "fantasy", "medieval", "costume", "sport", "gym", "leotard", "weapon", "action", "combat"],
        "quiet": ["sport", "gym", "combat", "action", "loud", "party"],
        "work": ["swimwear", "bikini", "lingerie", "armor", "fantasy", "medieval", "costume", "bed", "sleep"],
        "school": ["swimwear", "bikini", "lingerie", "armor", "fantasy", "weapon", "bed", "sleep"],
        "hospital": ["swimwear", "bikini", "lingerie", "armor", "fantasy", "medieval", "formal", "evening", "party"],
        "medical": ["swimwear", "bikini", "lingerie", "armor", "fantasy", "medieval", "formal", "evening", "party"],
        "gym": ["formal", "business", "evening", "gala", "suit", "armor", "jeans", "dress", "bed", "sofa", "couch"],
        "sport": ["formal", "business", "evening", "gala", "suit", "armor", "jeans", "dress", "heels", "bed", "sofa"],
        "beach": ["suit", "business", "formal", "winter", "coat", "jacket", "hoodie", "snow", "computer", "desk"],
        "pool": ["suit", "business", "formal", "winter", "coat", "jacket", "hoodie", "snow", "jeans", "computer", "desk"],
        "winter": ["swimwear", "bikini", "lingerie", "sleeveless", "shorts", "crop top"],
        "snow": ["swimwear", "bikini", "lingerie", "sleeveless", "shorts", "crop top", "sandals", "heels"],
        "indoor": ["winter", "snow", "ski", "heavy coat"], 
        "formal": ["swimwear", "bikini", "lingerie", "casual", "sport", "gym", "pajamas"],
        "gala": ["swimwear", "bikini", "lingerie", "casual", "sport", "gym", "pajamas", "jeans"],
        "bed": ["armor", "weapon", "shoes", "boots", "jacket", "coat", "hat", "standing", "run", "jump"],
        "sleep": ["armor", "weapon", "shoes", "boots", "jacket", "coat", "hat", "jeans", "formal", "standing"],
        "gallery": ["swimwear", "bikini", "lingerie", "armor", "costume", "sport", "combat", "bed", "sleep", "running"],
        "museum": ["swimwear", "bikini", "lingerie", "armor", "costume", "sport", "combat", "bed", "sleep", "running"],
        # Thematic Blocks
        "fantasy": ["sci-fi", "cyberpunk", "tech", "modern", "office", "business", "gun", "rifle", "computer"],
        "nature": ["office", "business", "sci-fi", "cyberpunk", "tech", "computer"],
        "sci-fi": ["fantasy", "medieval", "armor", "sword", "shield", "robe"],
        "cyberpunk": ["fantasy", "medieval", "armor", "sword", "shield", "robe", "nature"],
        "waterfall": ["sci-fi", "cyberpunk", "tech", "office", "suit", "computer"],
        "forest": ["sci-fi", "cyberpunk", "tech", "office", "suit", "computer"],
    }

    # POSITIVE constraints. If a scene matches a key, ONLY allow items with these tags.
    # If no items match, logic falls back to the SCENE_RESTRICTIONS blacklist.
    SCENE_WHITELISTS = {
        "gym": ["sport", "athletic", "gym", "active", "workout", "fitness", "yoga"],
        "sport": ["sport", "athletic", "gym", "active", "workout", "fitness", "yoga", "jersey", "uniform"],
        "medical": ["medical", "scrubs", "coat", "uniform", "doctor", "nurse", "white", "lab"],
        "hospital": ["medical", "scrubs", "coat", "uniform", "doctor", "nurse", "white"],
        "fantasy": ["fantasy", "medieval", "armor", "robe", "dress", "gala", "rustic", "traditional", "leather", "fur"],
        "sci-fi": ["sci-fi", "tech", "cyberpunk", "futuristic", "modern", "tactical", "armor", "suit", "latex", "metallic"],
        "cyberpunk": ["cyberpunk", "sci-fi", "tech", "neon", "urban", "street", "leather", "tactical", "edgy"],
        "pool": ["swimwear", "bikini", "swim", "pool", "summer"],
        "beach": ["swimwear", "bikini", "swim", "beach", "summer", "casual", "boho", "shorts", "dress", "linen"],
        "office": ["business", "formal", "office", "work", "suit", "smart casual", "blazer", "shirt", "pencil skirt"],
        "formal": ["formal", "evening", "gala", "dress", "suit", "tuxedo", "gown", "elegant", "luxury", "high fashion", "avant-garde", "runway"],
        "wedding": ["formal", "wedding", "white", "dress", "suit", "gown", "elegant"],
        "urban": ["streetwear", "casual", "skater", "edgy", "denim", "skate", "city", "urban", "graffiti"],
        "domestic": ["casual", "loungewear", "pajamas", "cozy", "knit", "sweater", "shorts", "t-shirt"],
        "vintage": ["vintage", "retro", "1950", "1970", "pinup", "disco", "server", "denim", "classic"],
        "academic": ["academia", "preppy", "glasses", "blazer", "skirt", "tights", "vest", "shirt"]
    }

    # [NEW] Contextual Clash Map: (Scene Tag) -> [Contradictory Interaction/Pose Tags]
    # Penalizes items that imply a completely different physical location.
    CONTEXT_CLASHES = {
         'studio': ['motorcycle', 'bowling', 'street', 'forest', 'beach', 'mountain', 'snow', 'rain', 'vehicle'],
         'indoor': ['landscape', 'scenic', 'horizon', 'sky', 'sunlight', 'heavy rain', 'snowfall'],
         'outdoor': ['classroom', 'kitchen', 'bedroom', 'living room', 'hospital', 'office', 'studio'],
         'athletic': ['formal', 'elegant', 'ballroom', 'gala', 'gown'],
         'formal': ['gym', 'stadium', 'wrestling', 'combat', 'sweat', 'messy', 'gymnastics'],
         'clinical': ['party', 'dance', 'drinking', 'messy', 'dirty', 'gritty']
    }

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
        "adventurous": ["adventure", "outdoorsy", "nature", "active"],
        "passionate": ["intense", "dramatic", "dynamic"],
        "energetic": ["active", "playful", "dynamic", "sport"],
        "bohemian": ["boho", "creative", "alternative", "artistic"],
        "boho": ["bohemian", "creative", "alternative", "artistic"],
        # Content bridges
        "skate": ["skater", "urban", "sport"],
        "skater": ["skate", "urban", "sport"],
        "esports": ["gaming", "tech", "competition"],
        "gaming": ["esports", "tech", "competition"],
        # Cultural Bridges
        "eastern-european": ["cultural", "traditional"],
        "latina": ["cultural", "traditional"],
        "romani": ["cultural", "traditional"],
        "japanese": ["cultural", "traditional", "anime", "manga"],
        "north-african": ["cultural", "traditional"],
        "nordic": ["cultural", "traditional"],
        "mediterranean": ["cultural", "traditional"],
        "african": ["cultural", "traditional"],
        "indian": ["cultural", "traditional"],
        # Bridges for under-represented styles
        "japanese": ["anime", "manga"],
        "modern": ["realistic", "contemporary", "urban"],
        "casual": ["realistic", "everyday", "life"],
        "detailed": ["high definition", "realistic"],
        "portrait": ["photography", "realistic"],
        # Universal Realism (Make Photorealistic the default baseline)
        "female": ["realistic", "high definition", "photography"],
        "male": ["realistic", "high definition", "photography"],
        "urban": ["realistic", "photography", "modern"],
        "nature": ["realistic", "photography"],
        "action": ["dynamic", "motion", "energetic"],
        "calm": ["peaceful", "quiet", "serene", "static"],
        "interior": ["realistic", "photography"],
        "realistic": ["high definition", "photography", "mood:realistic"],
        "formal": ["elegant", "evening", "realistic"],
        "business": ["formal", "professional", "office", "realistic"],
        "streetwear": ["urban", "modern", "casual", "realistic"],
        "candid": ["realistic", "photography"],
        "cinematic": ["realistic", "photography"],
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
            t_lower = t_str.lower()
            if t_lower.startswith("mood:"):
                mood.add(t_str[5:].strip())
            elif t_lower.startswith("block:"):
                blocked.add(t_str[6:].strip().lower()) # Block tags are case-insensitive for matching
            else:
                normal.add(t_str)
                
        return normal, mood, blocked

    def randomize(self, num_characters=None, include_scene=False, include_notes=False, forced_base_prompt=None, candidates=3, match_outfits_prob=0.3):
        """Generate multiple candidates and return the highest scoring one."""
        best_config = None
        best_score = -float('inf')
        
        MAX_RETRIES = 3
        MIN_SCORE_FLOOR = 125
        
        for attempt in range(MAX_RETRIES + 1):
            # Respect the passed candidate count, don't force a floor of 20
            num_to_generate = candidates
            for _ in range(num_to_generate):
                config = self._generate_single_candidate(num_characters, include_scene, include_notes, forced_base_prompt, match_outfits_prob=match_outfits_prob)
                score = self._score_candidate(config)
                
                if score > best_score:
                    best_score = score
                    best_config = config
            
            # If we found a good enough candidate, stop early
            if best_score >= MIN_SCORE_FLOOR:
                break
                
            # Otherwise, loop again (regenerate another batch of candidates)
            # effectively increasing the pool size until we hit the floor or max retries
        
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
            "mismatch_penalty": 0,
            "warnings": []
        }
        
        metadata = config.get("metadata", {})
        
        # Expand moods for broader matching
        raw_moods = metadata.get("moods", [])
        active_moods = self._expand_tags([m.lower() for m in raw_moods])
        
        # Re-derive blocked tags from scene context for validation
        scene_tags = metadata.get("scene_tags", [])
        blocked_tags = set()
        
        if scene_tags:
            # Apply Global SCENE_RESTRICTIONS
            for t in scene_tags:
                t_lower = t.lower()
                if t_lower in self.SCENE_RESTRICTIONS:
                     blocked_tags.update(self.SCENE_RESTRICTIONS[t_lower])
            
            # Check Scene Category (from text or metadata if available, heuristic from scene text?)
            # Ideally passed in metadata, but we can rely on tags usually.
            # scene_text = config.get("scene", "").lower()
            # for key in self.SCENE_RESTRICTIONS:
            #    if key in scene_text: # Simple text check
            #        blocked_tags.update(self.SCENE_RESTRICTIONS[key])

        if not active_moods:
            breakdown["warnings"].append("No active moods/context found for thematic scoring.")

        # 1. Base Structure (+5 each) - Always awarded for being a valid config
        if config.get("scene"): score += 5
        if config.get("notes"): score += 5
            
        # 2. Art Style Alignment (+25 per matching expanded mood)
        base_prompt_name = config.get("base_prompt")
        has_style_match = False

        if base_prompt_name:
            base_style_data = self.base_prompts.get(base_prompt_name, {})
            style_tags = self._get_tags(base_style_data)
            expanded_style_tags = self._expand_tags([t.lower() for t in style_tags])
            
            # Aesthetic Bias: Removed to prevent over-dominance. 
            # Style weights are already handled in base_prompts.md.

            if active_moods:
                style_matches = len(expanded_style_tags.intersection(active_moods))
                if style_matches > 0:
                    has_style_match = True
                points = style_matches * 25
                score += points
                breakdown["style_matches"] = points
            
            # Style-Scene Mismatch Penalty (-100 if style blocks scene theme)
            # AND Check if Style itself is blocked by Scene (-100)
            
            # Check 1: Style is blocked by Scene
            # (e.g. Scene="Medieval", Blocked="Sci-Fi", Style="Cyberpunk")
            if any(t.lower() in blocked_tags for t in style_tags):
                penalty = 100
                score -= penalty
                breakdown["mismatch_penalty"] -= penalty
                breakdown["warnings"].append(f"Style '{base_prompt_name}' is blocked by scene restrictions")

        # 3. Dynamic Thematic Character Alignment
        selected_chars = config.get("selected_characters", [])
        outfit_names = set()
        has_outfit_mood_match = False
        
        for char in selected_chars:
            char_name = char.get("name")
            char_def = self.characters.get(char_name, {})
            outfit_name = char.get("outfit")
            outfit_names.add(outfit_name)
            
            outfits_dict = char_def.get("outfits", {})
            outfit_data = outfits_dict.get(outfit_name)
            
            if outfit_data:
                raw_outfit_tags = self._get_tags(outfit_data)
                
                # Check for Scene-Outfit Mismatch (New Logic)
                # If outfit has a tag that is in blocked_tags -> Penalty
                if blocked_tags:
                    outfit_tags_lower = [t.lower() for t in raw_outfit_tags]
                    if any(bt in outfit_tags_lower for bt in blocked_tags):
                        penalty = 100
                        score -= penalty
                        breakdown["mismatch_penalty"] -= penalty
                        breakdown["warnings"].append(f"Outfit '{outfit_name}' violates scene restrictions")

                # A) Outfit Tags vs Scene Moods (+30 per match)
                if active_moods:
                    tags = self._expand_tags([t.lower() for t in raw_outfit_tags])
                    matches = len(tags.intersection(active_moods))
                    if matches > 0:
                        has_outfit_mood_match = True
                    points = matches * 30
                    score += points
                    breakdown["mood_matches"] += points
            elif not outfit_data and active_moods:
                breakdown["warnings"].append(f"No outfit data found for {char_name}'s {outfit_name}")
            
            # B) Pose Alignment (+10 per category match)
            pose_cat = char.get("pose_category")
            if pose_cat and active_moods:
                if any(m in pose_cat.lower() for m in active_moods):
                    score += 10
                    breakdown["tag_matches"] += 10
                    
            # C) Character Trait Alignment (+5 per match)
            char_tags = self._expand_tags([t.lower() for t in char_def.get("tags", [])])
            char_matches = len(char_tags.intersection(active_moods))
            points = char_matches * 5
            score += points
            breakdown["tag_matches"] += points

        # [NEW] Coherence Bonus (+50)
        # If both Style AND Outfits match the Scene Mood, we have a "Golden" prompt.
        if has_style_match and has_outfit_mood_match:
            score += 50
            breakdown["diversity_bonus"] += 50 # Reusing diversity bucket or just adding to score

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
            breakdown["diversity_bonus"] += points
            
        # 6. Repetitiveness Penalty (-5 per repeated word > 4 chars)
        text_content = f"{config.get('scene', '')} {config.get('notes', '')}".lower()
        clean_text = text_content.replace(',', ' ').replace('.', ' ').replace('!', ' ').replace('?', ' ')
        words = [w for w in clean_text.split() if len(w) > 4]
        seen_words = set()
        penalty = 0
        for w in words:
            if w in seen_words:
                penalty += 5
            seen_words.add(w)
        
        # [NEW] 7. Contextual Clash Penalty (-150 per clash)
        # Prevents "Motorcycles in a Photo Studio" or "Bowling Alley in a Forest"
        clash_penalty = 0
        if scene_tags:
            combined_content_tags = interaction_tags.union(metadata.get("pose_tags", []))
            for st in scene_tags:
                st_lower = st.lower()
                if st_lower in self.CONTEXT_CLASHES:
                    clashes = self.CONTEXT_CLASHES[st_lower]
                    for ct in combined_content_tags:
                        if any(c in ct.lower() for c in clashes):
                            clash_penalty += 150
                            breakdown["mismatch_penalty"] -= 150
                            breakdown["warnings"].append(f"Context Clash: '{st}' scene vs '{ct}' content")

        score -= penalty
        score -= clash_penalty
        breakdown["repetitive_penalty"] = -penalty
            
        metadata["score_breakdown"] = breakdown
        return score

    def _generate_single_candidate(self, num_characters=None, include_scene=False, include_notes=False, forced_base_prompt=None, match_outfits_prob=0.3):
        """Generate a single random prompt configuration using BASE PROMPT FIRST logic."""
        
        # =========================================================================
        # STEP 1: SELECT BASE PROMPT (The "Director")
        # =========================================================================
        
        base_prompt = ""
        context_tags = set()
        blocked_tags = set()
        context_moods = set()

        if forced_base_prompt and self.base_prompts and forced_base_prompt in self.base_prompts:
            base_prompt = forced_base_prompt
        elif self.base_prompts:
            # Weighted Random Selection
            # We parse "weight:N" from tags. Default is 1.0.
            keys = list(self.base_prompts.keys())
            weights = []
            
            for k in keys:
                data = self.base_prompts[k]
                w = 1.0
                if isinstance(data, dict):
                    tags = data.get("tags", [])
                    for t in tags:
                        t_lower = str(t).lower()
                        if t_lower.startswith("weight:"):
                            try:
                                w = float(t_lower.split(":")[1])
                            except ValueError:
                                pass
                weights.append(w)
            
            # Select ONE based on weights
            if keys:
                base_prompt = random.choices(keys, weights=weights, k=1)[0]

        if base_prompt and base_prompt in self.base_prompts:
            bp_data = self.base_prompts[base_prompt]
            if isinstance(bp_data, dict):
                tags = bp_data.get("tags", [])
                _, bp_mood, bp_blocked = self._extract_special_tags(tags)
                context_moods.update(bp_mood)
                blocked_tags.update(bp_blocked)
                context_tags.update(self._expand_tags([t.lower() for t in tags]))

        # =========================================================================
        # STEP 2: SELECT SCENE (Matching Base Prompt)
        # =========================================================================
        
        scene_text = ""
        scene_category = ""
        scene_tags = []

        if include_scene:
            # Filter scenes that match the Context Tags (if any)
            # AND are not blocked.
            compatible_scenes = []
            
            # If no base prompt tags, all scenes are compatible
            search_tags = context_tags if context_tags else None
            
            if search_tags:
                for cat, scenes in self.scenes.items():
                    for name, data in scenes.items():
                        # Check blocked
                        # (Scene tags vs Blocked tags)
                        s_tags_raw = self._get_tags(data)
                        
                        # [FIX] Derive tags from Category if explicit tags missing (Crucial for scenes.md)
                        if not s_tags_raw:
                            s_tags_raw = [cat.lower()]
                            
                        s_tags_expanded = self._expand_tags([t.lower() for t in s_tags_raw])
                        
                        if any(b in s_tags_expanded for b in blocked_tags):
                            continue
                            
                        # Check match
                        # (Scene Tags vs Base Prompt Tags)
                        # We want AT LEAST ONE overlap to consider it "Thematically Consistent"
                        # Only if search_tags are present.
                        if not s_tags_expanded.intersection(search_tags):
                             continue
                            
                        compatible_scenes.append((name, cat, s_tags_raw))
            
            # If no compatible scenes found (or no search tags), fallback to ANY valid scene
            if not compatible_scenes:
                 for cat, scenes in self.scenes.items():
                    for name, data in scenes.items():
                        s_tags_raw = self._get_tags(data)
                        if not s_tags_raw:
                             s_tags_raw = [cat.lower()]
                        
                        if blocked_tags:
                             s_tags_expanded = self._expand_tags([t.lower() for t in s_tags_raw])
                             if any(b in s_tags_expanded for b in blocked_tags):
                                continue
                        compatible_scenes.append((name, cat, s_tags_raw))
            
            if compatible_scenes:
                scene_name, scene_category, scene_tags = random.choice(compatible_scenes)
                # Resolve text
                s_data = self.scenes[scene_category][scene_name]
                if isinstance(s_data, dict):
                    scene_text = s_data.get("description", scene_name)
                else:
                    scene_text = s_data
            
            # Update Context with Scene Tags (Scene adds specificity to the broad Style)
            if scene_tags:
                context_tags.update([t.lower() for t in scene_tags])
                _, s_moods, s_blocked = self._extract_special_tags(scene_tags)
                context_moods.update(s_moods)
                blocked_tags.update(s_blocked)
                
                # Apply Global SCENE_RESTRICTIONS
                for t in scene_tags:
                    t_lower = t.lower()
                    if t_lower in self.SCENE_RESTRICTIONS:
                         blocked_tags.update(self.SCENE_RESTRICTIONS[t_lower])
                
                # Apply Global SCENE_WHITELISTS (Whitelist-First Logic)
                # If a scene matches a whitelist, we strictly enforce it.
                active_whitelist = []
                for t in scene_tags:
                    t_lower = t.lower()
                    if t_lower in self.SCENE_WHITELISTS:
                        active_whitelist.extend(self.SCENE_WHITELISTS[t_lower])
                
                if active_whitelist:
                    # Store for downstream filtering (randomize_character uses this)
                    # We store it in a way that _filter_items_by_tags can use it as a target
                    # But also as a filter against the general pool.
                    context_tags.update([f"whitelist:{w}" for w in active_whitelist])

        # =========================================================================
        # STEP 3: SETUP CHARACTERS
        # =========================================================================
        
        generate_interaction = include_notes
        generate_poses = True
        
        if include_notes and self.interactions and self.poses:
            roll = random.random()
            if roll < 0.15:
                generate_poses = False # Interaction focused
            elif roll < 0.95:
                # Interaction is highly likely if 2+ characters
                pass
            else:
                generate_interaction = False # Pose focused
            
        min_chars_needed = 2 if generate_interaction else 1
        
        if num_characters is None or num_characters == 0:
            lower_bound = max(1, min_chars_needed)
            upper_bound = max(3, lower_bound)
            num_characters = random.randint(lower_bound, min(5, upper_bound))
        else:
            num_characters = max(1, min(num_characters, 5))

        available_chars = list(self.characters.keys())
        if not available_chars:
             return {"selected_characters": [], "base_prompt": base_prompt, "scene": scene_text, "notes": ""}

        num_to_select = min(num_characters, len(available_chars))
        selected_char_names = random.sample(available_chars, num_to_select)
        
        prompt_framing = ""
        framing_chance = 1.0 if not generate_poses else 0.7
        if self.framing and random.random() < framing_chance: 
            prompt_framing = self._select_smart_framing(num_to_select, context_tags=context_tags, scene_category=scene_category)

        # =========================================================================
        # STEP 4: OUTFIT & CHARACTER GENERATION (Strictly Filtered)
        # =========================================================================
        
        # Reduced match_outfits_prob to ensure we don't always get uniform groups
        use_matching_outfits = num_to_select >= 2 and random.random() < 0.2
        matching_outfit = None

        if use_matching_outfits:
            matching_outfit = self._find_matching_outfit(
                selected_char_names, 
                context_tags=context_tags, 
                scene_category=scene_category,
                blocked_tags=blocked_tags
            )

        selected_characters = []
        any_supports_color = False
        
        for char_name in selected_char_names:
            char_data = self._randomize_character(
                char_name, 
                forced_outfit=matching_outfit, 
                include_pose=generate_poses,
                scene_category=scene_category, 
                context_tags=context_tags,
                blocked_tags=blocked_tags
            )
            
            if self._check_color_support(char_name, char_data.get("outfit", "")):
                any_supports_color = True
                
            if random.random() < 0.25:
                char_data["use_signature_color"] = True
            
            if prompt_framing:
                char_data["framing_mode"] = prompt_framing
                
            selected_characters.append(char_data)

        # =========================================================================
        # STEP 5: FINISHING TOUCHES (Colors & Notes)
        # =========================================================================

        color_scheme = "Default (No Scheme)"
        if any_supports_color and self.color_schemes and random.random() > 0.3:
            combined_search_tags = context_tags.union([m.lower() for m in context_moods])
            color_scheme = self._select_smart_color_scheme(combined_search_tags, scene_category)
            
            for char in selected_characters:
                char["color_scheme"] = color_scheme

        notes_text = ""
        interaction_name = "None"
        interaction_tags = []
        if generate_interaction:
            notes_text, interaction_name, interaction_tags = self._generate_random_notes(
                selected_characters, 
                scene_category, 
                context_tags=context_tags,
                context_moods=context_moods, # Added this
                blocked_tags=blocked_tags
            )
        
        if not notes_text and random.random() < 0.1:
            notes_text = "Cinematic lighting, high detail."

        config = {
            "selected_characters": selected_characters,
            "base_prompt": base_prompt,
            "scene": scene_text,
            "notes": notes_text,
            "color_scheme": color_scheme,
            "metadata": {
                "moods": list(context_moods),
                "interaction": interaction_name, # Storing the name here
                "interaction_tags": interaction_tags,
                "scene_tags": scene_tags
            }
        }

        return config

    def _select_smart_framing(self, num_characters, context_tags=None, scene_category=""):
        """Select a framing type appropriate for the number of characters and context."""
        if not self.framing:
            return ""

        all_framings = list(self.framing.keys())
        
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
        
        preferred_framings = []
        if context_tags:
            for tag in context_tags:
                tag_lower = tag.lower()
                for key, targets in tag_map.items():
                    if key in tag_lower:
                        preferred_framings.extend(targets)
                        
        if preferred_framings and random.random() < 0.7:
             valid_preferred = [f for f in preferred_framings if f in self.framing]
             if valid_preferred:
                 return random.choice(valid_preferred)
        
        # Number of Characters Logic
        close_types = [f for f in all_framings if any(x in f.lower() for x in ["close", "portrait", "face", "head"])]
        wide_types = [f for f in all_framings if any(x in f.lower() for x in ["wide", "full", "long", "cinematic", "scenic", "group"])]
        
        if num_characters == 1:
            if close_types and random.random() < 0.4:
                return random.choice(close_types)
        elif num_characters >= 3:
            if wide_types:
                return random.choice(wide_types)
            non_close = [f for f in all_framings if f not in close_types]
            if non_close:
                return random.choice(non_close)
        
        return random.choice(all_framings)

    def _select_smart_color_scheme(self, tags, scene_category):
        """Select a color scheme that matches character tags or scene mood."""
        if not self.color_schemes:
            return "Default (No Scheme)"

        matching_schemes = []
        all_schemes = list(self.color_schemes.keys())
        
        search_terms = list(tags)
        if scene_category:
            search_terms.append(scene_category.lower())

        for scheme in all_schemes:
            scheme_lower = scheme.lower()
            for term in search_terms:
                if term in scheme_lower:
                    matching_schemes.append(scheme)
        
        if matching_schemes and random.random() < 0.5:
            return random.choice(matching_schemes)
            
        return random.choice(all_schemes)

    def _generate_random_scene(self):
        """Generate a random scene description from scene presets.
        
        Returns:
             tuple: (description, category, tags)
        """
        if not self.scenes:
            # Fallback if no scenes loaded
            return "A simple studio background", "Studio", ["studio", "minimalist"]

        # TODO: In future, we could have weighted scene selection here
        # For now, purely random selection of category
        category = random.choice(list(self.scenes.keys()))
        presets = self.scenes[category]
        if presets:
            preset_name = random.choice(list(presets.keys()))
            data = presets[preset_name]
            desc = self._get_description(data)
            tags = self._get_tags(data)
            return desc, category, tags
            
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

        # 2. Whitelist enforcement
        active_whitelists = [t.split(":", 1)[1] for t in context_tags if t.startswith("whitelist:")]
        
        # Find matching available categories
        available_categories = list(categorized_outfits.keys())
        matching_categories = list(preferred_categories)
        
        if active_whitelists:
            # STRICT WHITELIST MODE: Only allow categories that contain whitelisted tags
            strict_candidates = []
            for cat_name, items in categorized_outfits.items():
                if self._filter_items_by_tags(items, active_whitelists, threshold=1):
                    strict_candidates.append(cat_name)
            
            if strict_candidates:
                available_categories = strict_candidates
                matching_categories = [c for c in matching_categories if c in strict_candidates]
                # If no overlap, prioritize a random strict candidate
                if not matching_categories:
                    matching_categories = strict_candidates

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
        
        # Apply Whitelist Filter to items within the category
        items_to_filter = outfits_in_cat
        if active_whitelists:
            whitelisted_item_names = self._filter_items_by_tags(outfits_in_cat, active_whitelists, threshold=1)
            if whitelisted_item_names:
                items_to_filter = {name: outfits_in_cat[name] for name in whitelisted_item_names}

        # Filter for blocked tags locally
        valid_outfits = []
        if items_to_filter:
            for name, data in items_to_filter.items():
                 item_tags = [t.lower() for t in self._get_tags(data)]
                 if not any(bt in item_tags for bt in (blocked_tags or [])):
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

    def _select_smart_pose(self, all_poses, char_tags, scene_category, personality_text="", theme_tags=None, blocked_tags=None):
        """Select a pose category that matches character or scene.
        
        Uses a scoring system to weight categories and items that match the context.
        """
        available_categories = list(all_poses.keys())
        if not available_categories:
            return ""

        context_tags = set(t.lower() for t in char_tags)
        if scene_category:
            context_tags.add(scene_category.lower())
            
        # Scoring map to store weights for each category
        scores = {}
        
        for cat_name, items in all_poses.items():
            cat_lower = cat_name.lower()
            score = 0
            
            # 1. Category Name match (Strong match)
            for t in context_tags:
                if t in cat_lower:
                    score += 5
            
            # 2. Deep tag match (Check items within category)
            # This accounts for tags like (Standing, Confident) in poses
            matched_items = self._filter_items_by_tags(items, context_tags)
            if matched_items:
                score += len(matched_items) * 2
                
            # 3. Theme tag match (VERY Strong - used for forced themes like 'Sport' or 'Medieval')
            if theme_tags:
                theme_tags_lower = {t.lower() for t in theme_tags}
                if any(t in cat_lower for t in theme_tags_lower):
                    score += 15
                
                theme_matched_items = self._filter_items_by_tags(items, theme_tags_lower)
                if theme_matched_items:
                    score += len(theme_matched_items) * 5

            if score > 0:
                scores[cat_name] = score

        # -- BLOCKING LOGIC --
        if blocked_tags and scores:
            for cat_name in list(scores.keys()):
                 cat_val_str = str(all_poses.get(cat_name, "")).lower()
                 if any(bt in cat_name.lower() or bt in cat_val_str for bt in blocked_tags):
                     del scores[cat_name]

        # Final Selection logic
        if not scores:
            # Fallback to random safe category
            if blocked_tags:
                safe_categories = [
                    c for c in available_categories 
                    if not any(bt in c.lower() for bt in blocked_tags)
                ]
                if safe_categories:
                    return random.choice(safe_categories)
            return random.choice(available_categories)

        # Build a weighted list for selection
        # We cap the score to prevent extreme dominance but allow clear preference
        choices = []
        for cat, s in scores.items():
            # Use a non-linear weight (s * s or just s)
            weight = min(s, 50) 
            choices.extend([cat] * weight)
            
        # Boosted smart chance (95% to pick a weighted choice)
        if choices and random.random() < 0.95:
            return random.choice(choices)
        
        return random.choice(available_categories)

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

    def _generate_random_notes(self, selected_characters, scene_category="", context_tags=None, context_moods=None, blocked_tags=None):
        """Generate random interaction template filled with character names.

        Args:
            selected_characters: List of selected character dicts with 'name' key
            scene_category: Category of the scene
            context_tags: Set of context tags (e.g. from characters, scene, base prompt)
            blocked_tags: Set of tags to block (e.g. from scene)

        Returns:
            tuple: (template_text, template_name, template_tags)
        """
        if not self.interactions or not selected_characters:
            # Fallback if no interactions loaded
            notes_options = [
                "Emphasis on natural lighting and soft shadows",
                "High detail and sharp focus",
                "Dynamic composition and movement",
                "Focus on facial expression and emotion",
            ]
            return random.choice(notes_options), "Ambient Notes", []

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
                    # BLOCKING logic (Content Check + Tag Check)
                    if blocked_tags:
                        blocked_lower = {b.lower() for b in blocked_tags}
                        
                        # Check 1: Explicit blocked tags
                        raw_blocked = {b.split(":", 1)[1].lower() for b in blocked_lower if b.startswith("block:")}
                        if tags:
                            template_tags_lower = {t.lower() for t in tags}
                            if template_tags_lower.intersection(raw_blocked):
                                continue
                        
                        # Check 2: Content Blocking (Text search)
                        # Filter blocks that are simple words (not "Block:Tag")
                        simple_blocks = {b for b in blocked_lower if ":" not in b}
                        desc_lower = desc.lower()
                        if any(block_word in desc_lower for block_word in simple_blocks):
                            continue

                    # TAG FILTERING logic
                    if tags:
                        template_tags_lower = {t.lower() for t in tags}
                        
                        # SMART FILTERING logic (Loosened: only filter if we have specific context moods)
                        # If a template has tags but they don't match the scene/prompt moods, we filter it.
                        # BUT we allow generic (no-tag) templates always.
                        if context_moods and template_tags_lower:
                            # Only block if there's ZERO overlap with active moods
                            if not template_tags_lower.intersection(context_tags_lower):
                                continue
                            
                    eligible_templates.append((desc, name, tags))

        if eligible_templates:
            # Pick a random template
            template_text, template_name, template_tags = random.choice(eligible_templates)

            # Fill template with character names
            char_names = [char["name"] for char in selected_characters]
            return fill_template(template_text, char_names), template_name, template_tags
            
        return "", "None", []

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
            
        # [FIX] Expand tags to ensure Aliases (Urban->Realistic) work for Prompt Selection
        context_tags = self._expand_tags(context_tags)
            
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
        
        # [MODIFIED] Flattened Distribution Logic
        # Removed "Drastic Measure" favoring Photorealistic to allow variety.
        # Probability 0.40: Select from matching pool (Context Sensitive)
        # Probability 0.60: Select purely random (Serendipity)
        if matching and random.random() < 0.40:
             return random.choice(matching)
             
        # Fallback to completely random selection from the entire pool
        return random.choice(available_prompts)
