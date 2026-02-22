"""Outfit templates for quick outfit creation."""

TEMPLATES = {
    "Blank": {"description": "Start from scratch", "content": ""},
    "Urban Minimalist": {
        "description": "Clean, modern street style",
        "content": """- **Top:** Boxy-fit heavyweight cotton t-shirt in charcoal
- **Bottom:** Tapered black cargo trousers with utility details
- **Footwear:** Chunky white technical sneakers
- **Accessories:** Silver chain necklace, black beanie
- **Hair/Makeup:** Messy bun; no makeup""",
    },
    "Executive Chic": {
        "description": "Modern high-powered business attire",
        "content": """- **Top:** Silk blouse with pussy-bow detail in ivory
- **Bottom:** High-waisted wide-leg wool trousers in navy
- **Footwear:** Pointed-toe patent leather stiletto pumps
- **Outerwear:** Structured oversized blazer matching trousers
- **Accessories:** Gold minimalist watch, leather structured tote
- **Hair/Makeup:** Sleek low ponytail; bold red lip""",
    },
    "Athleisure Luxe": {
        "description": "Premium workout-to-street look",
        "content": """- **Top:** Ribbed seamless crop top in sage green
- **Bottom:** High-waisted compression leggings in matching set
- **Footwear:** Designer retro-style running shoes
- **Outerwear:** Cropped puffer jacket in cream
- **Accessories:** Wireless headphones, canvas tote bag
- **Hair/Makeup:** Slicked back braid; fresh dewy skin""",
    },
    "Red Carpet Gala": {
        "description": "Show-stopping formal evening wear",
        "content": """- **Top:** Strapless corset bodice with crystal embellishments
- **Bottom:** Floor-length velvet mermaid skirt with high slit
- **Footwear:** Strappy metallic heels
- **Accessories:** Diamond drop earrings, silk opera gloves
- **Hair/Makeup:** Old Hollywood waves; smokey eye""",
    },
    "Cyberpunk Runner": {
        "description": "Futuristic tech-wear aesthetic",
        "content": """- **Top:** Asymmetric mesh paneled bodysuit
- **Bottom:** Tech-wear joggers with reflective straps
- **Footwear:** Heavy combat boots with neon accents
- **Outerwear:** Transparent vinyl cropped jacket
- **Accessories:** Visor glasses, tactical harness
- **Hair/Makeup:** Dyed streaks in hair; geometric liner""",
    },
    "K-Pop Sage": {
        "description": "High-energy performance outfit",
        "content": """- **Top:** Cropped metallic halter top with chain details
- **Bottom:** Pleated mini skirt with safety pin accents
- **Footwear:** Knee-high platform combat boots
- **Accessories:** Leather harness, fingerless gloves, choker
- **Hair/Makeup:** High pigtails; glitter eye makeup""",
    }
}


def get_template_names():
    """Get list of template names for dropdown."""
    return list(TEMPLATES.keys())


def get_template(name):
    """Get template data by name.

    Args:
        name: Template name

    Returns:
        String content or None if not found
    """
    template = TEMPLATES.get(name)
    return template.get("content") if template else None


def get_template_description(name):
    """Get template description.

    Args:
        name: Template name

    Returns:
        Description string or empty string if not found
    """
    template = TEMPLATES.get(name)
    return template.get("description", "") if template else ""
