"""Outfit templates for quick outfit creation."""

TEMPLATES = {
    "Blank": {"description": "Start from scratch", "content": ""},
    "Standard Format": {
        "description": "Standard markdown bullet format",
        "content": """- **Top:** [Description]
- **Bottom:** [Description]
- **Footwear:** [Description]
- **Accessories:** [Description]
- **Hair/Makeup:** [Description]""",
    },
    "Casual Daywear": {
        "description": "Simple casual look",
        "content": """- **Top:** Comfortable fitted cotton t-shirt in [color]
- **Bottom:** Well-fitted blue denim jeans
- **Footwear:** Clean white minimalist sneakers
- **Accessories:** Simple leather watch, small stud earrings
- **Hair/Makeup:** Natural loose hair; minimal fresh makeup""",
    },
    "Professional Business": {
        "description": "Formal business attire",
        "content": """- **Top:** Tailored blazer over a crisp button-down shirt
- **Bottom:** Pressed dress trousers or pencil skirt
- **Footwear:** Polished leather dress shoes or mid-height heels
- **Accessories:** Classic watch, professional leather bag
- **Hair/Makeup:** Neatly styled hair; natural professional makeup""",
    },
    "Athletic Training": {
        "description": "Sporty performance gear",
        "content": """- **Top:** Moisture-wicking performance tank or compression shirt
- **Bottom:** High-waisted athletic leggings or shorts
- **Footwear:** Technical running or cross-training shoes
- **Accessories:** Fitness tracker, water bottle nearby
- **Hair/Makeup:** Secure high ponytail; no makeup""",
    },
    "Evening Elegant": {
        "description": "Sophisticated formal look",
        "content": """- **Top:** Elegant silk blouse or tailored evening jacket
- **Bottom:** Flowing midi skirt or tailored trousers
- **Footwear:** Strappy heeled sandals or polished loafers
- **Accessories:** Statement necklace or cufflinks, small clutch
- **Hair/Makeup:** Polished updo or sleek waves; refined evening makeup""",
    },
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
