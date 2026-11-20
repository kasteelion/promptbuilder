from typing import Dict, List, Any, Optional
from core.models import SelectedCharacterConfig


class SuggestionItem:
    """Represents an actionable 1-click prompt suggestion."""

    def __init__(
        self,
        kind: str,
        label: str,
        description: str,
        category: str = "",
        payload: Optional[Dict[str, Any]] = None,
        icon: str = "lightbulb",
        score: float = 1.0,
        extra: Optional[Dict[str, Any]] = None,
    ):
        self.kind = kind  # "scene", "interaction", "outfit", "harmony"
        self.label = label
        self.description = description
        self.category = category
        self.payload = payload or {}
        self.icon = icon
        self.score = score
        self.extra = extra or {}


class SuggestionEngine:
    """Lightweight, zero-latency suggestion engine.
    
    Generates context-aware, gap-filling recommendations (scenes, multi-character
    interactions, outfits, color harmonies) by computing local tag and aesthetic overlap.
    """

    @classmethod
    def get_suggestions(cls, app_state) -> Dict[str, List[SuggestionItem]]:
        """Analyze current app_state and return categorized suggestions."""
        results: Dict[str, List[SuggestionItem]] = {
            "scenes": [],
            "interactions": [],
            "outfits": [],
            "harmonies": [],
        }

        if not hasattr(app_state, "state") or not hasattr(app_state, "ctx"):
            return results

        selected_chars: List[SelectedCharacterConfig] = app_state.state.get("selected_characters", [])
        if not selected_chars:
            return results

        # 1. Harvest active character tags & keywords
        char_tags = set()
        char_names = []
        for c in selected_chars:
            name = c.name if hasattr(c, "name") else c.get("name", "")
            char_names.append(name.split()[0])
            meta = app_state.ctx.characters_metadata.get(name)
            if meta:
                for t in getattr(meta, "tags", []):
                    char_tags.add(t.lower())
                vibe = getattr(meta, "vibe", "") or ""
                for word in vibe.replace(",", " ").split():
                    if len(word) > 3:
                        char_tags.add(word.lower())

        current_scene = (app_state.state.get("scene") or "").strip()
        current_notes = (app_state.state.get("notes") or "").strip()

        # 2. Scene Suggestions (Top priority if scene is missing, or suggest thematic alternatives)
        scene_suggestions = cls._suggest_scenes(app_state.ctx.scenes, char_tags, current_scene)
        results["scenes"] = scene_suggestions

        # 3. Multi-Character Interaction Suggestions (If 2+ characters and notes are empty)
        if len(selected_chars) >= 2 and not current_notes:
            int_suggestions = cls._suggest_interactions(app_state.ctx.interactions, char_tags, char_names)
            results["interactions"] = int_suggestions

        # 4. Outfit Suggestions (If any character is currently in 'Base' outfit)
        outfit_suggestions = cls._suggest_outfits(app_state, selected_chars, current_scene, char_tags)
        results["outfits"] = outfit_suggestions

        # 5. Color Harmony Suggestions (If no scheme or default scheme is active)
        harmony_suggestions = cls._suggest_harmonies(app_state.ctx.color_schemes, current_scene, char_tags)
        results["harmonies"] = harmony_suggestions

        return results

    @classmethod
    def _suggest_scenes(
        cls, scenes_dict: Dict[str, Any], char_tags: set, current_scene: str
    ) -> List[SuggestionItem]:
        scored = []
        for cat, presets in scenes_dict.items():
            if not isinstance(presets, dict):
                continue
            for p_name, p_data in presets.items():
                if not isinstance(p_data, dict):
                    continue
                desc = p_data.get("description", "")
                if current_scene and desc.strip() == current_scene:
                    continue  # already active

                s_tags = {t.lower() for t in p_data.get("tags", [])}
                hits = len(char_tags.intersection(s_tags))

                # Bonus for keywords matching
                desc_lower = desc.lower()
                for t in char_tags:
                    if t in desc_lower:
                        hits += 0.5

                if hits > 0 or not current_scene:
                    scored.append((hits, p_name, cat, desc))

        scored.sort(key=lambda x: x[0], reverse=True)

        suggestions = []
        seen_cats = set()
        for hits, name, cat, desc in scored:
            # Strive for diverse categories
            if cat in seen_cats and len(suggestions) >= 2:
                continue
            seen_cats.add(cat)
            suggestions.append(
                SuggestionItem(
                    kind="scene",
                    label=name,
                    category=cat,
                    description=desc,
                    payload={"category": cat, "preset": name, "description": desc},
                    score=hits,
                )
            )
            if len(suggestions) >= 4:
                break
        return suggestions

    @classmethod
    def _suggest_interactions(
        cls, interactions_dict: Dict[str, Any], char_tags: set, char_names: List[str]
    ) -> List[SuggestionItem]:
        scored = []
        for cat, presets in interactions_dict.items():
            if not isinstance(presets, dict):
                continue
            for p_name, p_data in presets.items():
                if not isinstance(p_data, dict):
                    continue
                min_c = p_data.get("min_chars", 2)
                if len(char_names) < min_c:
                    continue

                raw_desc = p_data.get("description", "")
                i_tags = {t.lower() for t in p_data.get("tags", [])}
                hits = len(char_tags.intersection(i_tags))

                # Resolve character names
                resolved_desc = raw_desc
                for i, cname in enumerate(char_names):
                    resolved_desc = resolved_desc.replace(f"{{char{i+1}}}", cname)

                scored.append((hits, p_name, cat, resolved_desc))

        scored.sort(key=lambda x: x[0], reverse=True)

        suggestions = []
        for hits, name, cat, desc in scored[:3]:
            suggestions.append(
                SuggestionItem(
                    kind="interaction",
                    label=name,
                    category=cat,
                    description=desc,
                    payload={"category": cat, "preset": name, "description": desc},
                    score=hits,
                )
            )
        return suggestions

    @classmethod
    def _suggest_outfits(
        cls, app_state, selected_chars: List[SelectedCharacterConfig], current_scene: str, char_tags: set
    ) -> List[SuggestionItem]:
        suggestions = []
        scene_lower = current_scene.lower()

        for idx, char_cfg in enumerate(selected_chars):
            current_outfit = getattr(char_cfg, "outfit", "Base")
            if current_outfit and current_outfit != "Base":
                continue  # already has a custom outfit

            char_name = char_cfg.name if hasattr(char_cfg, "name") else char_cfg.get("name", "")
            try:
                details = app_state.data_loader.get_character_details(char_name)
                available_outfits = details.outfits or {}
            except Exception:
                continue

            scored_outfits = []
            for o_name, o_data in available_outfits.items():
                if o_name in ("Base", "Default"):
                    continue
                o_str = str(o_data).lower()
                hits = 0

                # Match with active scene
                if current_scene:
                    for word in scene_lower.replace(",", " ").split():
                        if len(word) > 3 and word in o_str:
                            hits += 1.0

                # Match with character tags
                for tag in char_tags:
                    if tag in o_str:
                        hits += 0.5

                if hits > 0:
                    scored_outfits.append((hits, o_name))

            scored_outfits.sort(key=lambda x: x[0], reverse=True)
            chosen = scored_outfits[:2] if scored_outfits else [(0.5, o) for o in list(available_outfits.keys()) if o not in ("Base", "Default")][:2]

            for hits, o_name in chosen:
                suggestions.append(
                    SuggestionItem(
                        kind="outfit",
                        label=f"{char_name.split()[0]}: {o_name}",
                        category="Wardrobe",
                        description=f"Equip {o_name} on {char_name}",
                        payload={"char_index": idx, "char_name": char_name, "outfit": o_name},
                        score=hits,
                    )
                )
                if len(suggestions) >= 3:
                    return suggestions

        return suggestions

    @classmethod
    def _suggest_harmonies(
        cls, color_schemes: Dict[str, Any], current_scene: str, char_tags: set
    ) -> List[SuggestionItem]:
        suggestions = []
        curated_harmonies = [
            ("Maroon & Khaki", "#800020", "#C3B091", "Autumn Casual Contrast"),
            ("Olive & Rust", "#556B2F", "#B7410E", "Earthy Warm Contrast"),
            ("Navy & Amber", "#001F3F", "#FFBF00", "Complementary Pop"),
            ("Charcoal & Mustard", "#36454F", "#E1AD01", "Urban High Contrast"),
            ("Emerald & Bronze", "#50C878", "#CD7F32", "Jewel Tone Elegance"),
            ("Sage & Terracotta", "#9DC183", "#E2725B", "Warm Muted Contrast"),
            ("Midnight & Crimson", "#0A0F24", "#990000", "Dramatic Noir"),
        ]

        scene_lower = current_scene.lower()
        scored = []
        for name, p, s, desc in curated_harmonies:
            score = 1.0
            if any(w in scene_lower for w in ("noir", "night", "dark", "alley", "rain", "cyber")) and name in ("Midnight & Crimson", "Charcoal & Mustard", "Navy & Amber"):
                score += 2.0
            elif any(w in scene_lower for w in ("nature", "park", "forest", "garden", "outdoor")) and name in ("Olive & Rust", "Sage & Terracotta", "Emerald & Bronze"):
                score += 2.0
            elif any(w in scene_lower for w in ("cafe", "coffee", "street", "casual", "brunch")) and name in ("Maroon & Khaki", "Sage & Terracotta"):
                score += 2.0
            scored.append((score, name, p, s, desc))

        scored.sort(key=lambda x: x[0], reverse=True)
        for score, name, p, s, desc in scored[:3]:
            suggestions.append(
                SuggestionItem(
                    kind="harmony",
                    label=name,
                    category="Color Harmony",
                    description=desc,
                    payload={"scheme_name": name, "primary": p, "secondary": s},
                    score=score,
                    extra={"primary": p, "secondary": s},
                )
            )
        return suggestions
