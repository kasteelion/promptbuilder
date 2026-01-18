import random
from utils.interaction_helpers import fill_template
from logic.scenarios import ScenarioRegistry, Scenario, Role

class PromptRandomizer:
    """Generates random character, outfit, and pose combinations."""
    
    # DEFINING STONG HUB TAGS (Verified via Connectivity Audit)
    HUB_TAGS = [
        "Casual", "Urban", "Noir", "Sport", "Fantasy", "Sci-Fi", "Retro", 
        "Intimate", "Social", "Work", "Action", "Cyberpunk", "Vintage",
        "Basketball", "Football", "MMA", "Volleyball", "School", "Home", "Magic"
    ]
    
    # --- Composition Modes ---
    MODE_SOLO = "SOLO"                      # 1 Character, Pose focused
    MODE_INT_W_POSES = "INT_W_POSES"        # Interaction sets Poses (e.g. Fight)
    MODE_INT_WO_POSES = "INT_WO_POSES"      # Interaction sets Vibe, Poses Random
    MODE_GROUP_NO_INT = "GROUP_NO_INT"      # Group shot, Independent Poses

    # Centralized Tag Groups for constraint logic
    # REDUCED: From 20+ groups to 8 core groups (removed redundant and sport-specific)
    TAG_GROUPS = {
        # Essential constraint groups (kept)
        "EXPOSED_SKIN": {"swimwear", "bikini", "lingerie", "crop top", "shorts", "sleeveless", "undressing", "naked"},
        "ARMOR_WEAPON": {"armor", "weapon", "shield", "sword", "combat", "tactical", "gun", "rifle"},
        "FORMAL": {"formal", "evening", "gala", "suit", "tuxedo", "gown", "dress", "business"},
        "WINTER": {"winter", "snow", "ski", "heavy coat", "scarf", "coat", "jacket", "hoodie"},
        "FOOTWEAR": {"shoes", "boots", "heels", "sandals"},
        
        # Genre firewalls (critical for preventing clashes)
        "GENRE_FANTASY": {"fantasy", "medieval", "magic", "mystical", "castle", "knight", "sword", "shield", "robe", "dnd", "spell", "arcane", "mythology", "dragon", "lair", "dungeon", "temple", "quest"},
        "GENRE_MODERN": {"modern", "tech", "computer", "phone", "laptop", "car", "city", "office", "urban", "neon", "cyberpunk"},
        
        # Sport group (consolidated - no longer need per-sport groups)
        "GENRE_SPORT": {"sport", "athletic", "gym", "stadium", "court", "field", "track", "basketball", "bowling", "baseball", "volleyball", "football", "soccer", "tennis", "mma", "boxing", "wrestling", "relay", "baton", "jersey", "activewear", "sneakers"},
    }

    # =========================================================================
    # UNIFIED SCENE CONSTRAINTS
    # =========================================================================
    # Replaces: SCENE_RESTRICTIONS, SCENE_WHITELISTS, CONTEXT_CLASHES
    # Format: "scene_tag": {"allowed": [...], "blocked": [...]}
    # - If "allowed" is present, ONLY those tags are permitted (whitelist)
    # - If "blocked" is present, those tags are forbidden (blacklist)
    # - Both can coexist (allowed takes precedence)
    
    SCENE_CONSTRAINTS = {
        # Work/Professional Environments
        "office": {
            "allowed": ["business", "formal", "office", "work", "suit", "smart casual", "blazer", "shirt", "pencil skirt"],
            "blocked": ["swimwear", "bikini", "lingerie", "armor", "weapon", "pajamas", "fantasy", "medieval"]
        },
        "library": {
            "allowed": ["casual", "business", "academic", "preppy", "formal"],
            "blocked": ["swimwear", "armor", "weapon", "sport", "athletic", "fantasy"]
        },
        "work": {
            "blocked": ["swimwear", "armor", "weapon", "pajamas", "fantasy", "sleep"]
        },
        "school": {
            "blocked": ["swimwear", "armor", "fantasy", "weapon", "bed", "sleep", "lingerie"]
        },
        "hospital": {
            "allowed": ["medical", "scrubs", "coat", "uniform", "doctor", "nurse", "white", "lab"],
            "blocked": ["swimwear", "armor", "weapon", "fantasy", "formal", "party"]
        },
        "medical": {
            "allowed": ["medical", "scrubs", "coat", "uniform", "doctor", "nurse", "white", "lab"],
            "blocked": ["swimwear", "armor", "weapon", "fantasy", "formal", "party"]
        },
        
        # Fitness/Athletic Environments
        "fitness": {
            "allowed": ["sport", "athletic", "fitness", "active", "workout", "yoga"],
            "blocked": ["formal", "armor", "jeans", "dress", "bed", "winter"]
        },
        "yoga": {
            "allowed": ["sport", "athletic", "fitness", "yoga", "active"],
            "blocked": ["formal", "armor", "jeans", "dress", "bed", "winter"]
        },
        "sport": {
            "allowed": ["sport", "athletic", "gym", "active", "workout", "fitness", "yoga", "jersey", "uniform"],
            "blocked": ["formal", "armor", "jeans", "dress", "heels", "bed"]
        },
        "gym": {
            "allowed": ["gym", "fitness", "sport", "workout", "active", "training"],
            "blocked": ["fantasy", "formal", "business", "jeans", "armor", "weapon", "medieval"]
        },
        
        # Leisure/Social Environments
        "beach": {
            "allowed": ["swimwear", "bikini", "swim", "beach", "summer", "casual", "boho", "shorts", "dress", "linen"],
            "blocked": ["formal", "winter", "office", "armor", "coat", "jacket"]
        },
        "pool": {
            "allowed": ["swimwear", "bikini", "swim", "pool", "summer"],
            "blocked": ["formal", "winter", "jeans", "computer", "desk", "armor"]
        },
        "winter": {
            "blocked": ["swimwear", "bikini", "shorts", "crop top", "sleeveless"]
        },
        "snow": {
            "blocked": ["swimwear", "bikini", "sandals", "heels", "shorts"]
        },
        "indoor": {
            "blocked": ["winter", "snow", "ski", "heavy coat"]
        },
        
        # Formal/Elegant Environments
        "formal": {
            "allowed": ["formal", "evening", "gala", "dress", "suit", "tuxedo", "gown", "elegant", "luxury", "high fashion"],
            "blocked": ["swimwear", "casual", "sport", "gym", "pajamas", "jeans", "athletic"]
        },
        "gala": {
            "allowed": ["formal", "evening", "gala", "dress", "suit", "tuxedo", "gown", "elegant", "luxury"],
            "blocked": ["swimwear", "casual", "sport", "gym", "pajamas", "jeans"]
        },
        "wedding": {
            "allowed": ["formal", "wedding", "white", "dress", "suit", "gown", "elegant"],
            "blocked": ["casual", "sport", "armor", "fantasy"]
        },
        
        # Domestic/Private Environments
        "bed": {
            "allowed": ["pajamas", "sleep", "loungewear", "intimate", "lingerie"],
            "blocked": ["armor", "weapon", "footwear", "winter", "hat", "standing", "run", "jump", "shoes", "boots"]
        },
        "sleep": {
            "allowed": ["pajamas", "sleep", "loungewear", "intimate"],
            "blocked": ["armor", "weapon", "footwear", "winter", "hat", "jeans", "formal", "standing"]
        },
        "domestic": {
            "allowed": ["casual", "loungewear", "pajamas", "cozy", "knit", "sweater", "shorts", "t-shirt"],
            "blocked": ["armor", "weapon", "formal", "sport"]
        },
        
        # Cultural/Public Spaces
        "museum": {
            "allowed": ["casual", "business", "formal", "smart casual"],
            "blocked": ["swimwear", "armor", "costume", "sport", "combat", "bed", "sleep", "running", "pajamas"]
        },
        "gallery": {
            "allowed": ["casual", "business", "formal", "artistic", "smart casual"],
            "blocked": ["swimwear", "armor", "costume", "sport", "combat", "bed", "sleep", "running"]
        },
        "quiet": {
            "blocked": ["sport", "loud", "party", "combat", "action", "athletic"]
        },
        
        # Outdoor/Nature Environments
        "nature": {
            "allowed": ["casual", "outdoor", "hiking", "adventure", "rugged", "fantasy"],
            "blocked": ["office", "business", "formal", "tech", "computer", "modern", "neon"]
        },
        "forest": {
            "allowed": ["casual", "outdoor", "fantasy", "rugged", "adventure", "medieval"],
            "blocked": ["office", "tech", "modern", "computer", "neon"]
        },
        "waterfall": {
            "blocked": ["office", "tech", "computer", "modern", "neon"]
        },
        
        # Genre-Specific (STRICT FIREWALLS)
        "fantasy": {
            "allowed": ["fantasy", "medieval", "armor", "robe", "dress", "gala", "rustic", "traditional", "leather", "fur"],
            "blocked": ["modern", "tech", "office", "business", "gun", "rifle", "computer", "phone", "neon", "cyberpunk"]
        },
        "sci-fi": {
            "allowed": ["sci-fi", "tech", "cyberpunk", "futuristic", "modern", "tactical", "armor", "suit", "latex", "metallic"],
            "blocked": ["fantasy", "medieval", "sword", "shield", "magic"]
        },
        "cyberpunk": {
            "allowed": ["cyberpunk", "sci-fi", "tech", "neon", "urban", "street", "leather", "tactical", "edgy"],
            "blocked": ["fantasy", "medieval", "nature", "rustic"]
        },
        "castle": {
            "allowed": ["fantasy", "medieval", "historical", "armor", "traditional", "robe"],
            "blocked": ["modern", "tech", "computer", "phone", "neon", "sport", "athletic", "gym"]
        },
        "dungeon": {
            "allowed": ["fantasy", "medieval", "armor", "dark", "tactical"],
            "blocked": ["modern", "tech", "computer", "phone", "sport"]
        },
        "temple": {
            "allowed": ["fantasy", "historical", "traditional", "cultural", "robe"],
            "blocked": ["modern", "tech", "neon", "sport"]
        },
        "dragon": {
            "allowed": ["fantasy", "medieval", "armor", "magic"],
            "blocked": ["modern", "sport", "athletic", "tech"]
        },
        "lair": {
            "allowed": ["fantasy", "medieval", "dark", "tactical"],
            "blocked": ["modern", "sport", "athletic"]
        },
        "cave": {
            "blocked": ["sport", "athletic", "basketball", "bowling", "baseball", "volleyball", "football", "soccer", "tennis", "track", "stadium"]
        },
        "quest": {
            "allowed": ["fantasy", "medieval", "adventure", "armor"],
            "blocked": ["modern", "sport", "athletic"]
        },
        
        # Sport Venue Isolation (Prevent cross-sport contamination)
        "bowling": {
            "allowed": ["bowling", "retro", "casual"],
            "blocked": ["fantasy", "armor", "weapon", "sword", "shield", "magic", "medieval", "mythology"]
        },
        "stadium": {
            "allowed": ["sport", "athletic", "jersey", "active"],
            "blocked": ["fantasy", "armor", "weapon", "magic", "medieval"]
        },
        "alley": {
            "allowed": ["bowling", "casual", "retro"],
            "blocked": ["basketball", "baseball", "volleyball", "football", "soccer", "tennis", "track", "mma", "boxing", "wrestling"]
        },
        "octagon": {
            "allowed": ["mma", "fighting", "combat_sport"],
            "blocked": ["bowling", "basketball", "baseball", "volleyball", "football", "soccer", "tennis", "track"]
        },
        "cage": {
            "allowed": ["mma", "fighting", "combat_sport"],
            "blocked": ["bowling", "basketball", "baseball", "volleyball", "football", "soccer", "tennis", "track"]
        },
        "diamond": {
            "allowed": ["baseball", "softball"],
            "blocked": ["bowling", "basketball", "volleyball", "football", "soccer", "tennis", "track", "mma", "boxing", "wrestling"]
        },
        "mound": {
            "allowed": ["baseball", "softball"],
            "blocked": ["bowling", "basketball", "volleyball", "football", "soccer", "tennis", "track", "mma", "boxing", "wrestling"]
        },
        
        # Thematic/Stylistic
        "urban": {
            "allowed": ["streetwear", "casual", "skater", "edgy", "denim", "skate", "city", "urban", "graffiti"],
        },
        "vintage": {
            "allowed": ["vintage", "retro", "1950", "1970", "pinup", "disco", "server", "denim", "classic"],
        },
        "academic": {
            "allowed": ["academia", "preppy", "glasses", "blazer", "skirt", "tights", "vest", "shirt"],
        },
        
        # Sport-Specific (from old whitelists)
        "boxing": {
            "allowed": ["boxing", "combat_sport", "active", "training"],
        },
        "mma": {
            "allowed": ["mma", "combat_sport", "fighting"],
        },
        "basketball": {
            "allowed": ["basketball", "jersey", "active", "cheer"],
        },
        "baseball": {
            "allowed": ["baseball", "jersey", "active"],
        },
        "softball": {
            "allowed": ["softball", "baseball", "active"],
        },
        "football": {
            "allowed": ["football", "jersey", "active", "cheer"],
        },
        "soccer": {
            "allowed": ["soccer", "jersey", "active"],
        },
        "tennis": {
            "allowed": ["tennis", "active"],
        },
        "volleyball": {
            "allowed": ["volleyball", "active"],
        },
        "track": {
            "allowed": ["track", "running", "active"],
        },
        "gymnastics": {
            "allowed": ["gymnastics", "leotard", "activewear", "shorts", "leggings"],
        },
        "swim": {
            "allowed": ["swim", "swimwear", "pool", "water", "speedo", "bikini"],
        },
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
        self.scenario_registry = ScenarioRegistry()
        
        # Pre-compute tags (Phase 1 Optimization)
        self._precompute_tags()

    def _precompute_tags(self):
        """Bake expanded tags into internal structures for O(1) lookups."""
        
        # 1. Characters & Outfits
        for char_name, char_data in self.characters.items():
            # Char Tags
            raw_tags = set(char_data.get("tags", []))
            char_data["_expanded_tags"] = self._expand_tags(raw_tags)
            
            # Outfit Tags
            outfits = char_data.get("outfits", {})
            for outfit_name, outfit_val in outfits.items():
                # Handle both string and dict formats
                if isinstance(outfit_val, dict):
                    raw_o_tags = set(outfit_val.get("tags", []))
                    outfit_val["_expanded_tags"] = self._expand_tags(raw_o_tags)
                else:
                    # Upgrade string to dict in-place for caching?
                    # Safer to just not cache string-only outfits or wrap them.
                    # For now, we'll leave string outfits uncached as they have no tags anyway.
                    pass

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
        "combat": ["intense"], # Removed action, dynamic to prevent sport leak
        "action": ["motion", "energetic"], # Pure motion hub
        "fantasy": ["magic", "mythology"],
        "intense": ["dramatic"], # Removed dynamic
        "dramatic": ["theatrical"], # Removed intense
        "anime": ["japanese", "2d"],
        "rugged": ["outdoor", "nature", "western", "gritty"], # Removed action
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
        "energetic": ["active", "playful", "dynamic"],
        "bohemian": ["boho", "creative", "alternative", "artistic"],
        "boho": ["bohemian", "creative", "alternative", "artistic"],
        # Content bridges
        "skate": ["skater", "urban"],
        "skater": ["skate", "urban"],
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
        
        # [NEW] Combat Sports Bridges (Strict)
        "mma": ["fighting", "athletic", "grappling"], # Removed 'combat' and 'sport'
        "boxing": ["fighting", "athletic"], # Removed 'combat' and 'sport'
        "wrestling": ["fighting", "grappling", "athletic"], # Removed 'combat' and 'sport'
        "martial arts": ["fighting", "traditional", "athletic"], # Removed 'combat' and 'sport'
        "grappling": ["wrestling"], # Removed 'combat' and 'sport'
        
        # [NEW] Intimate & Sensual Bridges
        "intimate": ["sensual", "boudoir", "romantic", "sultry", "alluring", "bedroom"],
        "sensual": ["intimate", "glamour", "alluring"],
        "glamour": ["fashion", "beauty", "sensual"],
        "boudoir": ["intimate", "bedroom", "lingerie", "sensual"],
        "sultry": ["sensual", "intimate", "intense"],
        "alluring": ["sensual", "flirty", "intimate"],
        "romantic": ["intimate", "affectionate"],
        
        # [NEW] Missing Fantasy/Historical Bridges (from Audit)
        "druid": ["fantasy", "nature", "magic", "forest"],
        "alchemist": ["fantasy", "magic", "science"],
        "healer": ["fantasy", "magic", "medical", "peaceful"],
        "priestess": ["fantasy", "magic", "traditional", "spiritual"],
        "warrior": ["fantasy", "combat", "armor", "action", "strong"],
        "medieval": ["fantasy", "historical", "armor", "traditional"],
        
        # [NEW] Missing Era/Style Bridges
        "1890s": ["historical", "vintage", "retro", "victorian"],
        "1900s": ["historical", "vintage", "retro", "edwardian"],
        "1920s": ["historical", "vintage", "retro", "noir", "luxury"],
        "1950s": ["historical", "vintage", "retro", "classic"],
        "1970s": ["historical", "vintage", "retro", "boho"],
        "1980s": ["historical", "vintage", "retro", "neon", "pop"],
        "1990s": ["historical", "vintage", "retro", "grunge"],
        "victorian": ["historical", "vintage", "retro", "elegant", "formal"],
        "noir": ["vintage", "dark", "cinematic", "mystery"],
        "steampunk": ["fantasy", "retro", "sci-fi", "tech", "industrial"],
        
        # [NEW] Missing Fashion Bridges
        "k-fashion": ["fashion", "chic", "urban", "modern", "trendy"],
        "techwear": ["tech", "futuristic", "tactical", "urban", "edgy"],
        "streetwear": ["urban", "casual", "modern", "edgy", "fashion"],
        
        # Universal Realism (Make Photorealistic the default baseline BUT allow style variance)
        # Universal Realism (CLEANED: Allows stylized content for all)
        "female": [], 
        "male": [], 
        "urban": ["modern"], 
        "nature": [], 
        "action": ["dynamic", "motion", "energetic"],
        "calm": ["peaceful", "quiet", "serene", "static"],
        "interior": [], 
        "realistic": ["high definition", "photography", "mood:realistic"],
        "formal": ["elegant", "evening"], 
        "business": ["formal", "professional", "office"], 
        "candid": ["photography"], 
        "cinematic": ["dramatic", "lighting"], 
    }

    def _expand_tags(self, tags):
        """Expand tags with aliases/groups recursively."""
        expanded = set(tags)
        
        # Also clean "Mood:" prefixes from raw tags so they match their bare counterparts
        # e.g. "Mood:Futuristic" in tags should allow matching with "futuristic" in aliases
        for t in tags:
            t_str = str(t)
            if t_str.lower().startswith("mood:"):
                expanded.add(t_str[5:].strip())

        # Iterative expansion to handle chains (e.g. cottagecore -> vintage -> nostalgic)
        # 3 passes is usually enough for any reasonable taxonomy depth
        for _ in range(3):
            current_tags = list(expanded)
            added_new = False
            for t in current_tags:
                t_lower = str(t).lower()
                if t_lower in self.TAG_ALIASES:
                    new_tags = self.TAG_ALIASES[t_lower]
                    for nt in new_tags:
                        if nt not in expanded:
                            expanded.add(nt)
                            added_new = True
            if not added_new:
                break
                
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
        
        MAX_RETRIES = 2
        MIN_SCORE_FLOOR = 150
        
        for attempt in range(MAX_RETRIES + 1):
            # With Scenario-First, we need fewer candidates to find a "perfect" match
            num_to_generate = max(3, candidates // 2) if candidates > 5 else candidates
            
            for _ in range(num_to_generate):
                config = self._generate_single_candidate(num_characters, include_scene, include_notes, forced_base_prompt, match_outfits_prob=match_outfits_prob)
                score = self._score_candidate(config)
                
                if score > best_score:
                    best_score = score
                    best_config = config
            
            if best_score >= MIN_SCORE_FLOOR:
                break
        
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
        
        # 1. Setup Context & Constraints
        # Expand moods for broader matching
        raw_moods = metadata.get("vibe", []) or metadata.get("moods", [])
        active_moods = self._expand_tags([m.lower() for m in raw_moods])

        # Re-derive blocked/allowed tags from scene context using NEW unified system
        scene_tags = metadata.get("scene_tags", [])
        blocked_tags = set()
        allowed_tags = None  # None means no whitelist (everything allowed except blocked)
        
        if scene_tags:
            for t in scene_tags:
                t_lower = t.lower()
                if t_lower in self.SCENE_CONSTRAINTS:
                    constraints = self.SCENE_CONSTRAINTS[t_lower]
                    
                    # Apply blocked tags
                    if "blocked" in constraints:
                        blocked_tags.update(constraints["blocked"])
                    
                    # Apply allowed tags (whitelist)
                    if "allowed" in constraints:
                        if allowed_tags is None:
                            allowed_tags = set(constraints["allowed"])
                        else:
                            # Intersection: must satisfy ALL whitelists
                            allowed_tags.intersection_update(constraints["allowed"])

        if not active_moods:
            breakdown["warnings"].append("No active moods/context found for thematic scoring.")

        # 2. Base Score (+10)
        if config.get("scene"): score += 5
        if config.get("notes"): score += 5

        # 3. Calculate Component Scores
        style_score, style_tags = self._score_style_alignment(
            config.get("base_prompt"), active_moods, blocked_tags, breakdown
        )
        score += style_score

        char_score = self._score_character_alignment(
            config, active_moods, blocked_tags, style_tags, breakdown
        )
        score += char_score

        interaction_score, interaction_tags = self._score_interaction_and_diversity(
            config, active_moods, breakdown
        )
        score += interaction_score

        penalty_score = self._calculate_penalties(
            config, scene_tags, interaction_tags, breakdown
        )
        score += penalty_score

        metadata["score_breakdown"] = breakdown
        return score

    def _score_style_alignment(self, base_prompt_name, active_moods, blocked_tags, breakdown):
        """Calculate score for Art Style alignment."""
        score = 0
        expanded_style_tags = set()
        
        if base_prompt_name:
            base_style_data = self.base_prompts.get(base_prompt_name, {})
            style_tags = self._get_tags(base_style_data)
            expanded_style_tags = self._expand_tags([t.lower() for t in style_tags])
            
            if active_moods:
                style_matches = len(expanded_style_tags.intersection(active_moods))
                points = style_matches * 25
                score += points
                breakdown["style_matches"] = points
            
            # Mismatch Check
            if any(t.lower() in blocked_tags for t in style_tags):
                penalty = 100
                score -= penalty
                breakdown["mismatch_penalty"] -= penalty
                breakdown["warnings"].append(f"Style '{base_prompt_name}' is blocked by scene restrictions")
                
        return score, expanded_style_tags

    def _score_character_alignment(self, config, active_moods, blocked_tags, expanded_style_tags, breakdown):
        """Calculate score for Character/Outfit/Pose alignment."""
        score = 0
        selected_chars = config.get("selected_characters", [])
        
        char_tag_counts = {}
        has_outfit_mood_match = False
        
        for char in selected_chars:
            char_name = char.get("name")
            char_def = self.characters.get(char_name, {})
            outfit_name = char.get("outfit")
            
            # Helper to get outfit tags
            outfits_dict = char_def.get("outfits", {})
            outfit_data = outfits_dict.get(outfit_name, {})
            
            # Use pre-computed if available
            raw_outfit_tags = outfit_data.get("_expanded_tags") 
            if raw_outfit_tags is None:
                 raw_outfit_tags = self._expand_tags(self._get_tags(outfit_data))

            # Check Conflicts
            if not raw_outfit_tags.isdisjoint(blocked_tags):
                penalty = 100
                score -= penalty
                breakdown["mismatch_penalty"] -= penalty
                breakdown["warnings"].append(f"Outfit '{outfit_name}' violates scene restrictions")

            # A) Outfit Mood Match
            if active_moods:
                matches = raw_outfit_tags.intersection(active_moods)
                if matches:
                    has_outfit_mood_match = True
                    for m in matches:
                        char_tag_counts[m] = char_tag_counts.get(m, 0) + 1
                    
                    # Diminishing returns: 30 for first 3, 10 thereafter
                    count = len(matches)
                    points = min(count, 3) * 30 + max(0, count - 3) * 10
                    score += points
                    breakdown["mood_matches"] += points

            # B) Pose Alignment
            pose_cat = char.get("pose_category")
            if pose_cat and active_moods:
                if any(m in pose_cat.lower() for m in active_moods):
                    score += 10
                    breakdown["tag_matches"] += 10

            # C) Character Trait Alignment
            char_tags = char_def.get("_expanded_tags") or self._expand_tags([t.lower() for t in char_def.get("tags", [])])
            char_matches = len(char_tags.intersection(active_moods))
            points = char_matches * 5
            score += points
            breakdown["tag_matches"] += points

        # Thematic Singularity Bonus (+100)
        # If Style + Outfit + All Characters share a common tag
        if expanded_style_tags and has_outfit_mood_match and char_tag_counts:
             for mood, count in char_tag_counts.items():
                 # Must be present in ALL characters and the Art Style
                 if count >= len(selected_chars) and mood in expanded_style_tags:
                     score += 100
                     breakdown["diversity_bonus"] += 100
                     breakdown["warnings"].append(f"Thematic Singularity: All elements aligned on '{mood}'")
                     break
                     
        return score

    def _score_interaction_and_diversity(self, config, active_moods, breakdown):
        """Calculate interaction and diversity scores."""
        score = 0
        metadata = config.get("metadata", {})
        selected_chars = config.get("selected_characters", [])
        composition_mode = metadata.get("composition_mode", "Unknown")
        
        # 1. Action Cohesion
        cohesion_score, cohesion_msg = self._check_action_cohesion(config)
        score += cohesion_score
        if cohesion_score < 0:
            breakdown["mismatch_penalty"] += cohesion_score
            breakdown["warnings"].append(cohesion_msg)
        elif cohesion_score > 0:
            breakdown["diversity_bonus"] += cohesion_score

        # 2. Composition Mode Compliance (NEW)
        interaction_present = metadata.get("interaction", "None") != "None"
        num_chars = len(selected_chars)
        
        if composition_mode == self.MODE_SOLO:
            if num_chars == 1:
                score += 30
                breakdown["structure_bonus"] = 30
            else:
                score -= 50 # Solo mode failed
                
        elif composition_mode in (self.MODE_INT_W_POSES, self.MODE_INT_WO_POSES):
            if interaction_present and num_chars >= 2:
                bonus = 50 if composition_mode == self.MODE_INT_W_POSES else 30
                score += bonus
                breakdown["interaction_bonus"] = bonus
            else:
                score -= 100
                breakdown["warnings"].append("Broken Interaction: Mode set but interaction failed")
                
        elif composition_mode == self.MODE_GROUP_NO_INT:
            if num_chars > 1:
                score += 10
                breakdown["structure_bonus"] = 10

        # 3. Interaction Alignment (Context Check)
        interaction_raw_tags = metadata.get("interaction_tags", [])
        interaction_tags = self._expand_tags([t.lower() for t in interaction_raw_tags])
        
        if interaction_tags and active_moods:
            matches = len(interaction_tags.intersection(active_moods))
            points = min(matches, 3) * 10 + max(0, matches - 3) * 5
            score += points
            breakdown["interaction_matches"] = points

        # 4. Diversity (Unique Outfits) - Only for Groups
        if len(selected_chars) > 1:
            unique_outfits = {c.get("outfit") for c in selected_chars}
            points = len(unique_outfits) * 5
            score += points
            breakdown["diversity_bonus"] += points
            
        return score, interaction_tags

    def _calculate_penalties(self, config, scene_tags, interaction_tags, breakdown):
        """Calculate text repetitiveness and contextual clash penalties."""
        score = 0
        
        # 1. Repetitiveness
        text_content = f"{config.get('scene', '')} {config.get('notes', '')}".lower()
        clean_text = text_content.replace(',', ' ').replace('.', ' ').replace('!', ' ').replace('?', ' ')
        words = [w for w in clean_text.split() if len(w) > 4]
        seen_words = set()
        rep_penalty = 0
        for w in words:
            if w in seen_words:
                rep_penalty += 5
            seen_words.add(w)
            
        score -= rep_penalty
        breakdown["repetitive_penalty"] = -rep_penalty

        # 2. Contextual Clashes
        clash_penalty = 0
        if scene_tags:
            combined_content_tags = interaction_tags.union(config.get("metadata", {}).get("pose_tags", []))
            
            # Add character outfit tags to the check
            for char in config.get("selected_characters", []):
                char_tags = set(config.get("metadata", {}).get("character_tags", {}).get(char["name"], []))
                combined_content_tags.update(char_tags)

            # expanded_content_tags = self._expand_tags(combined_content_tags)
            
            for st in scene_tags:
                st_lower = st.lower()
                
                # --- STRICT GENRE BLOCKING (The "Death Penalty") ---
                # If scene is Modern and content features Fantasy (or vice versa)
                is_fantasy_scene = any(t in st_lower for t in self.TAG_GROUPS["GENRE_FANTASY"])
                is_modern_scene = any(t in st_lower for t in self.TAG_GROUPS["GENRE_MODERN"])
                
                if is_fantasy_scene:
                    if any(t in ct.lower() for ct in combined_content_tags for t in self.TAG_GROUPS["GENRE_MODERN"]):
                        clash_penalty += 1000
                        breakdown["mismatch_penalty"] -= 1000
                        breakdown["warnings"].append(f"GENRE CLASH: Fantasy Scene vs Modern Content")

                if is_modern_scene:
                    if any(t in ct.lower() for ct in combined_content_tags for t in self.TAG_GROUPS["GENRE_FANTASY"]):
                        clash_penalty += 1000
                        breakdown["mismatch_penalty"] -= 1000
                        breakdown["warnings"].append(f"GENRE CLASH: Modern Scene vs Fantasy Content")
                        
        score -= clash_penalty
        return score

    def _check_action_cohesion(self, config):
        """Check if all characters are doing things that make sense together.
        
        Returns:
            tuple: (score_modifier, message)
        """
        selected_chars = config.get("selected_characters", [])
        if len(selected_chars) < 2:
            return 0, ""

        categories = set()
        for char in selected_chars:
            cat = char.get("pose_category", "").lower()
            if cat:
                # Group related categories
                if any(x in cat for x in ["athletic", "sport", "action", "combat", "dynamic"]):
                    categories.add("athletic")
                elif any(x in cat for x in ["sleep", "bed", "bedroom", "pajamas", "morning"]):
                    categories.add("sleep")
                elif any(x in cat for x in ["art", "creative", "judge", "work", "office"]):
                    categories.add("productive")
                elif any(x in cat for x in ["social", "friendly", "casual", "talk"]):
                    categories.add("social")
                elif any(x in cat for x in ["sensual", "lingerie", "glamour"]):
                    categories.add("glamour")
                else:
                    categories.add(cat)

        # Discordant Check: Athletic vs Sleep or Productive vs Sleep
        clashes = [
            ({"athletic", "sleep"}, -200, "Action Clashes: Athletic vs Sleep"),
            ({"productive", "sleep"}, -150, "Action Clashes: Productive vs Sleep"),
            ({"glamour", "athletic"}, -100, "Action Clashes: Glamour vs Athletic"),
            ({"formal", "sleep"}, -200, "Action Clashes: Formal vs Sleep")
        ]

        for clash_set, penalty, msg in clashes:
            if clash_set.issubset(categories):
                return penalty, msg

        # Cohesion Bonus: Everyone doing the same broad thing
        if len(categories) == 1:
            cat = list(categories)[0]
            # Verify it matches the scene category
            scene_text = config.get("scene", "").lower()
            if cat in scene_text or any(t.lower() in scene_text for t in self._expand_tags([cat])):
                 return 75, f"Cohesion Bonus: All characters in {cat} mode matching scene"

        return 0, ""

    def _generate_single_candidate(self, num_characters=None, include_scene=False, include_notes=False, forced_base_prompt=None, match_outfits_prob=0.3):
        """Generate a single random prompt configuration using SCENARIO-FIRST logic."""
        # =========================================================================
        # STEP 0: SELECT HUB & SCENARIO (THE PARTNERSHIP)
        # =========================================================================
        # Pick the scenario first (since it's the authority), then pick a compatible Hub.
        # This ensures the Hub is a thematic guide, not a logic bypass.
        scenario = self.scenario_registry.get_random()
        
        # Identify valid Hubs for this scenario
        scenario_vibes = [v.lower() for v in getattr(scenario, 'vibe_tags', [])]
        scenario_blocked = [b.lower() for b in getattr(scenario, 'blocked_global_tags', [])]
        
        possible_hubs = [h for h in self.HUB_TAGS if h.lower() not in scenario_blocked]
        preferred_hubs = [h for h in possible_hubs if h.lower() in scenario_vibes]
        
        if preferred_hubs:
            hub_tag = random.choice(preferred_hubs)
        elif possible_hubs:
            hub_tag = random.choice(possible_hubs)
        else:
            hub_tag = random.choice(self.HUB_TAGS) # Emergency fallback

        # =========================================================================
        # STEP 2: SELECT SCENE (Driven by Hub)
        # =========================================================================
        scene_desc = ""
        scene_category = ""
        scene_tags = []
        
        if include_scene:
            # 1. Identify Candidate Scenes (Global Scan or Category Limit?)
            # Strategy: Search ALL scenes for the Hub Tag.
            # Efficiency: Pre-calculated index would be better, but iteration is fast enough for <1000 items.
            
            hub_scenes = []
            
            valid_scenes = []
            
            # Identify Scenario Requirements
            req_scene_tags = set(t.lower() for t in getattr(scenario, 'required_scene_tags', []))
            blocked_global = set(t.lower() for t in getattr(scenario, 'blocked_global_tags', []))
            
            eligible_categories = scenario.allowed_scene_categories
            target_scene_cats = eligible_categories if eligible_categories else self.scenes.keys()
            
            for cat_name in target_scene_cats:
                if cat_name in self.scenes:
                    for p_name, p_data in self.scenes[cat_name].items():
                        tags = self._get_tags(p_data)
                        tags_lower = set(t.lower() for t in tags)
                        
                        # A) Must NOT contain blocked global tags
                        if not tags_lower.isdisjoint(blocked_global):
                            continue
                            
                        # B) Must satisfy Scenario requirements (Hard Filter)
                        if req_scene_tags and not req_scene_tags.issubset(tags_lower):
                            continue
                            
                        valid_scenes.append((cat_name, p_name, p_data, tags_lower))
            
            # HUB PREFERENCE
            hub_scenes = [s for s in valid_scenes if hub_tag.lower() in s[3]]
            
            if hub_scenes:
                s_cat, s_name, s_data, _ = random.choice(hub_scenes)
            elif valid_scenes:
                s_cat, s_name, s_data, _ = random.choice(valid_scenes)
            else:
                # Emergency Fallback (Total Failure)
                valid_cats = [c for c in self.scenes.keys() if self.scenes[c]]
                if valid_cats:
                    s_cat = random.choice(valid_cats)
                    s_name = random.choice(list(self.scenes[s_cat].keys()))
                    s_data = self.scenes[s_cat][s_name]
                else:
                    # Absolute disaster recovery
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
        if num_characters is None:
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
        available_char_names = list(self.characters.keys())
        if not available_char_names:
            return None
            
        # Sample names (ensure we don't exceed availability)
        char_count = min(num_characters, len(available_char_names))
        char_names = random.sample(available_char_names, char_count)
        selected_characters = []
        
        # Context for roles
        context_tags = set(scenario.vibe_tags)
        context_tags.update(scene_tags)

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
                hub_tag=hub_tag # Pass Hub Tag for outfit filtering
            )
            
            # --- APPLY MODE SPECIFIC POSE LOGIC ---

            # --- APPLY MODE SPECIFIC POSE LOGIC ---
            # [STRICT SEPARATION] If any Interaction is present, suppress individual character poses 
            # to prevent technical clashes in the generated prompt.
            if composition_mode in (self.MODE_INT_W_POSES, self.MODE_INT_WO_POSES):
                 char_data["pose_preset"] = ""
                 char_data["pose_category"] = ""
                 
                 if composition_mode == self.MODE_INT_W_POSES:
                      # MODE_INT_W_POSES uses specific poses for each character as required by the interaction
                      req_poses = selected_interaction.get("required_poses", [])
                      if req_poses and i < len(req_poses):
                          char_data["action_note"] = req_poses[i]
                      elif req_poses:
                          char_data["action_note"] = random.choice(req_poses)
                      else:
                          char_data["action_note"] = ""
                 else:
                      # MODE_INT_WO_POSES is purely text-based (Interactions without Poses)
                      char_data["action_note"] = ""

            selected_characters.append(char_data)

        # =========================================================================
        # STEP 6: FINALIZE INTERACTION NOTES
        # =========================================================================
        notes_text = ""
        notes_name = "None"
        
        if composition_mode in (self.MODE_INT_W_POSES, self.MODE_INT_WO_POSES) and selected_interaction:
             notes_name = selected_interaction["name"]
             t_text = selected_interaction["text"]
             c_names = [c["name"] for c in selected_characters]
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
                "interaction": notes_name,
                "interaction_tags": set(self._get_tags(selected_interaction)) if selected_interaction else set(),
                "min_chars": selected_interaction.get("min_chars", 0) if selected_interaction else 0,
                "composition_mode": composition_mode,
                "hub_tag": hub_tag
            }
        }

    def _randomize_character_with_role(self, char_name, role, scene_category="", context_tags=None, hub_tag=None):
        """Generate character features strictly matching a role."""
        char_def = self.characters.get(char_name, {})
        outfits = char_def.get("outfits", {})
        categorized_outfits = char_def.get("outfits_categorized", {})
        
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
            if scene_cat_lower in self.SCENE_WHITELISTS:
                for tag in self.SCENE_WHITELISTS[scene_cat_lower]:
                    selection_tags.add(f"whitelist:{tag}")
            
            if scene_cat_lower in self.SCENE_RESTRICTIONS:
                local_blocked.update(self.SCENE_RESTRICTIONS[scene_cat_lower])

        # 2. Context Tag Specifics (Precise)
        # Check if any active scene tags trigger a specific whitelist/blocklist
        # e.g. "volleyball" tag triggers the "volleyball" whitelist
        if context_tags:
            # Extract explicit blocks from scene tags (e.g. block:MMA)
            _, _, scene_blocks = self._extract_special_tags(context_tags)
            local_blocked.update(scene_blocks)
            
            for tag in context_tags:
                t_lower = tag.lower()
                if t_lower in self.SCENE_WHITELISTS:
                     for w_tag in self.SCENE_WHITELISTS[t_lower]:
                         selection_tags.add(f"whitelist:{w_tag}")
                
                if t_lower in self.SCENE_RESTRICTIONS:
                     local_blocked.update(self.SCENE_RESTRICTIONS[t_lower])

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
        available_traits = char_def.get("traits", {})
        selected_traits = [random.choice(list(available_traits.keys()))] if available_traits and random.random() < 0.9 else []

        # 4. Color Scheme (especially important for sports)
        outfit_tags = self._get_tags(outfits.get(outfit_name, {}))
        color_scheme = self._select_smart_color_scheme(outfit_tags, scene_category)
        
        # 5. Outfit Modifiers/Traits
        outfit_traits = []
        if isinstance(outfits.get(outfit_name), dict):
            outfit_data = outfits[outfit_name]
            if "modifiers" in outfit_data and outfit_data["modifiers"]:
                available_modifiers = list(outfit_data["modifiers"].keys())
                # 30% chance to apply a modifier
                if available_modifiers and random.random() < 0.3:
                    outfit_traits = [random.choice(available_modifiers)]

        return {
            "name": char_name,
            "outfit": outfit_name,
            "pose_category": pose_category,
            "pose_preset": pose_preset,
            "character_traits": selected_traits,
            "color_scheme": color_scheme,
            "outfit_traits": outfit_traits,
            "role_name": role.name
        }

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

            for p_name, p_data in items.items():
                 p_tags = get_pose_tags(p_data)
                 if not p_tags.isdisjoint(blocked):
                     continue # Item is blocked, don't count it
                 
                 if not p_tags.isdisjoint(context_tags):
                     relevant_items += 1
            
            score += (relevant_items * 2.0)
            
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
            char_names = [char["name"] for char in selected_characters]
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
                # Check for hard scene restrictions
                if scene_category.lower() in self.SCENE_RESTRICTIONS:
                    restricted_tags = self.SCENE_RESTRICTIONS[scene_category.lower()]
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
                if scene_category.lower() in self.SCENE_WHITELISTS:
                    whitelist = set(self.SCENE_WHITELISTS[scene_category.lower()])
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
        
        # [MODIFIED] Flattened Distribution Logic
        # Removed "Drastic Measure" favoring Photorealistic to allow variety.
        # Probability 0.40: Select from matching pool (Context Sensitive)
        # Probability 0.60: Select purely random (Serendipity)
        if matching and random.random() < 0.40:
             return random.choice(matching)
             
        # Fallback to completely random selection from the entire pool
        return random.choice(available_prompts)
