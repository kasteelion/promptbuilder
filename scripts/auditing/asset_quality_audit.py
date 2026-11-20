"""
Comprehensive Asset Quality Audit
Analyzes all assets (characters, outfits, scenes, poses, interactions) for:
- Cross-asset compatibility gaps
- Overly specific assets that may force prompt conflicts
- Missing combinations and synergy opportunities
- Tag coverage and orphan detection
"""

import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from logic.data_loader import DataLoader

def run_audit():
    d = DataLoader()
    d.clear_cache()

    chars = d.load_characters()
    bp = d.load_base_prompts()
    poses = d.load_presets("poses.md")
    scenes = d.load_presets("scenes.md")
    interactions = d.load_interactions()
    tags_by_cat = d.load_categorized_tags()
    all_tags = [t for tags in tags_by_cat.values() for t in tags]

    # Flatten outfit categories from characters
    all_outfit_cats = set()
    char_outfit_map = {}
    for name, cdata in chars.items():
        oc = cdata.get("outfits_categorized", {})
        char_outfit_map[name] = oc
        all_outfit_cats.update(oc.keys())

    # Shared outfits from folder
    outfit_dir = Path(__file__).parent.parent.parent / "assets" / "data" / "outfits"
    shared_outfit_cats = {}
    if outfit_dir.exists():
        for cat_dir in sorted(outfit_dir.iterdir()):
            if cat_dir.is_dir():
                outfits = [f.stem for f in cat_dir.glob("*.txt")]
                shared_outfit_cats[cat_dir.name] = outfits

    print("=" * 80)
    print("ASSET QUALITY AUDIT REPORT")
    print("=" * 80)

    # ===== SECTION 1: ASSET INVENTORY =====
    print("\n## 1. ASSET INVENTORY")
    print(f"  Characters:       {len(chars)}")
    print(f"  Base Prompts:     {len(bp)}")
    print(f"  Pose Categories:  {len(poses)} -> {sum(len(v) for v in poses.values())} presets")
    print(f"  Scene Categories: {len(scenes)} -> {sum(len(v) for v in scenes.values())} presets")
    print(f"  Interaction Cats: {len(interactions)} -> {sum(len(v) for v in interactions.values())} presets")
    print(f"  Shared Outfit Cats: {len(shared_outfit_cats)} -> {sum(len(v) for v in shared_outfit_cats.values())} outfits")
    print(f"  Tag Categories:   {len(tags_by_cat)} -> {len(all_tags)} tags")

    # ===== SECTION 2: CHARACTER TAG COVERAGE =====
    print("\n## 2. CHARACTER TAG COVERAGE")
    tag_usage = Counter()
    chars_without_tags = []
    chars_without_bearing = []
    chars_without_vibe = []
    chars_without_traits = []
    chars_with_few_outfits = []
    gender_dist = Counter()

    for name, char_obj in sorted(chars.items()):
        cdata = char_obj.dict() if hasattr(char_obj, "dict") else char_obj
        tags = cdata.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]
        for t in tags:
            tag_usage[t] += 1

        if not tags:
            chars_without_tags.append(name)
        if not cdata.get("bearing"):
            chars_without_bearing.append(name)
        if not cdata.get("vibe"):
            chars_without_vibe.append(name)
        if not cdata.get("traits"):
            chars_without_traits.append(name)

        outfit_count = sum(len(outfits) for outfits in cdata.get("outfits_categorized", {}).values())
        if outfit_count < 2:
            chars_with_few_outfits.append((name, outfit_count))

        gender_dist[cdata.get("gender", "unknown")] += 1

    print(f"  Gender: {dict(gender_dist)}")
    print(f"  Characters without tags: {len(chars_without_tags)}")
    if chars_without_tags:
        for c in chars_without_tags[:10]:
            print(f"    - {c}")
    print(f"  Characters without bearing: {len(chars_without_bearing)}")
    if chars_without_bearing:
        for c in chars_without_bearing:
            print(f"    - {c}")
    print(f"  Characters without vibe: {len(chars_without_vibe)}")
    if chars_without_vibe:
        for c in chars_without_vibe:
            print(f"    - {c}")
    print(f"  Characters without traits: {len(chars_without_traits)}")
    if chars_without_traits and len(chars_without_traits) < 20:
        for c in chars_without_traits:
            print(f"    - {c}")
    else:
        print(f"    ({len(chars_without_traits)} total)")
    print(f"  Characters with <2 outfits: {len(chars_with_few_outfits)}")
    if chars_with_few_outfits:
        for c, n in chars_with_few_outfits[:10]:
            print(f"    - {c} ({n} outfits)")

    # ===== SECTION 3: TAG DISTRIBUTION =====
    print("\n## 3. TAG DISTRIBUTION (most -> least)")
    orphan_tags = [t for t in all_tags if tag_usage.get(t, 0) == 0]
    rare_tags = [(t, c) for t, c in tag_usage.most_common() if c <= 2]
    dominant_tags = [(t, c) for t, c in tag_usage.most_common(10)]

    print("  Top 10 most used tags:")
    for t, c in dominant_tags:
        print(f"    {t}: {c} characters")
    print(f"\n  Orphan tags (in tags.md but no character uses): {len(orphan_tags)}")
    for t in orphan_tags[:15]:
        print(f"    - {t}")
    print(f"\n  Rare tags (<=2 characters): {len(rare_tags)}")
    for t, c in rare_tags[:15]:
        print(f"    - {t}: {c}")

    # ===== SECTION 4: POSE ANALYSIS =====
    print("\n## 4. POSE ANALYSIS")
    pose_tags = {}
    for cat, presets in poses.items():
        for name, desc in presets.items():
            desc_lower = str(desc).lower() if desc else ""
            pose_tags[f"{cat}/{name}"] = desc_lower

    print(f"  Pose categories: {sorted(poses.keys())}")
    for cat in sorted(poses.keys()):
        print(f"    {cat}: {len(poses[cat])} presets")

    # Check: poses that reference specific clothing or settings
    pose_clothing_refs = []
    for key, desc in pose_tags.items():
        clothing_words = ["dress", "skirt", "heels", "boots", "suit", "bikini", "gown", "uniform", "jersey"]
        found = [w for w in clothing_words if w in desc]
        if found:
            pose_clothing_refs.append((key, found))

    if pose_clothing_refs:
        print(f"\n  ⚠ Poses referencing specific clothing ({len(pose_clothing_refs)}):")
        for key, words in pose_clothing_refs[:10]:
            print(f"    - {key}: mentions {words}")

    # ===== SECTION 5: SCENE ANALYSIS =====
    print("\n## 5. SCENE ANALYSIS")
    print(f"  Scene categories: {sorted(scenes.keys())}")
    for cat in sorted(scenes.keys()):
        print(f"    {cat}: {len(scenes[cat])} presets")

    # Check: scenes that force specific character counts or genders
    scene_forcing = []
    for cat, presets in scenes.items():
        for name, desc in presets.items():
            desc_str = str(desc).lower() if desc else ""
            issues = []
            import re
            if re.search(r'\b(she|her)\b', desc_str):
                # Extra check to ensure it's not 'sheer' or 'hero'
                issues.append("gender-specific (she/her)")
            if re.search(r'\b(he|his|him)\b', desc_str):
                issues.append("gender-specific (he/his)")
            if "two " in desc_str or "both " in desc_str:
                issues.append("forces character count")
            if issues:
                scene_forcing.append((f"{cat}/{name}", issues))

    if scene_forcing:
        print(f"\n  ⚠ Scenes with forcing language ({len(scene_forcing)}):")
        for key, issues in scene_forcing[:15]:
            print(f"    - {key}: {', '.join(issues)}")

    # ===== SECTION 6: INTERACTION ANALYSIS =====
    print("\n## 6. INTERACTION ANALYSIS")
    print(f"  Interaction categories: {sorted(interactions.keys())}")
    for cat in sorted(interactions.keys()):
        print(f"    {cat}: {len(interactions[cat])} presets")

    # Check: interactions with placeholder usage
    placeholder_interactions = []
    no_placeholder_interactions = []
    for cat, presets in interactions.items():
        for name, data in presets.items():
            desc = ""
            if isinstance(data, dict):
                desc = str(data.get("description", ""))
            else:
                desc = str(data)
            if "{" in desc and "}" in desc:
                placeholder_interactions.append(f"{cat}/{name}")
            elif desc.strip():
                no_placeholder_interactions.append(f"{cat}/{name}")

    print(f"\n  With character placeholders: {len(placeholder_interactions)}")
    print(f"  Without placeholders (static): {len(no_placeholder_interactions)}")

    # ===== SECTION 7: SHARED OUTFIT ANALYSIS =====
    print("\n## 7. SHARED OUTFIT ANALYSIS")
    for cat_name, outfits in sorted(shared_outfit_cats.items()):
        print(f"  {cat_name}: {len(outfits)}")
        for o in sorted(outfits):
            print(f"    - {o}")

    # Check: outfit categories with very few options
    thin_cats = [(c, len(o)) for c, o in shared_outfit_cats.items() if len(o) <= 2]
    if thin_cats:
        print("\n  ⚠ Categories with <=2 outfits:")
        for c, n in thin_cats:
            print(f"    - {c}: {n}")

    # ===== SECTION 8: CROSS-ASSET COMPATIBILITY =====
    print("\n## 8. CROSS-ASSET COMPATIBILITY GAPS")

    # Build tag sets for each category
    base_prompt_tags = {}
    for name, data in bp.items():
        if isinstance(data, dict):
            bp_tags = data.get("tags", [])
        else:
            bp_tags = []
        if isinstance(bp_tags, str):
            bp_tags = [t.strip() for t in bp_tags.split(",") if t.strip()]
        base_prompt_tags[name] = set(t.lower() for t in bp_tags)

    # Check: base prompts with tags that have no matching poses
    pose_cat_lower = {c.lower(): c for c in poses.keys()}
    scene_cat_lower = {c.lower(): c for c in scenes.keys()}

    print("  Base Prompt -> Pose coverage:")
    for bp_name, bp_tag_set in sorted(base_prompt_tags.items()):
        matching_pose_cats = []
        for tag in bp_tag_set:
            for pc_lower, pc in pose_cat_lower.items():
                if tag in pc_lower or pc_lower in tag:
                    matching_pose_cats.append(pc)
        if not matching_pose_cats and bp_tag_set:
            print(f"    ⚠ {bp_name} (tags: {bp_tag_set}) -> no obvious matching pose category")

    print("\n  Base Prompt -> Scene coverage:")
    for bp_name, bp_tag_set in sorted(base_prompt_tags.items()):
        matching_scene_cats = []
        for tag in bp_tag_set:
            for sc_lower, sc in scene_cat_lower.items():
                if tag in sc_lower or sc_lower in tag:
                    matching_scene_cats.append(sc)
        if not matching_scene_cats and bp_tag_set:
            print(f"    ⚠ {bp_name} (tags: {bp_tag_set}) -> no obvious matching scene category")

    # ===== SECTION 9: CONFLICT DETECTION =====
    print("\n## 9. POTENTIAL PROMPT CONFLICTS")

    # Check: scenes or interactions that describe clothing in detail
    scene_clothing_conflicts = []
    for cat, presets in scenes.items():
        for name, desc in presets.items():
            desc_str = str(desc).lower() if desc else ""
            outfit_words = ["wearing", "dressed in", "clad in", "outfit", "costume", "clothing"]
            found = [w for w in outfit_words if w in desc_str]
            if found:
                scene_clothing_conflicts.append((f"{cat}/{name}", found))

    if scene_clothing_conflicts:
        print(f"  ⚠ Scenes describing clothing ({len(scene_clothing_conflicts)}) - may conflict with outfit system:")
        for key, words in scene_clothing_conflicts[:10]:
            print(f"    - {key}: mentions {words}")

    interaction_clothing = []
    for cat, presets in interactions.items():
        for name, data in presets.items():
            desc = str(data.get("description", "") if isinstance(data, dict) else data).lower()
            outfit_words = ["wearing", "dressed in", "outfit", "costume"]
            found = [w for w in outfit_words if w in desc]
            if found:
                interaction_clothing.append((f"{cat}/{name}", found))

    if interaction_clothing:
        print(f"  ⚠ Interactions describing clothing ({len(interaction_clothing)}) - may override outfit selection:")
        for key, words in interaction_clothing[:10]:
            print(f"    - {key}: mentions {words}")

    # ===== SECTION 10: GAP ANALYSIS =====
    print("\n## 10. ASSET GAP ANALYSIS")

    # Tag categories vs outfit categories
    outfit_cat_set = set(c.lower() for c in shared_outfit_cats.keys())
    scene_cat_set = set(c.lower() for c in scenes.keys())
    pose_cat_set = set(c.lower() for c in poses.keys())

    all_theme_words = set()
    for t in all_tags:
        all_theme_words.add(t.lower())
    for c in shared_outfit_cats.keys():
        all_theme_words.add(c.lower())
    for c in scenes.keys():
        all_theme_words.add(c.lower())
    for c in poses.keys():
        all_theme_words.add(c.lower())

    # Scenes without matching poses
    print("  Scene categories without obvious pose match:")
    for sc in sorted(scenes.keys()):
        sc_l = sc.lower()
        match = any(sc_l in pc.lower() or pc.lower() in sc_l for pc in poses.keys())
        if not match:
            print(f"    - Scene '{sc}' has no pose category with a similar name")

    # Poses without matching scenes
    print("\n  Pose categories without obvious scene match:")
    for pc in sorted(poses.keys()):
        pc_l = pc.lower()
        match = any(pc_l in sc.lower() or sc.lower() in pc_l for sc in scenes.keys())
        if not match:
            print(f"    - Pose '{pc}' has no scene category with a similar name")

    print("\n" + "=" * 80)
    print("END OF AUDIT")
    print("=" * 80)

if __name__ == "__main__":
    run_audit()
