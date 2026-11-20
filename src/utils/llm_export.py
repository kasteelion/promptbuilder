"""Utility for exporting application data in an LLM-friendly format."""

import random
from typing import Dict, Any
from utils.outfit_summary import generate_consolidated_outfit_data

def generate_llm_export_text(ctx: Any, is_audit: bool = False) -> str:
    """Generate a condensed text block for knowledge injection into an LLM.
    
    When is_audit=True, produces a heavily trimmed version (~5KB) containing
    only the information needed to judge outfit-scene coherence: scene constraints,
    outfit category names, and pose category names. The full character list, tag
    synonyms, and art style descriptions are omitted to keep the model focused.
    """
    
    lines = []
    
    if is_audit:
        # ── AUDIT MODE: Minimal catalog for judging coherence ──────────
        lines.append("### SCENE CONSTRAINTS (Use these to detect clashes) ###")
        if ctx.randomizer:
            for scene_tag, rules in sorted(ctx.randomizer.scene_constraints.items()):
                rule_str = []
                if "allowed" in rules:
                    rule_str.append(f"ALLOWED: {', '.join(rules['allowed'])}")
                if "blocked" in rules:
                    rule_str.append(f"BLOCKED: {', '.join(rules['blocked'])}")
                if rule_str:
                    lines.append(f"- {scene_tag}: {' | '.join(rule_str)}")
        lines.append("")
        
        # Compact outfit categories (just names + tags, no descriptions)
        lines.append("### OUTFIT CATEGORIES ###")
        from logic.feedback_loop import FeedbackLoop
        feedback = FeedbackLoop()
        low_quality = feedback.get_low_quality_names()
        
        outfit_data = generate_consolidated_outfit_data()
        for cat_name in sorted(outfit_data.keys()):
            outfits = outfit_data[cat_name]
            names = []
            for out_name in sorted(outfits.keys()):
                # SANITIZATION: Skip templates or low quality
                if "template" in out_name.lower() or out_name in low_quality:
                    continue
                tags = outfits[out_name].get("tags", [])
                tag_str = f" [{', '.join(tags[:2])}]" if tags else ""
                names.append(f"{out_name}{tag_str}")
            if names:
                lines.append(f"**{cat_name}**: {', '.join(names)}")
        lines.append("")

        # Pose category names only
        lines.append("### POSE CATEGORIES ###")
        for cat, items in sorted(ctx.poses.items()):
            item_names = sorted(items.keys())
            display = ", ".join(item_names[:8])
            if len(item_names) > 8:
                display += f"... (+{len(item_names) - 8} more)"
            lines.append(f"- {cat}: {display}")
        
        return "\n".join(lines)
    
    # ── FULL MODE: Complete catalog for generation/enhancement ──────
    lines = [
        "### CATALOG KNOWLEDGE BASE ###",
        "You are an expert creative director. Use this data to validate or enhance prompts.",
        ""
    ]
    
    lines.extend([
        "### PROMPT CONFIG FORMAT ###",
        "PROMPT CONFIG",
        "Base: [Name of Art Style]",
        "Scene: [Paragraph describing environment and lighting]",
        "---",
        "[1] [Character Name]",
        "Outfit: [Outfit Name]",
        "Colors: [Color Scheme Name] (Only for 🎨 items)",
        "Sig: [Yes or No] (Only for ✨ items)",
        "Pose: [Pose Name or Custom Description]",
        "---",
        "Notes: [Interaction details between characters]",
        "",
    ])

    lines.append("--- CATALOG BEGINS ---")
    lines.append("")

    # 2. Scene Constraints (Critical for Coherence)
    lines.append("## SCENE CONSTRAINTS (Genre Firewalls)")
    lines.append("Use these rules to avoid mismatched content logic:")
    if ctx.randomizer:
        for scene_tag, rules in sorted(ctx.randomizer.scene_constraints.items()):
            rule_str = []
            if "allowed" in rules:
                rule_str.append(f"ALLOWED: {', '.join(rules['allowed'])}")
            if "blocked" in rules:
                rule_str.append(f"BLOCKED: {', '.join(rules['blocked'])}")
            
            if rule_str:
                lines.append(f"- **{scene_tag}**: {' | '.join(rule_str)}")
    lines.append("")

    # 3. Tag Logic (Synonyms)
    lines.append("## TAG LOGIC (Synonyms & Bridges)")
    lines.append("These tags are interchangeable or related:")
    if ctx.randomizer:
        for tag, aliases in sorted(ctx.randomizer.tag_aliases.items()):
            lines.append(f"- **{tag}**: {', '.join(aliases)}")
    lines.append("")

    # 4. Base Prompts (Art Styles)
    lines.append("## AVAILABLE ART STYLES (Base)")
    for name, data in sorted(ctx.base_prompts.items()):
        tags_str = ""
        desc_str = ""
        if isinstance(data, dict):
            t_list = data.get("tags", [])
            if t_list:
                tags_str = f" [Tags: {', '.join(t_list)}]"
            
            # Add a snippet of the description to help the AI understand the style
            desc = data.get("prompt", "")
            if desc:
                # Just first 80 chars to save tokens but give "vibe"
                desc_str = f" - {desc[:80]}..."
        
        lines.append(f"- {name}{tags_str}{desc_str}")
    lines.append("")

    # 5. Characters
    lines.append("## AVAILABLE CHARACTERS")
    lines.append("Format: Name [Signature Color] [Tags]")
    # Use characters_metadata as it's always populated (ctx.characters is lazy-loaded)
    for name, data in sorted(ctx.characters_metadata.items()):
        sig = getattr(data, "signature_color", "None")
        tags_list = getattr(data, "tags", [])
        if isinstance(data, dict):
            sig = data.get("signature_color", "None")
            tags_list = data.get("tags", [])
            
        tags = ", ".join(tags_list)
        lines.append(f"- {name} [{sig}] [{tags}]")
    lines.append("")

    # 6. Outfits (Consolidated)
    lines.append("## OUTFIT LIBRARY")
    lines.append("Legend: 🎨 = Team Colors, ✨ = Signature Color")
    
    outfit_data = generate_consolidated_outfit_data()
    from logic.feedback_loop import FeedbackLoop
    feedback = FeedbackLoop()
    low_quality = feedback.get_low_quality_names()

    for cat_name in sorted(outfit_data.keys()):
        outfits = outfit_data[cat_name]
        outfit_names = []
        for out_name in sorted(outfits.keys()):
            # SANITIZATION: Skip templates or low quality
            if "template" in out_name.lower() or out_name in low_quality:
                continue
                
            data = outfits[out_name]
            indicators = ""
            if data.get("has_color_scheme"):
                indicators += "🎨"
            if data.get("has_signature"):
                indicators += "✨"
            
            tags = data.get("tags", [])
            tag_str = f" [{', '.join(tags[:2])}]" if tags else ""
            
            variants = data.get("variants", [])
            v_str = f" (Variants: {', '.join(variants)})" if variants else ""
            
            outfit_names.append(f"{out_name}{indicators}{tag_str}{v_str}")
        
        # TRUNCATION: Limit to 15 outfits per category to save tokens
        if len(outfit_names) > 15:
            remainder = len(outfit_names) - 15
            outfit_names = outfit_names[:15]
            outfit_names.append(f"... (+{remainder} more)")
            
        if outfit_names:
            lines.append(f"### {cat_name}")
            lines.append(f"  * {', '.join(outfit_names)}")
    lines.append("")

    # 7. Poses
    lines.append("## PRESET POSES")
    for cat, items in sorted(ctx.poses.items()):
        item_names = sorted(items.keys())
        display_list = ", ".join(item_names)
        lines.append(f"  * {cat}: {display_list}")
    lines.append("")

    # 8. Color Schemes & Modifiers
    lines.append("## TEAM COLOR SCHEMES (Apply to 🎨 outfits)")
    lines.append(", ".join(sorted(ctx.color_schemes.keys())))
    
    lines.append("\n## OUTFIT MODIFIERS (Apply to 🛠️ outfits)")
    lines.append("Format: Trait Name")
    for mod_name in sorted(ctx.modifiers.keys()):
        lines.append(f"- {mod_name}")
    
    lines.append("\n--- CATALOG ENDS ---")
    
    return "\n".join(lines)

def get_content_creation_prompts(ctx: Any) -> Dict[str, str]:
    """Generate a dictionary of segmented prompts for LLM content creation."""
    
    # Common Header
    header = [
        "### CONTENT CREATION GUIDE for PromptBuilder ###",
        "You are a creative assistant helping to expand the PromptBuilder library.",
        "Your task is to generate NEW content that fits the application's specific syntax.",
        ""
    ]

    # Section 1: Characters
    char_section = [
        "### 1. CHARACTER SYNTAX ###",
        "Format (Markdown):",
        "### [Name]",
        "**Tags:** [comma, separated, tags]",
        "**Summary:** [2-3 sentences capturing their vibe]",
        "**Gender:** [F, M, or H (Hijabi)]",
        "**Signature Color:** [Hex Code]",
        "",
        "**Appearance:**",
        "* **Body:** [Description]",
        "* **Face:** [Description]",
        "* **Hair:** [Description]",
        "* **Skin:** [Description]",
        "",
        "**Age Presentation:** [e.g., mid-20s]",
        "**Vibe / Energy:** [keywords]",
        "**Bearing:** [how they move]",
        "",
        "**Outfits:**",
        "",
        "#### Base",
        "- **Top:** [Description]",
        "- **Bottom:** [Description]",
        "- **Footwear:** [Description]",
        "- **Accessories:** [Description]",
        "- **Hair/Makeup:** [Description]",
        ""
    ]

    # Section 2: Outfits
    outfit_section = [
        "### 2. OUTFIT SYNTAX ###",
        "Format (Saved as .txt file):",
        "tags: [Tag1, Tag2, Tag3]",
        "",
        "[F]",
        "- **Top:** [Description for Femme frame]",
        "- **Bottom:** [Description]",
        "",
        "[M]",
        "- **Top:** [Description for Masc frame]",
        "- **Bottom:** [Description]",
        "",
        "[H]",
        "- **Top:** [Description for Hijabi frame]",
        "- **Bottom:** [Description]",
        "",
        "Rules:",
        "- Start file with 'tags: [...]' header.",
        "- Create sections using [F], [M], [H] headers to handle gender variations.",
        "- Use detailed, visual descriptions.",
        "- Use {primary_color}, {secondary_color}, {accent} placeholders for team outfits.",
        "- Use ((default:color) or (signature)) for signature color support.",
        ""
    ]

    # Section 3 & 4: Poses and Interactions
    pose_interaction_section = [
        "### 3. POSE SYNTAX ###",
        "Format (Markdown):",
        "- **[Pose Name]:** [Detailed visual description of the pose, camera angle, and expression]",
        "",
        "### 4. INTERACTION SYNTAX ###",
        "Format (Markdown):",
        "- **[Interaction Name]:** {char1} [action] {char2} [action]. [Description of visual connection].",
        "",
        "Rules:",
        "- Use {char1}, {char2}, {char3} placeholders.",
        "- Focus on physical positioning and emotional connection.",
        ""
    ]

    # Section 5: Base Prompts (Art Styles)
    base_prompt_section = [
        "### 5. BASE PROMPT (ART STYLE) SYNTAX ###",
        "Format (Markdown):",
        "## [Style Name]",
        "[Detailed prompt description including medium, lighting, color palette, and rendering style]",
        "",
        "Rules:",
        "- This is the root style for the generation.",
        "- Focus on artistic medium (e.g., 'Oil painting', '3D render', 'Polaroid photo').",
        "- Include specific artists or eras if relevant (e.g., '1980s anime', 'Art Deco').",
        ""
    ]

    # Section 6: Scenes
    scene_section = [
        "### 6. SCENE SYNTAX ###",
        "Format (Markdown):",
        "## [Category Name] (e.g., 'Nature & Outdoors')",
        "- **[Scene Name]:** [Detailed description of environment, lighting, and mood].",
        "",
        "Rules:",
        "- Describe the background independent of characters.",
        "- Focus on lighting, weather, depth, and environmental details.",
        ""
    ]

    # Common Norms
    common_norms = [
        "### CURRENT NORMS (Elite Standard) ###",
        "- **Photorealistic First:** Assume the default output is high-fidelity photography unless specified otherwise. Lighting and texture (skin, fabric) are paramount.",
        "- **Detail Level:** Extreme. Focus on visual descriptors (subsurface scattering, fabric weight, ambient occlusion).",
        "- **Genre Consistency:** Respect genre boundaries. Do not mix High Fantasy elements with Modern Tech unless 'Portal' or 'Crossover' is the explicit theme.",
        "- **Creativity:** Encourage unique, diverse, and specific character designs. Avoid generic 'attractive' descriptors; use specific anatomical and stylistic terms.",
        ""
    ]

    # Character Specific Norms
    char_norms = [
        "#### CHARACTER DESCRIPTION STYLE",
        "- **Phrasing:** Use semicolon-separated phrases for physical descriptions (e.g., 'Natural frame; balanced athletic build; grounded presence').",
        "- **Measurements:** Avoid numerical height/weight. Use qualitative descriptors (e.g., 'moderate height', 'soft jawline', 'vertical line').",
        "- **Structure:** generally follow this flow: Physical Structure -> Specific Features (Face/Eyes) -> Vibe/Presence.",
        "- **Hair:** Specify type (e.g., 'Type 3B–3C curls'), density, and styling options.",
        "- **Required Fields:** Ensure 'Gender', 'Signature Color', 'Age Presentation', 'Vibe / Energy', and 'Bearing' are always included.",
        "",
        "#### RECOMMENDED DESCRIPTIVE FRAMEWORKS",
        "Use these frameworks to ensure precise, modular descriptions:",
        "",
        "**1. BODY ARCHITECTURE:**",
        "- **Kibbe Types:** (e.g., 'Soft Natural', 'Dramatic Classic') for bone structure and clothing lines.",
        "- **Fruit/Shape:** (e.g., 'Pear', 'Inverted Triangle') for silhouette distribution.",
        "- **Somatotype:** (Ectomorph, Mesomorph, Endomorph) for musculature baseline.",
        "",
        "**2. HAIR TEXTURE:**",
        "- **Andre Walker System:** Always specify type (1a-4c) (e.g., 'Type 3B–3C curls').",
        "- **Density:** Mention if hair is 'high density', 'fine', or 'thick'.",
        "",
        "**3. COLOR & LIGHT:**",
        "- **Seasonal Color Analysis:** (e.g., 'Deep Autumn', 'Bright Spring') to guide complexion and signature color.",
        "- **Skin Undertone:** Explicitly state Warm, Cool, Neutral, or Olive.",
        ""
    ]

    # Outfit Specific Norms
    outfit_norms = [
        "#### OUTFIT DESIGN FRAMEWORKS",
        "- **Silhouette & Cut:** Use terms like 'A-line', 'Oversized', 'Tailored', 'Draped' to define shape.",
        "- **Fabric & Texture:** Always specify material properties (e.g., 'matte leather', 'sheer chiffon', 'chunky knit').",
        "- **Aesthetics:** Reference specific styles (e.g., 'Dark Academia', 'Streetwear', 'High Fantasy').",
        ""
    ]

    # Pose/Interaction Specific Norms
    pose_norms = [
        "#### POSES & COMPOSITION FRAMEWORKS",
        "- **Line of Action:** Describe the flow of the body (e.g., 'dynamic S-curve', 'grounded stance').",
        "- **Camera Angles:** Specify viewpoint (e.g., 'low angle', 'eye level', 'Dutch angle').",
        "- **Laban/Effort:** Use movement qualities (e.g., 'heavy/grounded', 'light/floating') for dynamic poses.",
        "",
        "#### INTERACTIONS & PROXEMICS FRAMEWORKS",
        "- **Proxemics:** Define physical distance (Intimate, Personal, Social).",
        "- **Power Dynamics:** Describe high/low status through positioning (e.g., 'standing over', 'kneeling').",
        "- **Eye Contact:** Specify the gaze vector (e.g., 'locked gaze', 'averted eyes').",
        ""
    ]

    # Scene Specific Norms
    scene_norms = [
        "#### SCENE & ENVIRONMENT FRAMEWORKS",
        "- **Lighting Key:** Specify High Key (bright/optimistic) or Low Key (dark/dramatic).",
        "- **Atmosphere:** Describe particulates (e.g., 'dust motes', 'fog', 'rain', 'haze').",
        "- **Depth:** Use foreground/midground/background layering to create 3D space.",
        "- **Color Grading:** Suggest a cinematic palette (e.g., 'teal and orange', 'sepia tone').",
        ""
    ]

    # Footer
    footer = [
        "### TASK ###",
        "Please generate the following new content:"
    ]

    return {
        "Full Guide": "\n".join(header + char_section + outfit_section + pose_interaction_section + base_prompt_section + scene_section + common_norms + char_norms + outfit_norms + pose_norms + scene_norms + footer),
        "Characters": "\n".join(header + char_section + common_norms + char_norms + footer),
        "Outfits": "\n".join(header + outfit_section + common_norms + outfit_norms + footer),
        "Poses & Interactions": "\n".join(header + pose_interaction_section + common_norms + pose_norms + footer),
        "Scenes": "\n".join(header + scene_section + common_norms + scene_norms + footer),
        "Base Prompts": "\n".join(header + base_prompt_section + common_norms + footer)
    }

def generate_roster_context(ctx: Any, character_pool: list[str] = None) -> str:
    """Export only character names and art style names for initial selection."""
    lines = ["### AVAILABLE ART STYLES ###"]
    
    # Shuffle styles to prevent primacy bias
    styles = list(ctx.base_prompts.keys())
    random.shuffle(styles)
    lines.append(", ".join(styles))
    
    lines.append("\n### AVAILABLE CHARACTER NAMES ###")
    available_chars = list(ctx.characters_metadata.keys())
    if character_pool:
        available_chars = [c for c in available_chars if c in character_pool]
        
    # Shuffle characters to prevent primacy bias
    random.shuffle(available_chars)
    lines.append(", ".join(available_chars))
    
    return "\n".join(lines)

def generate_character_gear_context(ctx: Any, selected_names: list[str]) -> str:
    """Export outfits and poses ONLY for the selected characters."""
    lines = [f"### DATA FOR SELECTED CHARACTERS: {', '.join(selected_names)} ###"]
    
    from utils.outfit_summary import generate_outfit_data
    global_outfits = generate_outfit_data()
    
    # 1. Characters Outfits (from metadata)
    for name in selected_names:
        data = ctx.characters_metadata.get(name)
        if not data:
            continue
        
        lines.append(f"\n## {name} OUTFITS")
        # Check if it has specific outfit descriptions or just tags
        outfits = {}
        if hasattr(data, "outfits"):
            outfits = data.outfits
        elif isinstance(data, dict):
            outfits = data.get("outfits", {})
            
        if outfits:
            for oname, odata in outfits.items():
                tags = []
                if isinstance(odata, dict):
                    tags = odata.get("tags", [])
                elif hasattr(odata, "tags"):
                    tags = odata.tags
                lines.append(f"- {oname} [{', '.join(tags[:3])}]")
        else:
            lines.append("- Base [Default]")
            
        # Add global outfits for the character's modifier
        mod = getattr(data, "gender", "F")
        if isinstance(data, dict):
             mod = data.get("gender", "F")
        if not mod:
            mod = "F"
        mod = mod.upper()
        
        if mod in global_outfits:
            from logic.feedback_loop import FeedbackLoop
            low_quality = FeedbackLoop().get_low_quality_names()
            
            lines.append(f"\n### Additional Global Outfits ({mod})")
            for cat, o_dict in sorted(global_outfits[mod].items()):
                # Filter templates/low quality
                names = [n for n in o_dict.keys() if "template" not in n.lower() and n not in low_quality]
                if names:
                    lines.append(f"- {cat}: {', '.join(names)}")

    # 2. Global Poses (trimmed)
    lines.append("\n## AVAILABLE POSES (Categorized)")
    for cat, items in sorted(ctx.poses.items()):
        item_names = sorted(items.keys())
        lines.append(f"- {cat}: {', '.join(item_names[:10])}")
        
    return "\n".join(lines)

def generate_character_appearance_context(ctx: Any, selected_names: list[str]) -> str:
    """Export appearance descriptions (Body, Face, Hair, Skin, Gender) for selected characters."""
    lines = [f"### APPEARANCE DATA FOR SELECTED CHARACTERS: {', '.join(selected_names)} ###"]
    
    for name in selected_names:
        data = ctx.characters_metadata.get(name)
        if not data:
            continue
        
        lines.append(f"\n## {name}")
        
        # Pull key traits
        gender = getattr(data, "gender", "F")
        if isinstance(data, dict):
             gender = data.get("gender", "F")
        lines.append(f"- **Gender:** {gender}")
        
        appearance = None
        if hasattr(data, "appearance"):
            appearance = data.appearance
        elif isinstance(data, dict):
            appearance = data.get("appearance")
            
        if appearance:
            # Handle both dict and Pydantic models
            get_trait = lambda d, t: d.get(t, "No description") if isinstance(d, dict) else getattr(d, t, "No description")
            
            lines.append(f"- **Body:** {get_trait(appearance, 'body')}")
            lines.append(f"- **Face:** {get_trait(appearance, 'face')}")
            lines.append(f"- **Hair:** {get_trait(appearance, 'hair')}")
            lines.append(f"- **Skin:** {get_trait(appearance, 'skin')}")
        
    return "\n".join(lines)
