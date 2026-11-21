import random
from core.models import SelectedCharacterConfig
from utils.interaction_helpers import fill_template
from logic.scenarios import ScenarioRegistry
from logic.scoring_heuristics import ScoringEngine

class PromptRandomizer:
    """Generates random character, outfit, and pose combinations."""

    # Composition Modes
    MODE_SOLO = "solo"
    MODE_GROUP_NO_INT = "group_no_interaction"
    MODE_INT_W_POSES = "interaction_with_poses"
    MODE_INT_WO_POSES = "interaction_without_poses"
    
    def __init__(self, characters, base_prompts, poses, scenes=None, interactions=None, color_schemes=None, modifiers=None, framing=None, scene_constraints=None, tag_rules=None, scoring_config=None):
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
            scene_constraints: Dict of scene constraints (allowed/blocked tags)
            tag_rules: Dict containing tag_aliases, tag_groups, and hub_tags
        """
        self.characters = characters
        self.base_prompts = base_prompts
        self.poses = poses
        self.scenes = scenes or {}
        self.interactions = interactions or {}
        self.color_schemes = color_schemes or {}
        self.modifiers = modifiers or {}
        self.framing = framing or {}
        self.scenario_registry = ScenarioRegistry()
        
        # [NEW] Load injected configs
        self.scene_constraints = scene_constraints or {}
        tag_rules = tag_rules or {}
        self.tag_aliases = tag_rules.get("tag_aliases", {})
        self.tag_groups = tag_rules.get("tag_groups", {})
        self.hub_tags = tag_rules.get("hub_tags", [])
        
        # [NEW] Scoring Heuristics
        self.scoring = scoring_config or {
            "weights": {"mood_match": 30, "style_alignment": 25, "diversity_bonus": 10},
            "penalties": {"mismatch": -100, "genre_clash": -1000},
            "thresholds": {"min_score_floor": 250, "mood_diminishing_returns_cutoff": 3, "mood_excess_value": 10}
        }
        self.scorer = ScoringEngine(self)
        
        # [NEW] Pre-compute Tag Transitive Closure
        self._tag_expansion_cache = {}
        self._compute_tag_transitive_closure()
        
        # Pre-compute tags (Phase 1 Optimization)
        self._precompute_tags()
        
        # [NEW] Index Scenes for Hub-driven selection
        self._scene_tag_index = {}
        self._index_scenes()

    def _compute_tag_transitive_closure(self):
        """Pre-calculate the full expansion of every tag in tag_aliases."""
        # Start with direct aliases
        closure = {k.lower(): set(v) for k, v in self.tag_aliases.items()}
        
        # Add Mood: tags to closure
        for k in list(closure.keys()):
            if k.startswith("mood:"):
                mood_name = k[5:].strip()
                if mood_name:
                    closure[k].add(mood_name)

        # Iterate until no more changes
        changed = True
        while changed:
            changed = False
            for tag, expanded in closure.items():
                new_tags = set(expanded)
                for t in expanded:
                    t_lower = str(t).lower()
                    if t_lower in closure:
                        for target in closure[t_lower]:
                            if target not in new_tags:
                                new_tags.add(target)
                                changed = True
                closure[tag] = new_tags
        
        # Lowercase everything for consistency
        self._tag_expansion_cache = {k: {str(t).lower() for t in v} for k, v in closure.items()}

    def _index_scenes(self):
        """Index scenes by their tags for O(1) hub-based lookups."""
        self._scene_tag_index = {}
        if not self.scenes:
            return
            
        for cat_name, presets in self.scenes.items():
            for s_name, s_data in presets.items():
                tags = self._get_tags(s_data)
                for t in tags:
                    t_lower = t.lower()
                    if t_lower not in self._scene_tag_index:
                        self._scene_tag_index[t_lower] = []
                    self._scene_tag_index[t_lower].append((cat_name, s_name, s_data))

    def _precompute_tags(self):
        """Bake expanded tags into internal structures for O(1) lookups."""
        
        # 1. Characters & Outfits
        for char_name, char_data in self.characters.items():
            self._precompute_character_tags(char_name, char_data)

        # 2. Poses (Categories -> Presets)
        for cat, presets in self.poses.items():
             for p_name, p_data in presets.items():
                 if isinstance(p_data, dict):
                     raw_p_tags = set(p_data.get("tags", []))
                     p_data["_expanded_tags"] = self._expand_tags(raw_p_tags)

        # 3. Scenes (Category -> Presets)
        for cat, presets in self.scenes.items():
             for s_name, s_data in presets.items():
                 if isinstance(s_data, dict):
                     raw_s_tags = set(s_data.get("tags", []))
                     s_data["_expanded_tags"] = self._expand_tags(raw_s_tags)

    def _precompute_character_tags(self, char_name, char_data):
        """Expand tags for a single character and their outfits."""
        # Char Tags
        if hasattr(char_data, "tags"):
            raw_tags = set(char_data.tags)
        else:
            raw_tags = set(char_data.get("tags", []))
        
        expanded_char_tags = self._expand_tags(raw_tags)
        if hasattr(char_data, "dict"):
             setattr(char_data, "_expanded_tags", expanded_char_tags)
        else:
             char_data["_expanded_tags"] = expanded_char_tags
        
        # Outfit Tags
        outfits = char_data.outfits if hasattr(char_data, "outfits") else char_data.get("outfits", {})
        for outfit_name, outfit_val in outfits.items():
            if isinstance(outfit_val, dict):
                raw_o_tags = set(outfit_val.get("tags", []))
                outfit_val["_expanded_tags"] = self._expand_tags(raw_o_tags)
            elif hasattr(outfit_val, "tags"):
                setattr(outfit_val, "_expanded_tags", self._expand_tags(set(outfit_val.tags)))

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

    def _expand_tags(self, tags):
        """Expand tags with aliases/groups using pre-computed closure."""
        expanded = set()
        
        for t in tags:
            t_str = str(t)
            t_lower = t_str.lower()
            
            # Clean "Mood:" prefixes and add to expansion
            if t_lower.startswith("mood:"):
                mood_name = t_str[5:].strip()
                expanded.add(mood_name.lower())
                t_lower = mood_name.lower()
            else:
                expanded.add(t_lower)

            # Add pre-computed expansions
            if t_lower in self._tag_expansion_cache:
                expanded.update(self._tag_expansion_cache[t_lower])
                
        return expanded

    def _check_color_support(self, char_name, outfit_name):
        """Check if an outfit supports color substitution or signature colors."""
        char_def = self.characters.get(char_name)
        if not char_def: return False
        
        outfits = char_def.outfits if hasattr(char_def, "outfits") else char_def.get("outfits", {})
        outfit_data = outfits.get(outfit_name, "")
        
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

    def randomize(self, num_characters=None, include_scene=False, include_notes=False, forced_base_prompt=None, candidates=3, match_outfits_prob=0.3, forced_characters=None, forced_scenario=None, character_pool=None):
        """Generate multiple candidates and return the highest scoring one."""
        best_config = None
        best_score = -float('inf')
        
        MAX_RETRIES = 2
        min_floor = self.scoring["thresholds"]["min_score_floor"]
        
        for attempt in range(MAX_RETRIES + 1):
            # With Scenario-First, we need fewer candidates to find a "perfect" match
            num_to_generate = max(3, candidates // 2) if candidates > 5 else candidates
            
            for _ in range(num_to_generate):
                config = self._generate_single_candidate(num_characters, include_scene, include_notes, forced_base_prompt, match_outfits_prob=match_outfits_prob, forced_characters=forced_characters, forced_scenario=forced_scenario, character_pool=character_pool)

                # [NEW] Inject thematic constraints from the Art Style into the metadata
                # This helps trigger penalties for low-quality prompts (e.g. "Default" in Action style)
                if config.get("base_prompt") == "High-Speed Action":
                    meta = config.setdefault("metadata", {})
                    stags = meta.setdefault("scene_tags", [])
                    if "sport" not in stags: stags.append("sport")
                    if "active" not in stags: stags.append("active")

                score = self.scorer.score_candidate(config)
                
                if score > best_score:
                    best_score = score
                    best_config = config
            
            if best_score >= min_floor:
                break
        
        if best_config and "metadata" in best_config:
            best_config["metadata"]["score"] = best_score
            
        return best_config


    def _generate_single_candidate(self, num_characters=None, include_scene=False, include_notes=False, forced_base_prompt=None, match_outfits_prob=0.3, forced_characters=None, forced_scenario=None, character_pool=None):
        """Generate a single random prompt configuration using SCENARIO-FIRST logic."""
        # =========================================================================
        # STEP 0: SELECT HUB & SCENARIO (THE PARTNERSHIP)
        # =========================================================================
        # Pick the scenario first (since it's the authority), then pick a compatible Hub.
        # This ensures the Hub is a thematic guide, not a logic bypass.
        if forced_scenario:
            scenario = self.scenario_registry.scenarios.get(forced_scenario)
            if not scenario:
                print(f"WARNING: Forced scenario '{forced_scenario}' not found. Falling back to random.")
                scenario = self.scenario_registry.get_random()
        else:
            scenario = self.scenario_registry.get_random()
        
        # Identify valid Hubs for this scenario
        scenario_vibes = [v.lower() for v in getattr(scenario, 'vibe_tags', [])]
        scenario_blocked = [b.lower() for b in getattr(scenario, 'blocked_global_tags', [])]
        
        possible_hubs = [h for h in self.hub_tags if h.lower() not in scenario_blocked]
        preferred_hubs = [h for h in possible_hubs if h.lower() in scenario_vibes]
        
        if preferred_hubs:
            hub_tag = random.choice(preferred_hubs)
        elif possible_hubs:
            hub_tag = random.choice(possible_hubs)
        else:
            hub_tag = random.choice(self.hub_tags) # Emergency fallback

        # =========================================================================
        # STEP 2: SELECT SCENE (Driven by Hub)
        # =========================================================================
        scene_desc = ""
        scene_category = ""
        scene_tags = []
        
        if include_scene:
            # 1. Identify Candidate Scenes
            # Strategy: Use pre-computed index for Hub Tag, then filter by scenario requirements.
            
            valid_scenes = []
            
            # Identify Scenario Requirements
            req_scene_tags = set(t.lower() for t in getattr(scenario, 'required_scene_tags', []))
            blocked_global = set(t.lower() for t in getattr(scenario, 'blocked_global_tags', []))
            
            eligible_categories = scenario.allowed_scene_categories
            target_scene_cats = set(eligible_categories) if eligible_categories else None
            
            # HUB PREFERENCE - Use index for speed
            hub_candidates = self._scene_tag_index.get(hub_tag.lower(), [])
            hub_scenes = []
            
            for cat_name, p_name, p_data in hub_candidates:
                # Filter by Category
                if target_scene_cats and cat_name not in target_scene_cats:
                    continue
                    
                tags = self._get_tags(p_data)
                tags_lower = set(t.lower() for t in tags)
                
                # A) Must NOT contain blocked global tags
                if not tags_lower.isdisjoint(blocked_global):
                    continue
                    
                # B) Must satisfy Scenario requirements (Hard Filter)
                if req_scene_tags and not req_scene_tags.issubset(tags_lower):
                    continue
                    
                hub_scenes.append((cat_name, p_name, p_data, tags_lower))
            
            if hub_scenes:
                s_cat, s_name, s_data, _ = random.choice(hub_scenes)
            else:
                # Fallback: Scan categories (only if Hub match failed)
                target_cats = eligible_categories if eligible_categories else self.scenes.keys()
                for cat_name in target_cats:
                    if cat_name in self.scenes:
                        for p_name, p_data in self.scenes[cat_name].items():
                            tags = self._get_tags(p_data)
                            tags_lower = set(t.lower() for t in tags)
                            
                            if not tags_lower.isdisjoint(blocked_global):
                                continue
                            if req_scene_tags and not req_scene_tags.issubset(tags_lower):
                                continue
                            
                            valid_scenes.append((cat_name, p_name, p_data, tags_lower))
                
                if valid_scenes:
                    s_cat, s_name, s_data, _ = random.choice(valid_scenes)
                else:
                    # Emergency Fallback
                    valid_cats = [c for c in self.scenes.keys() if self.scenes[c]]
                    if valid_cats:
                        s_cat = random.choice(valid_cats)
                        s_name = random.choice(list(self.scenes[s_cat].keys()))
                        s_data = self.scenes[s_cat][s_name]
                    else:
                        return None

            scene_category = s_cat
            scene_desc = self._get_description(s_data)
            scene_tags = self._get_tags(s_data)
                
            # [STRICT OVERRIDE] Ensure Hub Tag is in scene_tags for downstream logic
            if hub_tag.lower() not in [t.lower() for t in scene_tags] and scene_desc:
                 scene_tags.append(hub_tag) # Treat it as present for context

        # =========================================================================
        # STEP 3: DETERMINE COMPOSITION MODE (Explicit Logic)
        # =========================================================================
        # 1. Determine Character Count first (needed for Mode decision if not constrained)
        if forced_characters:
            num_characters = len(forced_characters)
        elif num_characters is None:
             # Default random range from scenario
             num_characters = random.randint(scenario.min_characters, scenario.max_characters)
        
        # 2. Decide Mode (Now with Hub-Tag)
        composition_mode, selected_interaction = self._determine_composition_mode(
            scenario, 
            num_characters, 
            include_notes=include_notes,
            hub_tag=hub_tag
        )
        
        # 3. Refine Character Count based on Mode/Interaction
        if composition_mode in (self.MODE_INT_W_POSES, self.MODE_INT_WO_POSES) and selected_interaction:
             # STRICT SCALING: If an interaction is selected, the character count MUST match it.
             # This filters down (or up) to exactly the number of participants defined in the template.
             target_c = selected_interaction.get("min_chars", 2)
             
             if num_characters != target_c:
                 # Override requested count with interaction requirements
                 num_characters = target_c
                 
             # Re-verify availability
             max_avail = len(self.characters.keys())
             if num_characters > max_avail:
                 num_characters = max_avail

        # =========================================================================
        # STEP 4: SELECT STYLE (Contextual - Driven by Hub)
        # =========================================================================
        # Broaden Styles has ensured Hubs cover Styles.
        compatible_styles = []
        for s_name, s_data in self.base_prompts.items():
            # Parse tags from header? (Actually self.base_prompts is dict of name->data)
            # We assume data_loader parsed tags into s_data['tags'] or similar?
            # Data loader for base prompts currently stores raw text. 
            # WAIT: self.base_prompts in `data_loader.py` is simple dict name -> content.
            # The tags are in the KEY (Header). e.g. "Cyberpunk (Tag, Tag)"
            # So s_name contains the tags.
            
            if "(" in s_name and ")" in s_name:
                tag_part = s_name[s_name.rfind("(")+1 : s_name.rfind(")")]
                tags = [t.strip().lower() for t in tag_part.split(",")]
                if hub_tag.lower() in tags:
                    compatible_styles.append(s_name)
                    
        if compatible_styles:
            base_prompt_name = random.choice(compatible_styles)
        else:
            # Fallback to Scenario Default or Random
            base_prompt_name = scenario.default_style_tags[0] if scenario.default_style_tags and scenario.default_style_tags[0] in self.base_prompts else ""
            if not base_prompt_name and self.base_prompts:
                 base_prompt_name = random.choice(list(self.base_prompts.keys()))
        # STEP 5: SELECT CHARACTERS & ASSIGN ROLES (Decision Tree Logic)
        # =========================================================================
        if character_pool:
            available_char_names = [c for c in self.characters.keys() if c in character_pool]
        else:
            available_char_names = list(self.characters.keys())
            
        if not available_char_names:
            return None
            
        if forced_characters:
            # Validate forced characters exist
            char_names = [c for c in forced_characters if c in self.characters]
            
            if len(char_names) < num_characters:
                # Fill the rest from the pool
                remaining = num_characters - len(char_names)
                pool = [c for c in available_char_names if c not in char_names]
                if len(pool) >= remaining:
                     char_names.extend(random.sample(pool, remaining))
                elif pool:
                     char_names.extend(pool)
            elif len(char_names) > num_characters:
                 # Trim
                 char_names = char_names[:num_characters]
        else:
            # Sample names (ensure we don't exceed availability)
            char_count = min(num_characters, len(available_char_names))
            char_names = random.sample(available_char_names, char_count)
            
        selected_characters = []
        
        # Context for roles
        context_tags = set(scenario.vibe_tags)
        context_tags.update(scene_tags)

        existing_schemes = []
        anchor_genre = None

        for i, char_name in enumerate(char_names):
            # 1. Role Assignment
            role = None
            if i < len(scenario.role_slots):
                slot_name = scenario.role_slots[i]
                role = next((r for r in scenario.roles if r.name == slot_name), None)
            if not role:
                role = random.choice(scenario.roles)
            
            # 2. Pose Selection Strategy based on MODE
            # We pass specific constraints to the character randomizer if needed
            # Currently `_randomize_character_with_role` handles pose selection internally.
            # We might need to override it or post-process it if MODE_INT_W_POSES
            
            char_data = self._randomize_character_with_role(
                char_name, 
                role, 
                scene_category=scene_category,
                context_tags=context_tags,
                hub_tag=hub_tag, # Pass Hub Tag for outfit filtering
                existing_schemes=existing_schemes,
                anchor_genre=anchor_genre
            )
            if char_data.color_scheme and char_data.color_scheme != "Default (No Scheme)":
                existing_schemes.append(char_data.color_scheme)
            
            # Set anchor genre from first character to align subsequent characters
            if not anchor_genre:
                char_def = self.characters.get(char_name, {})
                char_outfits = char_def.outfits if hasattr(char_def, "outfits") else (char_def.get("outfits", {}) if isinstance(char_def, dict) else {})
                outfit_data = char_outfits.get(char_data.outfit, {})
                if isinstance(outfit_data, dict):
                    outfit_tags = outfit_data.get("_expanded_tags") or self._expand_tags(self._get_tags(outfit_data))
                    for g_name, g_tags in self.tag_groups.items():
                        if g_name.startswith("GENRE_"):
                            if outfit_tags.intersection({t.lower() for t in g_tags}):
                                anchor_genre = g_name[6:].lower()
                                break
            
            # --- APPLY MODE SPECIFIC POSE LOGIC ---

            # [STRICT SEPARATION] If any Interaction is present, suppress individual character poses 
            # to prevent technical clashes in the generated prompt.
            if composition_mode in (self.MODE_INT_W_POSES, self.MODE_INT_WO_POSES):
                 char_data.pose_preset = ""
                 char_data.pose_category = ""
                 
                 if composition_mode == self.MODE_INT_W_POSES:
                      # MODE_INT_W_POSES uses specific poses for each character as required by the interaction
                      req_poses = selected_interaction.get("required_poses", [])
                      if req_poses and i < len(req_poses):
                          char_data.action_note = req_poses[i]
                      elif req_poses:
                          char_data.action_note = random.choice(req_poses)
                      else:
                          char_data.action_note = ""
                 else:
                      # MODE_INT_WO_POSES is purely text-based (Interactions without Poses)
                      char_data.action_note = ""

            selected_characters.append(char_data)

        # =========================================================================
        # STEP 6: FINALIZE INTERACTION NOTES
        # =========================================================================
        notes_text = ""
        notes_name = "None"
        
        if composition_mode in (self.MODE_INT_W_POSES, self.MODE_INT_WO_POSES) and selected_interaction:
             notes_name = selected_interaction["name"]
             t_text = selected_interaction["text"]
             c_names = [c.name for c in selected_characters]
             notes_text = fill_template(t_text, c_names)
             
        elif composition_mode == self.MODE_GROUP_NO_INT and len(selected_characters) > 1:
             # Generic Fallback if we ended up here (e.g. intended interaction failed)
             # Or just simple group shot instructions
             # For now, leave empty or minor alignment hint?
             pass 
             
        # Use fallback if we failed to generate notes but "needs_notes" was strict?
        # The mode determination handled the "Strict" check, so if we are here, we are good.

        # =========================================================================
        # STEP 6: COMPILE CONFIG
        # =========================================================================
        return {
            "base_prompt": base_prompt_name,
            "scene": scene_desc,
            "scene_category": scene_category,
            "selected_characters": selected_characters,
            "notes": notes_text,
            "notes_name": notes_name,
            "scenario_name": scenario.name,
            "metadata": {
                "scenario": scenario.name,
                "vibe": scenario.vibe_tags,
                "scene_tags": scene_tags,        # FIX: was missing; _score_candidate requires this
                "scene_category": scene_category, # FIX: duplicate at top-level AND in metadata for scorer
                "interaction": notes_name,
                "interaction_tags": set(self._get_tags(selected_interaction)) if selected_interaction else set(),
                "min_chars": selected_interaction.get("min_chars", 0) if selected_interaction else 0,
                "composition_mode": composition_mode,
                "hub_tag": hub_tag
            }
        }

    def _randomize_character_with_role(self, char_name, role, scene_category="", context_tags=None, hub_tag=None, existing_schemes=None, anchor_genre=None):
        """Generate character features strictly matching a role."""
        char_def = self.characters.get(char_name, {})
        # Handle CharacterDetails vs dict
        outfits = char_def.outfits if hasattr(char_def, "outfits") else char_def.get("outfits", {})
        categorized_outfits = char_def.outfits_categorized if hasattr(char_def, "outfits_categorized") else char_def.get("outfits_categorized", {})
        
        # Merge role requirement tags into selection context
        selection_tags = set(context_tags or [])
        selection_tags.update(role.required_tags)
        
        # --- HUB-DRIVEN WHITELISTING ---
        if hub_tag:
             selection_tags.add(f"whitelist:{hub_tag}")
        
        # --- SCENE-BASED GENRE ENFORCEMENT ---
        # Inject scene-based whitelists and blocks into the role selection flow
        local_blocked = set(role.blocked_tags or [])
        
        # 1. Primary Category (Legacy/Broad)
        if scene_category:
            scene_cat_lower = scene_category.lower()
            if scene_cat_lower in self.scene_constraints:
                constraints = self.scene_constraints[scene_cat_lower]
                if "allowed" in constraints:
                    for tag in constraints["allowed"]:
                        selection_tags.add(f"whitelist:{tag}")
            
            if scene_cat_lower in self.scene_constraints:
                constraints = self.scene_constraints[scene_cat_lower]
                if "blocked" in constraints:
                    local_blocked.update(constraints["blocked"])

            # Everyday/Peaceful scenes block overt tactical/combat/spacesuits unless role demands it
            if scene_cat_lower in ("domestic", "casual", "home", "bedroom", "office", "library", "coffee"):
                if not any(t in role.required_tags for t in ["combat", "armor", "weapon", "tactical"]):
                    local_blocked.update(["armor", "weapon", "combat", "spacesuit", "cyber-deck"])

        # 1b. Multi-Character Aesthetic Anchor Alignment
        if anchor_genre:
            if anchor_genre in ("casual", "historical"):
                local_blocked.update(["cyberpunk", "spacesuit", "sci-fi", "scifi", "techwear", "armor"])
            elif anchor_genre == "scifi":
                local_blocked.update(["medieval", "cottagecore", "victorian", "robe", "sword", "shield"])
            elif anchor_genre == "fantasy":
                local_blocked.update(["computer", "laptop", "cyberpunk", "spacesuit", "techwear"])

        # 2. Context Tag Specifics (Precise)
        # Check if any active scene tags trigger a specific whitelist/blocklist
        # e.g. "volleyball" tag triggers the "volleyball" whitelist
        if context_tags:
            # Extract explicit blocks from scene tags (e.g. block:MMA)
            _, _, scene_blocks = self._extract_special_tags(context_tags)
            local_blocked.update(scene_blocks)
            
            for tag in context_tags:
                t_lower = tag.lower()
                if t_lower in self.scene_constraints:
                    constraints_inner = self.scene_constraints[t_lower]
                    if "allowed" in constraints_inner:
                        for w_tag in constraints_inner["allowed"]:
                            selection_tags.add(f"whitelist:{w_tag}")
                
                if t_lower in self.scene_constraints:
                    constraints = self.scene_constraints[t_lower]
                    if "blocked" in constraints:
                        local_blocked.update(constraints["blocked"])

        # Decision Tree: Strict Outfit Whitelisting
        if role.allowed_outfit_categories:
            for cat in role.allowed_outfit_categories:
                selection_tags.add(f"whitelist:{cat}")
            
        # Decision Tree: Strict Pose Whitelisting
        if role.allowed_pose_categories:
            for cat in role.allowed_pose_categories:
                selection_tags.add(f"pose_whitelist:{cat}")
            
        # 1. Select Outfit matching Role
        outfit_name = self._select_smart_outfit(
            outfits, 
            categorized_outfits, 
            selection_tags, 
            scene_category, 
            blocked_tags=local_blocked
        )
        
        # 2. Select Pose matching Role
        pose_context = selection_tags.union(role.preferred_poses)
        pose_category = self._select_smart_pose(
            self.poses, 
            pose_context, 
            scene_category, 
            blocked_tags=local_blocked
        )
        
        pose_presets = self.poses.get(pose_category, {})
        pose_preset = random.choice(list(pose_presets.keys())) if pose_presets else ""

        # 3. Traits
        # Handle CharacterDetails vs dict
        available_traits = char_def.traits if hasattr(char_def, "traits") else char_def.get("traits", {})
        selected_traits = [random.choice(list(available_traits.keys()))] if available_traits and random.random() < 0.9 else []

        # 4. Color Scheme (especially important for sports, contrast, and visual punch)
        outfit_tags = self._get_tags(outfits.get(outfit_name, {}))
        color_scheme = self._select_smart_color_scheme(
            outfit_tags,
            scene_category,
            char_name=char_name,
            existing_schemes=existing_schemes,
            context_tags=context_tags,
        )

        # 4b. Signature Color Integration
        use_sig = False
        outfit_obj = outfits.get(outfit_name, "")
        outfit_str = str(outfit_obj) if not isinstance(outfit_obj, dict) else " ".join(str(v) for v in outfit_obj.values() if isinstance(v, str))
        sig_color = getattr(char_def, "signature_color", None) if hasattr(char_def, "signature_color") else (char_def.get("signature_color") if isinstance(char_def, dict) else None)

        if sig_color:
            if "{signature_color}" in outfit_str or "(signature)" in outfit_str:
                use_sig = True
            elif random.random() < 0.35:
                use_sig = True
        
        # 5. Outfit Modifiers/Traits
        outfit_traits = []
        outfit_obj = outfits.get(outfit_name)
        if isinstance(outfit_obj, dict):
            outfit_data = outfit_obj
            if "modifiers" in outfit_data and outfit_data["modifiers"]:
                available_modifiers = list(outfit_data["modifiers"].keys())
                # 30% chance to apply a modifier
                if available_modifiers and random.random() < 0.3:
                    outfit_traits = [random.choice(available_modifiers)]

        return SelectedCharacterConfig(
            name=char_name,
            outfit=outfit_name,
            pose_category=pose_category,
            pose_preset=pose_preset,
            character_traits=selected_traits,
            color_scheme=color_scheme,
            use_signature_color=use_sig,
            outfit_traits=outfit_traits,
            action_note="",
            _expanded=True
        )

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

    def _select_smart_color_scheme(
        self,
        tags,
        scene_category="",
        char_name="",
        existing_schemes=None,
        context_tags=None,
    ):
        """Select a color scheme that matches character tags, scene mood, or provides smart contrast."""
        if not self.color_schemes:
            return "Default (No Scheme)"

        all_schemes = list(self.color_schemes.keys())
        existing = existing_schemes or []

        # 1. First priority: Exact or substring match in tags or scene_category (preserves test_smart_color_scheme)
        matching_schemes = []
        search_terms = list(tags)
        if scene_category:
            search_terms.append(scene_category.lower())

        for scheme in all_schemes:
            scheme_lower = scheme.lower()
            for term in search_terms:
                if term and term.lower() in scheme_lower:
                    matching_schemes.append(scheme)

        if matching_schemes and random.random() < 0.6:
            filtered = [s for s in matching_schemes if s not in existing]
            return random.choice(filtered if filtered else matching_schemes)

        # 2. Curated contrast harmonies & mood pairings (e.g. Maroon & Khaki, Olive & Rust)
        contrast_harmonies = [
            "Maroon & Khaki", "Olive & Rust", "Navy & Amber",
            "Charcoal & Mustard", "Emerald & Bronze", "Sage & Terracotta",
            "Midnight & Crimson"
        ]
        available_harmonies = [s for s in contrast_harmonies if s in self.color_schemes]

        # Check scene/context mood for thematic pairing
        all_context = set(t.lower() for t in (context_tags or []))
        if scene_category:
            all_context.add(scene_category.lower())

        dark_dramatic = any(w in all_context for w in ["night", "noir", "neon", "cyberpunk", "dark", "dramatic", "club", "bar", "action"])
        nature_outdoor = any(w in all_context for w in ["nature", "forest", "park", "garden", "outdoor", "beach", "mountain", "spring", "summer"])
        casual_urban = any(w in all_context for w in ["casual", "cafe", "coffee", "street", "city", "campus", "library", "school", "office"])

        thematic_pool = []
        if dark_dramatic:
            thematic_pool = [s for s in ["Midnight & Crimson", "Charcoal & Mustard", "Navy & Amber", "The Neon Knights", "The Brick City"] if s in self.color_schemes]
        elif nature_outdoor:
            thematic_pool = [s for s in ["Olive & Rust", "Emerald & Bronze", "Sage & Terracotta", "The Forest Keepers", "The Summit"] if s in self.color_schemes]
        elif casual_urban:
            thematic_pool = [s for s in ["Maroon & Khaki", "Navy & Amber", "Sage & Terracotta", "Charcoal & Mustard"] if s in self.color_schemes]

        filtered_thematic = [s for s in thematic_pool if s not in existing]
        candidate_thematic = filtered_thematic if filtered_thematic else thematic_pool
        if candidate_thematic and random.random() < 0.7:
            return random.choice(candidate_thematic)

        # 3. If multi-character, prioritize an unused contrast harmony
        unused_harmonies = [s for s in available_harmonies if s not in existing]
        if unused_harmonies and random.random() < 0.6:
            return random.choice(unused_harmonies)

        # Fallback pool: exclude already used schemes if possible
        pool = [s for s in all_schemes if s not in existing] if existing else all_schemes
        return random.choice(pool if pool else all_schemes)

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
            else:
                # All poses in this category were blocked — broaden to any safe category
                for fallback_cat, fallback_items in self.poses.items():
                    if fallback_cat == pose_category:
                        continue  # Skip the one we already tried
                    fb_names = [
                        pn for pn in fallback_items.keys()
                        if not blocked_tags or not any(
                            bt in (t.lower() for t in self._get_tags(fallback_items[pn]))
                            for bt in blocked_tags
                        )
                    ]
                    if fb_names:
                        pose_category = fallback_cat
                        pose_preset = random.choice(fb_names)
                        break

        # Random Character Traits (e.g. Glasses, Freckles)
        # 90% chance to include a trait if available
        selected_character_traits = []
        available_traits = char_def.get("traits", {})
        if available_traits and random.random() < 0.9:
            # Pick one random trait
            selected_character_traits.append(random.choice(list(available_traits.keys())))

        return SelectedCharacterConfig(
            name=char_name,
            outfit=outfit_name,
            outfit_traits=outfit_traits,
            character_traits=selected_character_traits,
            custom_modifiers=local_modifiers,
            pose_category=pose_category,
            pose_preset=pose_preset,
            framing_mode="Portrait", 
            action_note="",
            _expanded=True
        )

    def _select_smart_outfit(self, all_outfits, categorized_outfits, char_tags, scene_category, blocked_tags=None):
        """Select an outfit using weighted constraints (Filter -> Select)."""
        # [FIX] Properly parse blocked tags to remove 'block:' prefix
        raw_blocked = blocked_tags or []
        parsed_blocked = set()
        for b in raw_blocked:
             if b.lower().startswith("block:"):
                 parsed_blocked.add(b.split(":", 1)[1].lower())
             else:
                 parsed_blocked.add(b.lower())
                 
        blocked = self._expand_tags(list(parsed_blocked))
        
        context_tags = set(t.lower() for t in char_tags)
        if scene_category:
            context_tags.add(scene_category.lower())

        # Extract strict whitelists (e.g., "whitelist:Activewear")
        whitelists = {t.split(":", 1)[1].lower() for t in context_tags if t.startswith("whitelist:")}
        
        candidates = [] # List of (name, weight)

        # Helper to get tags efficiently
        def get_item_tags(item_data):
            if isinstance(item_data, dict):
                # Use pre-computed tags if available (Phase 1)
                return item_data.get("_expanded_tags") or self._expand_tags(item_data.get("tags", []))
            return set()

        # Iterate through categories to handle category-level logic
        source_categories = categorized_outfits if categorized_outfits else {"Uncategorized": all_outfits}

        for cat_name, items in source_categories.items():
            cat_lower = cat_name.lower()
            
            # 1. Whitelist Check
            if whitelists:
                # If whitelist active, category MUST match one of the whitelists
                # OR contain items that match? Strict interpretation: Category Name Match.
                if not any(wl in cat_lower for wl in whitelists):
                    continue

            # 2. Category Blocking
            # (e.g. Block "Swimwear" category in "Office")
            # We check if the category name itself implies a blocked tag
            # This is a heuristic: "Swimwear" category matches "swimwear" tag.
            if any(b in cat_lower for b in blocked):
                continue
            
            # Category Boost Score
            cat_boost = 1.0
            if any(t in cat_lower for t in context_tags):
                cat_boost = 5.0

            for name, data in items.items():
                item_tags = get_item_tags(data)
                
                # --- HARD CONSTRAINTS ---
                if not item_tags.isdisjoint(blocked):
                    continue
                
                # --- SCORING ---
                base_score = 10.0 * cat_boost
                
                # Tag Overlap Bonus
                matches = len(item_tags.intersection(context_tags))
                token_bonus = matches * 15.0
                
                final_score = base_score + token_bonus
                candidates.append((name, final_score))

        # Parsing Fallback: If no candidates found (too restrictive?), try relaxing constraints
        # Parsing Fallback: If no candidates found...
        if not candidates and whitelists:
             # RETRY PHASE 2: Item-Level Whitelist (Ignore Category Structure)
             # Maybe the "Sports" outfit is miscategorized in "Casual"?
             for cat_name, items in source_categories.items():
                 cat_lower = cat_name.lower()
                 if any(b in cat_lower for b in blocked): continue
                 
                 for name, data in items.items():
                     item_tags = get_item_tags(data)
                     if not item_tags.isdisjoint(blocked): continue
                     
                     # Check if Item Tags match any Whitelist term
                     if not item_tags.isdisjoint(whitelists):
                         # Found a match via tags!
                         final_score = 5.0 # Lower scope
                         candidates.append((name, final_score))
            
             if candidates:
                  # Found items via direct tag match, use them!
                  population, weights = zip(*candidates)
                  return random.choices(population, weights=weights, k=1)[0]

             # RETRY PHASE 3: Drop Whitelist (Total Failure)
             # IMPORTANT: Strip "whitelist:" tags from context to prevent infinite recursion
             clean_tags = [t for t in char_tags if not t.lower().startswith("whitelist:")]
             return self._select_smart_outfit(all_outfits, categorized_outfits, clean_tags, scene_category, blocked_tags=blocked_tags)

        if not candidates:
             # Last resort: Any unblocked outfit from 'all_outfits'
             fallback_opts = []
             for name, data in all_outfits.items():
                 item_tags = get_item_tags(data)
                 if item_tags.isdisjoint(blocked):
                     fallback_opts.append(name)
             if fallback_opts:
                 return random.choice(fallback_opts)
             # If literally everything is blocked, return random (User can see the clash)
             return random.choice(list(all_outfits.keys()))

        # Weighted Selection
        population, weights = zip(*candidates)
        return random.choices(population, weights=weights, k=1)[0]

    def _select_smart_pose(self, all_poses, char_tags, scene_category, personality_text="", theme_tags=None, blocked_tags=None):
        """Select a pose category using weighted constraints."""
        blocked = self._expand_tags(blocked_tags or [])
        
        context_tags = set(t.lower() for t in char_tags)
        if scene_category:
            context_tags.add(scene_category.lower())
            
        whitelists = {t.split(":", 1)[1].lower() for t in context_tags if t.startswith("pose_whitelist:")}
        
        candidates = []

        for cat_name, items in all_poses.items():
            cat_lower = cat_name.lower()

            # 1. Whitelist Check
            if whitelists:
                # Category MUST match one of the whitelists
                if not any(wl in cat_lower for wl in whitelists):
                    continue

            # 2. Block Check (Category Level)
            if any(b in cat_lower for b in blocked):
                continue

            # Base Score
            score = 10.0

            # Category Name Match
            if any(t in cat_lower for t in context_tags):
                score += 20.0
            
            # Theme Tag Forced Match
            if theme_tags:
                theme_tags_lower = {t.lower() for t in theme_tags}
                if any(t in cat_lower for t in theme_tags_lower):
                    score += 50.0

            # Deep Item Check (Bonus if category contains highly relevant poses)
            # Use a sample or check ratio to keep it fast
            relevant_items = 0
            
            # Helper to get tags efficiently (Same as outfit selector)
            def get_pose_tags(p_data):
                if isinstance(p_data, dict):
                     return p_data.get("_expanded_tags") or self._expand_tags(p_data.get("tags", []))
                return set()

            # Environment Requirements Check
            # Prevent "Bed" poses in "Boat" scenes, etc.
            REQUISITES = {
                "bed": ["bedroom", "indoors", "hotel", "asylum", "studio", "hospital"],
                "desk": ["office", "indoors", "library", "studio", "school"],
                "chair": ["indoors", "office", "cafe", "studio", "restaurant"],
                "sofa": ["indoors", "living room", "studio", "lounge"]
            }

            for p_name, p_data in items.items():
                 p_tags = get_pose_tags(p_data)
                 if not p_tags.isdisjoint(blocked):
                     continue # Item is blocked, don't count it
                 
                 # Check requisites
                 clash_found = False
                 for req_obj, allowed_scenes in REQUISITES.items():
                     if req_obj in p_tags:
                         # Pose requires this object. Does the scene (or its category) support it?
                         scene_match = any(s in scene_category.lower() or s in context_tags for s in allowed_scenes)
                         if not scene_match:
                             clash_found = True
                             break
                 
                 if clash_found:
                     continue # Skip this pose item as it doesn't fit the environment
                 
                 if not p_tags.isdisjoint(context_tags):
                     relevant_items += 1
            
            score += (relevant_items * 5.0) # Increased bonus for relevant items
            
            candidates.append((cat_name, score))

        if not candidates:
            # Fallback: Return random (safe) from all available
            safe_categories = [
                c for c in all_poses.keys() 
                if not any(bt in c.lower() for bt in blocked)
            ]
            if safe_categories:
                return random.choice(safe_categories)
            return random.choice(list(all_poses.keys()))

        population, weights = zip(*candidates)
        return random.choices(population, weights=weights, k=1)[0]

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
            char_outfits = char_def.outfits if hasattr(char_def, "outfits") else char_def.get("outfits", {})
            outfit_sets.append(set(char_outfits.keys()))

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
            first_char_outfits = first_char.outfits if hasattr(first_char, "outfits") else first_char.get("outfits", {})
            
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

    def _generate_random_notes(self, selected_characters, scene_category="", context_tags=None, context_moods=None, blocked_tags=None, exclusive=False):
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
            return {"name": "Ambient Notes", "text": random.choice(notes_options), "min_chars": 1, "tags": []}, "Ambient Notes", []

        num_chars = len(selected_characters)
        
        # Collect all eligible templates across all categories
        eligible_templates = []
        fallback_templates = []
        
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
                    is_strict_match = False
                    
                    if tags:
                        template_tags_lower = {t.lower() for t in tags}
                        
                        # STRICT SCENARIO MATCHING
                        # If we have scenario vibes, the interaction MUST share at least one tag.
                        if context_moods:
                            expanded_vibes = self._expand_tags([v.lower() for v in context_moods])
                            if template_tags_lower.intersection(expanded_vibes):
                                is_strict_match = True
                        else:
                            is_strict_match = True
                    else:
                        # No tags -> matched unless strict logic requires tags (which it doesn't usually)
                        is_strict_match = True

                    if is_strict_match:
                        eligible_templates.append((desc, name, tags))
                    elif not exclusive:
                        # Allow as fallback
                        fallback_templates.append((desc, name, tags))

        if not eligible_templates:
            if exclusive:
                # If we found nothing in exclusive mode, return empty instead of picking a random backup
                return "", "None", []
            # Use fallback
            eligible_templates = fallback_templates

        if eligible_templates:
            # Pick a random template
            template_text, template_name, template_tags = random.choice(eligible_templates)

            # Fill template with character names
            char_names = [char.name if hasattr(char, "name") else char.get("name") for char in selected_characters]
            return fill_template(template_text, char_names), template_name, template_tags
            
        # If no eligible templates found (due to strict exclusive mode or blocking)
        # Return a safe, generic fallback instead of None
        fallback_options = [
            "Cinematic composition with focus on character expression",
            "Atmospheric lighting emphasizing the relationship dynamics",
            "Detailed capture of the moment and setting",
            "High contrast dramatic framing",
            "Natural and candid interaction capture"
        ]
        return random.choice(fallback_options), "Generic (Fallback)", ["neutral"]

    def _select_interaction_template(self, scene_category="", context_tags=None, context_moods=None, blocked_tags=None, exclusive=False, hub_tag=None):
        """Select an interaction template BEFORE character selection.
        
        Args:
            scene_category: Category of the scene
            context_tags: Set of context tags
            context_moods: List of mood tags from scenario
            blocked_tags: Set of tags to block
            exclusive: Whether to strictly enforce context matching
            
        Returns:
            dict: {
                "name": str,
                "text": str,
                "tags": list,
                "min_chars": int,
                "required_poses": list (optional)
            } or None
        """
        if not self.interactions:
            return None

        # Collect eligible templates
        eligible_templates = []
        fallback_templates = []
        
        # Pre-process context
        context_tags_lower = {t.lower() for t in context_tags} if context_tags else set()
        expanded_vibes = set()
        if context_moods:
            expanded_vibes = self._expand_tags([v.lower() for v in context_moods])

        for category, templates in self.interactions.items():
            for name, data in templates.items():
                # Normalize data format
                tags = []
                desc = ""
                min_chars = 2 # Default to 2 for interactions
                
                if isinstance(data, dict):
                    desc = data.get("description", "")
                    min_chars = data.get("min_chars", 1)
                    tags = data.get("tags", [])
                else:
                    desc = data
                    # Legacy string format assumes min 2 for interactions usually, 
                    # but let's be safe and say 1 if unknown, though interactions implying plural need 2.
                    # For now, safe default.
                    min_chars = 1
                
                # Minimum characters logic: 
                # Ideally, interactions are for >1 person. 
                # If an interaction specifies min_chars=1, it is safe for 1 person (like "Walking").
                
                # --- FILTERING LOGIC ---
            
                # 1. Blocking (Strict Blacklist)
                # Check for hard scene constraints
                if scene_category.lower() in self.scene_constraints:
                    constraints = self.scene_constraints[scene_category.lower()]
                    restricted_tags = constraints.get("blocked", set())
                else:
                    restricted_tags = set()
                    
                if tags:
                        template_tags_lower = {t.lower() for t in tags}
                        if template_tags_lower.intersection(restricted_tags):
                            continue
                
                # Global tag blocks
                if blocked_tags:
                    blocked_lower = {b.lower() for b in blocked_tags}
                    raw_blocked = {b.split(":", 1)[1].lower() for b in blocked_lower if b.startswith("block:")}
                    if tags:
                        template_tags_lower = {t.lower() for t in tags}
                        if template_tags_lower.intersection(raw_blocked):
                            continue
                    simple_blocks = {b for b in blocked_lower if ":" not in b}
                    desc_lower = desc.lower()
                    if any(block_word in desc_lower for block_word in simple_blocks):
                        continue

                # 2. Hard Whitelisting (Strict Whitelist)
                # If a scene has a whitelist (e.g. gym, bowling), MUST match at least one tag.
                if scene_category.lower() in self.scene_constraints:
                    constraints = self.scene_constraints[scene_category.lower()]
                    if "allowed" in constraints:
                        whitelist = set(constraints["allowed"])
                        if tags:
                            template_tags_lower = {t.lower() for t in tags}
                            if not template_tags_lower.intersection(whitelist):
                                continue # Strict filter: no match, no selection
                    else:
                        # Untagged items are only allowed if the whitelist is not "exclusive"
                        # But for strict consistency, we skip untagged items in whitelisted scenes.
                        continue

                # 3. Context / Vibe / Hub Matching
                is_strict_match = False
                if tags:
                    template_tags_lower = {t.lower() for t in tags}
                    
                    # Hub Match (Primary thematic guide)
                    if hub_tag and hub_tag.lower() in template_tags_lower:
                        is_strict_match = True
                    
                    # Scenario Vibe Match (Partnership guide)
                    elif context_moods and template_tags_lower.intersection(expanded_vibes):
                        is_strict_match = True
                        
                    elif not hub_tag and not context_moods:
                        is_strict_match = True
                else:
                    # Untagged templates are generic matches
                    is_strict_match = True

                # Determine actual placeholder count from text
                placeholders = []
                import re
                p_matches = re.findall(r"\{char(\d+)\}", desc)
                if p_matches:
                    placeholders = [int(m) for m in p_matches]
                    min_chars = max(placeholders) if placeholders else 1
                else:
                    # Fallback if no placeholders found (legacy or special format)
                    min_chars = min_chars

                template_obj = {
                    "name": name,
                    "text": desc,
                    "tags": tags,
                    "min_chars": min_chars,
                    "required_poses": data.get("required_poses", []) if isinstance(data, dict) else []
                }

                if is_strict_match:
                    eligible_templates.append(template_obj)
                elif not exclusive:
                    # [THEMATIC PROTECTION]
                    # Only allow fallback if it DOES NOT contain a "Strong Genre Tag" that is missing from context.
                    # This prevents "Sport" interactions appearing in "Fantasy" scenes just because they weren't explicitly blocked.
                    
                    # Construct strong genre tags from loaded tag groups
                    strong_genre_tags = set()
                    for group_name, tags in self.tag_groups.items():
                        if group_name.startswith("GENRE_"):
                            strong_genre_tags.update([t.lower() for t in tags])
                    
                    if not strong_genre_tags:
                        # Fallback if config is missing
                        strong_genre_tags = {
                            "sport", "basketball", "baseball", "football", "soccer", "volleyball", 
                            "tennis", "mma", "boxing", "wrestling", "gym", "athlete", 
                            "fantasy", "medieval", "magic", "dragon", "wizard",
                            "sci-fi", "cyberpunk", "futuristic", "robot", "tech",
                            "noir", "detective", "vintage", "retro", "western"
                        }
                    
                    template_tags_lower = {t.lower() for t in tags}
                    has_strong_clash = False
                    
                    # If template has a strong tag, it MUST be allowed by context (hub, mood, or whitelist)
                    # We check if any of the template's strong tags are NOT in the current context/hub.
                    
                    # 1. Gather all allowed context tags (Hub + Moods)
                    allowed_concepts = set()
                    if hub_tag: allowed_concepts.add(hub_tag.lower())
                    if context_moods: allowed_concepts.update(self._expand_tags([m.lower() for m in context_moods]))
                    
                    # 2. Check overlap
                    # If interaction has a strong tag, and that tag is NOT in allowed_concepts, it's a clash.
                    for t in template_tags_lower:
                        if t in strong_genre_tags:
                            # Is this strong tag allowed?
                            # We use expanded matching (e.g. if context is "Combat", "MMA" might be allowed? 
                            # But here we are just checking if the tag itself is present in the allowed set)
                            # Let's be strict: if the tag isn't explicitly in the allowed context, reject it.
                            if t not in allowed_concepts:
                                # Special Case: "Sport" covers specific sports
                                if t in ["basketball", "baseball", "football", "soccer", "volleyball", "tennis", "mma", "boxing", "wrestling", "gym"]:
                                    if "sport" in allowed_concepts or "athletic" in allowed_concepts:
                                        continue
                                
                                has_strong_clash = True
                                break
                    
                    if not has_strong_clash:
                        fallback_templates.append(template_obj)

        selected = None
        if eligible_templates:
            selected = random.choice(eligible_templates)
        elif fallback_templates and not exclusive:
            selected = random.choice(fallback_templates)
            
        return selected

    def _determine_composition_mode(self, scenario, num_characters, include_notes=False, hub_tag=None):
        """Determine the composition strategy based on constraints.
        
        Args:
           scenario: Selected Scenario object
           num_characters: Intended number of characters (if known/fixed)
           include_notes: Boolean flag for interaction intention
           
        Returns:
           tuple: (CompositionMode, interaction_template_or_None)
        """
        # 1. SOLO MODE
        if num_characters == 1:
            return self.MODE_SOLO, None
            
        # 2. Check Intention
        needs_interaction = include_notes or scenario.force_interaction
        
        # [USER REQUEST] Balance Adjustment: 20% chance to skip global interaction 
        # even if requested, to allow more individual-pose group variety.
        if needs_interaction and not scenario.force_interaction:
            if random.random() < 0.2:
                return self.MODE_GROUP_NO_INT, None

        if not needs_interaction:
            # If we are a group but don't need interaction, default to Group Poses
            return self.MODE_GROUP_NO_INT, None

        # 3. Attempt to Select Interaction
        # We need context tags for selection, which usually come from Scene/Scenario.
        # Ideally this is called with context, but for now we'll use Scenario's default context.
        context_tags = set(scenario.vibe_tags) 
        
        selected_interaction = self._select_interaction_template(
            scene_category="", # Generic selection for now
            context_tags=context_tags,
            context_moods=scenario.vibe_tags,
            exclusive=scenario.exclusive_notes,
            hub_tag=hub_tag
        )
        
        if not selected_interaction:
            if scenario.exclusive_notes:
                # If we MUST have an interaction but found none, what do we do?
                # For safety, fallback to Group No Int (or generic fallback later)
                return self.MODE_GROUP_NO_INT, None
            else:
                return self.MODE_GROUP_NO_INT, None
        
        # 4. Determine Interaction Type (Poses vs No Poses)
        # Check if interaction has pose constraints
        # Since our current data might not support 'required_poses', we assume NO POSES unless specified.
        # Future: if selected_interaction.get("required_poses"): return MODE_INT_W_POSES
        
        # For now, if we have an interaction, we treat it as WITH POSES if the text implies it,
        # otherwise usually characters do their own thing. 
        # Actually, let's stick to the plan:
        # If 'required_poses' is present -> INT_W_POSES
        # Else -> INT_INT_WO_POSES
        
        # [USER REQUEST] Balance Adjustment: Precise Interactions (with required_poses)
        # should be relatively rare (30% activation). 
        # Otherwise, fallback to MODE_INT_WO_POSES which allows individual character poses.
        if selected_interaction.get("required_poses"):
             if random.random() < 0.3:
                 return self.MODE_INT_W_POSES, selected_interaction
             else:
                 return self.MODE_INT_WO_POSES, selected_interaction
             
        return self.MODE_INT_WO_POSES, selected_interaction

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
        
        # Context-driven probability: the more matching styles found, the more confident we are
        # that context is strong and we should honour it.
        # 0 matches  → 0% (pure random)
        # 1 match    → 60%
        # 2 matches  → 75%
        # 3+ matches → 85%
        if not matching:
            match_prob = 0.0
        elif len(matching) == 1:
            match_prob = 0.60
        elif len(matching) == 2:
            match_prob = 0.75
        else:
            match_prob = 0.85

        if matching and random.random() < match_prob:
             return random.choice(matching)
             
        # Fallback to completely random selection from the entire pool
        return random.choice(available_prompts)