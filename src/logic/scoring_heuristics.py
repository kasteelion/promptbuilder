import logging
import traceback

logger = logging.getLogger(__name__)

class ScoringEngine:
    """Handles heuristic scoring and coherence checking for generated prompt configurations."""

    def __init__(self, randomizer_context):
        """
        Initialize with a context object providing necessary data and helper methods.
        Expected context attributes:
            - scoring: dict
            - base_prompts: dict
            - characters: dict
            - tag_groups: dict
            - scene_constraints: dict
            - _expand_tags: method(tags_list)
            - _get_tags: method(item_data)
        """
        self.ctx = randomizer_context

    def score_candidate(self, config):
        """
        Score a generated configuration based on simplified heuristics.
        
        SIMPLIFIED SCORING (6 rules):
        1. Mood Match (+30/match) - Core thematic alignment
        2. Style Alignment (+25/match) - Art style coherence  
        3. Genre Clash (-1000) - Critical firewall
        4. Mismatch Penalty (-100) - Constraint violations
        5. Diversity Bonus (+10/unique) - Group variety
        6. Affinity Bonus (+50/match) - Gemma recommended affinities
        """
        score = 0
        breakdown = {
            "mood_matches": 0,
            "style_matches": 0,
            "diversity_bonus": 0,
            "mismatch_penalty": 0,
            "genre_clash": 0,
            "affinity_bonus": 0,
            "color_harmony_bonus": 0,
            "color_clash_penalty": 0,
            "warnings": []
        }
        
        metadata = config.get("metadata", {})
        
        # 1. Setup Context & Constraints
        raw_moods = metadata.get("vibe", []) or metadata.get("moods", [])
        active_moods = self.ctx._expand_tags([m.lower() for m in raw_moods])

        scene_tags = metadata.get("scene_tags", [])
        blocked_tags = set()
        allowed_tags = None  
        
        if scene_tags:
            for t in scene_tags:
                t_lower = t.lower()
                if t_lower in self.ctx.scene_constraints:
                    constraints = self.ctx.scene_constraints[t_lower]
                    if "blocked" in constraints:
                        blocked_tags.update(constraints["blocked"])
                    if "allowed" in constraints:
                        if allowed_tags is None:
                            allowed_tags = set(constraints["allowed"])
                        else:
                            allowed_tags.intersection_update(constraints["allowed"])

        if not active_moods:
            breakdown["warnings"].append("No active moods/context found for thematic scoring.")
        
        # Store for penalty checks
        if "metadata" not in config:
            config["metadata"] = {}
        config["metadata"]["blocked_tags"] = blocked_tags
        config["metadata"]["allowed_tags"] = allowed_tags
        config["metadata"]["active_moods"] = active_moods
        
        # 2. Style Alignment (+25/match)
        base_prompt = config.get("base_prompt")
        if base_prompt and active_moods:
            style_data = self.ctx.base_prompts.get(base_prompt, {})
            expanded_style = style_data.get("_expanded_tags")
            if not expanded_style:
                style_tags = self.ctx._get_tags(style_data)
                expanded_style = self.ctx._expand_tags([t.lower() for t in style_tags])
            
            matches = len(expanded_style.intersection(active_moods))
            points = matches * 25
            score += points
            breakdown["style_matches"] = points

        # 2b. Style-scene genre coherence (-200 penalty)
        if base_prompt and scene_tags:
            style_name_tags = set()
            if "(" in base_prompt and ")" in base_prompt:
                tag_part = base_prompt[base_prompt.rfind("(") + 1: base_prompt.rfind(")")]
                style_name_tags = {t.strip().lower() for t in tag_part.split(",")}

            style_genres = set()
            for group_name, group_tags in self.ctx.tag_groups.items():
                if group_name.startswith("GENRE_"):
                    genre_label = group_name[len("GENRE_"):].lower()
                    if style_name_tags.intersection({t.lower() for t in group_tags}):
                        style_genres.add(genre_label)

            expanded_scene_tags_local = self.ctx._expand_tags(scene_tags)
            local_scene_genres = set()
            for group_name, group_tags in self.ctx.tag_groups.items():
                if group_name.startswith("GENRE_"):
                    genre_label = group_name[len("GENRE_"):].lower()
                    if expanded_scene_tags_local.intersection({t.lower() for t in group_tags}):
                        local_scene_genres.add(genre_label)

            if style_genres and local_scene_genres and style_genres.isdisjoint(local_scene_genres):
                penalty = 200
                score -= penalty
                breakdown["mismatch_penalty"] -= penalty
                breakdown["warnings"].append(f"STYLE-SCENE MISMATCH: '{base_prompt}' genre={style_genres} vs scene genre={local_scene_genres}")
        
        # 3. Mood Matches (+30/match)
        for char in config.get("selected_characters", []):
            char_name = char.name if hasattr(char, "name") else char.get("name")
            outfit_name = char.outfit if hasattr(char, "outfit") else char.get("outfit")
            
            char_def = self.ctx.characters.get(char_name, {})
            char_outfits = char_def.outfits if hasattr(char_def, "outfits") else char_def.get("outfits", {})
            outfit_data = char_outfits.get(outfit_name, {})
            
            if isinstance(outfit_data, dict):
                outfit_tags = outfit_data.get("_expanded_tags")
                if not outfit_tags:
                    outfit_tags = self.ctx._expand_tags(self.ctx._get_tags(outfit_data))
            else:
                outfit_tags = set()
            
            if active_moods and outfit_tags:
                matches = outfit_tags.intersection(active_moods)
                count = len(matches)
                cutoff = self.ctx.scoring["thresholds"]["mood_diminishing_returns_cutoff"]
                full_weight = self.ctx.scoring["weights"]["mood_match"]
                excess_weight = self.ctx.scoring["thresholds"]["mood_excess_value"]
                
                points = min(count, cutoff) * full_weight + max(0, count - cutoff) * excess_weight
                score += points
                breakdown["mood_matches"] += points
        
        # 4. Diversity Bonus (+10/unique outfit)
        chars = config.get("selected_characters", [])
        if len(chars) > 1:
            unique_outfits = {char.outfit if hasattr(char, "outfit") else char.get("outfit") for char in chars}
            points = len(unique_outfits) * 10
            score += points
            breakdown["diversity_bonus"] = points
            
        # 5. Affinity Bonus (+50/match)
        scene_cat = config.get("scene_category", "")
        for char in chars:
            char_name = char.name if hasattr(char, "name") else char.get("name")
            char_def = self.ctx.characters.get(char_name, {})
            if hasattr(char_def, "affinities") and char_def.affinities:
                affinities = char_def.affinities
                if base_prompt and any(base_prompt.lower() == a.lower() for a in affinities.get("Styles", [])):
                    points = 50
                    score += points
                    breakdown["affinity_bonus"] += points
                if scene_cat and any(scene_cat.lower() == a.lower() for a in affinities.get("Scenes", [])):
                    points = 50
                    score += points
                    breakdown["affinity_bonus"] += points
                
        # 6. Mismatch Penalty (-100)
        for char in chars:
            char_name = char.name if hasattr(char, "name") else char.get("name")
            outfit_name = char.outfit if hasattr(char, "outfit") else char.get("outfit")
            
            char_def = self.ctx.characters.get(char_name, {})
            char_outfits = char_def.outfits if hasattr(char_def, "outfits") else char_def.get("outfits", {})
            outfit_data = char_outfits.get(outfit_name, {})
            
            if isinstance(outfit_data, dict):
                outfit_tags = outfit_data.get("_expanded_tags") or self.ctx._expand_tags(self.ctx._get_tags(outfit_data))
                if blocked_tags and not outfit_tags.isdisjoint(blocked_tags):
                    penalty = abs(self.ctx.scoring["penalties"]["mismatch"])
                    score -= penalty
                    breakdown["mismatch_penalty"] -= penalty
                    violations = outfit_tags.intersection(blocked_tags)
                    breakdown["warnings"].append(f"Outfit '{outfit_name}' violates restrictions: {violations}")
                
                if allowed_tags and not outfit_tags.intersection(allowed_tags):
                    penalty = abs(self.ctx.scoring["penalties"]["mismatch"])
                    score -= penalty
                    breakdown["mismatch_penalty"] -= penalty
                    breakdown["warnings"].append(f"Outfit '{outfit_name}' not in scene whitelist")
        
        # 6. Genre Clash
        genre_groups = {}
        for group_name, group_tags in self.ctx.tag_groups.items():
            if group_name.startswith("GENRE_"):
                genre_groups[group_name[6:].lower()] = {t.lower() for t in group_tags}

        expanded_scene_tags = self.ctx._expand_tags(scene_tags)
        scene_genres = {label for label, gtags in genre_groups.items() if expanded_scene_tags.intersection(gtags)}

        for char in chars:
            char_name = char.name if hasattr(char, "name") else char.get("name")
            outfit_name = char.outfit if hasattr(char, "outfit") else char.get("outfit")
            char_def = self.ctx.characters.get(char_name, {})
            char_outfits = char_def.outfits if hasattr(char_def, "outfits") else char_def.get("outfits", {})
            outfit_data = char_outfits.get(outfit_name, {})

            if isinstance(outfit_data, dict):
                outfit_tags = outfit_data.get("_expanded_tags") or self.ctx._expand_tags(self.ctx._get_tags(outfit_data))
                outfit_genres = {label for label, gtags in genre_groups.items() if outfit_tags.intersection(gtags)}

                if scene_genres and outfit_genres and scene_genres.isdisjoint(outfit_genres):
                    penalty = abs(self.ctx.scoring["penalties"]["genre_clash"])
                    score -= penalty
                    breakdown["genre_clash"] -= penalty
                    breakdown["warnings"].append(f"GENRE CLASH: scene={scene_genres} vs outfit '{outfit_name}' genres={outfit_genres}")

        # 6b. Feedback Loop: Historic Clash Check
        from logic.feedback_loop import FeedbackLoop
        feedback = FeedbackLoop()
        if feedback.is_clashing(expanded_scene_tags):
             penalty = 500
             score -= penalty
             breakdown["warnings"].append(f"HISTORIC CLASH: Configuration matches a previously rejected thematic pattern.")

        # 7. Cross-character outfit genre coherence
        if len(chars) > 1 and genre_groups:
            genres_present = []
            for char in chars:
                char_name = char.name if hasattr(char, "name") else char.get("name")
                outfit_name = char.outfit if hasattr(char, "outfit") else char.get("outfit")
                char_def = self.ctx.characters.get(char_name, {})
                char_outfits = char_def.outfits if hasattr(char_def, "outfits") else char_def.get("outfits", {})
                outfit_data = char_outfits.get(outfit_name, {})
                if isinstance(outfit_data, dict):
                    outfit_tags = outfit_data.get("_expanded_tags") or self.ctx._expand_tags(self.ctx._get_tags(outfit_data))
                    char_genres = frozenset(lbl for lbl, gtags in genre_groups.items() if outfit_tags.intersection(gtags))
                    if char_genres:
                        genres_present.append(char_genres)

            if genres_present:
                all_outfit_genres = set().union(*genres_present)
                if len(all_outfit_genres) > 1:
                    extra_genres = len(all_outfit_genres) - 1
                    penalty = abs(self.ctx.scoring["penalties"]["mismatch"]) * extra_genres
                    score -= penalty
                    breakdown["mismatch_penalty"] -= penalty
                    breakdown["warnings"].append(f"OUTFIT INCOHERENCE: {len(all_outfit_genres)} genre axes in group ({all_outfit_genres})")

        # 8. Color Harmony & Contrast Scoring
        contrast_schemes = {
            "maroon & khaki", "olive & rust", "navy & amber",
            "charcoal & mustard", "emerald & bronze", "sage & terracotta",
            "midnight & crimson"
        }
        char_schemes = []
        for char in chars:
            cs = getattr(char, "color_scheme", None) if hasattr(char, "color_scheme") else char.get("color_scheme")
            use_sig = getattr(char, "use_signature_color", False) if hasattr(char, "use_signature_color") else char.get("use_signature_color", False)
            char_name = char.name if hasattr(char, "name") else char.get("name")
            char_def = self.ctx.characters.get(char_name, {})
            sig_color = getattr(char_def, "signature_color", None) if hasattr(char_def, "signature_color") else (char_def.get("signature_color") if isinstance(char_def, dict) else None)

            if cs and cs.lower() in contrast_schemes:
                # Bonus for intentional contrast harmony
                points = 35
                score += points
                breakdown["color_harmony_bonus"] += points

            if use_sig and sig_color:
                # Bonus for signature color pop
                points = 20
                score += points
                breakdown["color_harmony_bonus"] += points

            if cs and cs not in ("Default (No Scheme)", ""):
                char_schemes.append(cs)

        # Multi-character color coordination
        if len(chars) > 1 and len(char_schemes) > 1:
            is_sports = any(t in ["sport", "sports", "athletic", "team"] for t in [st.lower() for st in scene_tags])
            if len(set(char_schemes)) < len(char_schemes) and not is_sports:
                # Penalty for identical scheme duplication in narrative scenes
                penalty = 50
                score -= penalty
                breakdown["color_clash_penalty"] -= penalty
                breakdown["warnings"].append(f"DUPLICATE SCHEME: Multiple characters assigned '{char_schemes[0]}'")
            elif len(set(char_schemes)) == len(char_schemes):
                # Distinct harmonious contrast bonus
                points = 25
                score += points
                breakdown["color_harmony_bonus"] += points
        
        metadata["score_breakdown"] = breakdown
        return score

    def check_action_cohesion(self, config):
        """Check if all characters are doing things that make sense together."""
        selected_chars = config.get("selected_characters", [])
        if not selected_chars:
            return 0, ""

        score_mod = 0
        warnings = []
        categories = set()
        
        metadata = config.get("metadata", {})
        scene_tags = metadata.get("scene_tags", [])
        is_high_energy = any(t in ["action", "combat", "sport", "athletic", "energetic", "dynamic"] for t in [st.lower() for st in scene_tags])
        
        for char in selected_chars:
            pose = char.get("pose_preset", "Default")
            cat = char.get("pose_category", "").lower()
            
            if is_high_energy and pose == "Default":
                score_mod -= 300
                warnings.append("Static pose 'Default' in high-energy scene.")
            
            if cat:
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

        clashes = [
            ({"athletic", "sleep"}, -200, "Action Clashes: Athletic vs Sleep"),
            ({"productive", "sleep"}, -150, "Action Clashes: Productive vs Sleep"),
            ({"glamour", "athletic"}, -100, "Action Clashes: Glamour vs Athletic"),
            ({"formal", "sleep"}, -200, "Action Clashes: Formal vs Sleep")
        ]

        for clash_set, penalty, msg in clashes:
            if clash_set.issubset(categories):
                score_mod += penalty
                warnings.append(msg)

        if len(categories) == 1 and len(selected_chars) > 1:
            cat = list(categories)[0]
            score_mod += 75
            warnings.append(f"Cohesion Bonus: All characters in {cat} mode")

        return score_mod, "; ".join(warnings) if warnings else ""
