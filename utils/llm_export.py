"""Utility for exporting application data in an LLM-friendly format."""

from typing import Dict, Any
from utils.outfit_summary import generate_consolidated_outfit_data

def generate_llm_export_text(ctx: Any) -> str:
    """Generate a condensed text block for knowledge injection into an LLM."""
    
    # 1. System Instructions
    lines = [
        "### SYSTEM INSTRUCTIONS for PromptBuilder ###",
        "You are an expert creative director. Your goal is to generate high-coherence image prompts.",
        "Output MUST be in the specific format below for the app to parse it.",
        "",
        "### COHERENCE RULES ###",
        "1. **Strict Base Styles**: The selected 'Base' (Art Style) sets the visual rules. Choose Poses and Outfits that match its Tags (e.g., if Base is 'Cyberpunk', strictly prefer Sci-Fi/Tech content).",
        "2. **Smart Defaults**: Gender variants ([F]/[M]/[H]) are handled automatically. You only need to select the Outfit Name.",
        "3. **Anatomy**: For complex poses, provide detailed anatomical descriptions in the 'Pose' field if a preset doesn't fit.",
        "",
        "### PROMPT CONFIG FORMAT ###",
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
        "--- CATALOG BEGINS ---",
        ""
    ]

    # 2. Base Prompts (Art Styles)
    lines.append("## AVAILABLE ART STYLES (Base)")
    for name, data in sorted(ctx.base_prompts.items()):
        tags_str = ""
        if isinstance(data, dict):
            t_list = data.get("tags", [])
            if t_list:
                tags_str = f" [Tags: {', '.join(t_list)}]"
        lines.append(f"- {name}{tags_str}")
    lines.append("")

    # 3. Characters
    lines.append("## AVAILABLE CHARACTERS")
    lines.append("Format: Name [Signature Color] [Tags]")
    for name, data in sorted(ctx.characters.items()):
        sig = data.get("signature_color", "None")
        tags = ", ".join(data.get("tags", []))
        lines.append(f"- {name} [{sig}] [{tags}]")
    lines.append("")

    # 4. Outfits (Consolidated)
    lines.append("## OUTFIT LIBRARY")
    lines.append("Legend: 🎨 = Team Colors, ✨ = Signature Color, 🛠️ = Traits")
    
    outfit_data = generate_consolidated_outfit_data()
    for cat_name in sorted(outfit_data.keys()):
        lines.append(f"### {cat_name}")
        outfits = outfit_data[cat_name]
        for out_name in sorted(outfits.keys()):
            data = outfits[out_name]
            indicators = ""
            if data.get("has_color_scheme"): indicators += " 🎨"
            if data.get("has_signature"): indicators += " ✨"
            if data.get("has_modifier"): indicators += " 🛠️"
            
            # Add Tags
            tags_str = ""
            t_list = data.get("tags", [])
            if t_list:
                tags_str = f" [Tags: {', '.join(t_list)}]"
                
            lines.append(f"  * {out_name}{indicators}{tags_str}")
    lines.append("")

    # 5. Poses
    lines.append("## PRESET POSES")
    for cat, items in sorted(ctx.poses.items()):
        item_list = ", ".join(sorted(items.keys()))
        lines.append(f"  * {cat}: {item_list}")
    lines.append("")

    # 6. Color Schemes
    lines.append("## TEAM COLOR SCHEMES (Apply to 🎨 outfits)")
    lines.append(", ".join(sorted(ctx.color_schemes.keys())))

    # 7. Modifiers
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
        "### CURRENT NORMS ###",
        "- **Detail Level:** High. Focus on visual descriptors (lighting, texture, fabric, emotion).",
        "- **Style:** Cinematic, photorealistic, or stylized art. Avoid generic descriptions.",
        "- **Creativity:** Encourage unique, diverse, and specific character designs.",
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
