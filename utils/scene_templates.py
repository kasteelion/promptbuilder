"""Scene templates for quick scene creation."""


TEMPLATES = {
    "Blank": {
        "description": "Start from scratch",
        "content": ""
    },
    
    "Sunny Park": {
        "description": "Bright outdoor park setting",
        "content": """Bright sunny park with lush green grass and scattered trees, warm natural lighting filtering through leaves, clear blue sky with few clouds, park benches and walking paths visible, vibrant flowers in background, cheerful outdoor atmosphere"""
    },
    
    "Cozy Café": {
        "description": "Warm indoor café environment",
        "content": """Warm cozy café interior with soft ambient lighting, wooden tables and comfortable chairs, coffee bar in background, warm color palette with browns and creams, gentle window light, plants and artwork on walls, inviting atmosphere"""
    },
    
    "Modern Office": {
        "description": "Clean professional workspace",
        "content": """Modern office space with clean lines and minimalist design, bright fluorescent or LED lighting, glass partitions and open floor plan, computers and office equipment visible, neutral color palette with blues and grays, professional corporate atmosphere"""
    },
    
    "Urban Street": {
        "description": "City street setting",
        "content": """Urban city street with buildings and storefronts, natural daylight with shadows from buildings, pedestrians and vehicles in background, street signs and urban details, concrete and asphalt textures, dynamic city atmosphere"""
    },
    
    "Beach Sunset": {
        "description": "Beach at golden hour",
        "content": """Beautiful beach at sunset with golden hour lighting, warm orange and pink sky, ocean waves gently rolling, sandy beach with footprints, palm trees or beach vegetation, peaceful romantic atmosphere"""
    },
    
    "Home Living Room": {
        "description": "Comfortable home interior",
        "content": """Comfortable living room with soft natural window light, couch and coffee table, home decorations and personal touches, warm color palette, carpet or wood flooring, relaxed homey atmosphere"""
    },
    
    "Gym Interior": {
        "description": "Fitness center environment",
        "content": """Modern gym interior with bright overhead lighting, exercise equipment visible in background, mirrors on walls, rubber flooring, motivational atmosphere, clean and energetic environment"""
    },
    
    "Night City": {
        "description": "Urban nighttime scene",
        "content": """City at night with neon signs and street lights, dramatic artificial lighting creating pools of light and shadow, illuminated buildings and storefronts, night sky, urban nightlife atmosphere"""
    },
    
    "Forest Path": {
        "description": "Natural forest setting",
        "content": """Dense forest with dappled sunlight filtering through tree canopy, dirt path winding through trees, lush green vegetation and ferns, natural earthy tones, peaceful nature atmosphere"""
    },
    
    "Art Studio": {
        "description": "Creative workspace",
        "content": """Artist studio with large windows providing natural light, easels and art supplies visible, paintings and sketches on walls, colorful paint splatters, creative bohemian atmosphere"""
    },
    
    "Rooftop Terrace": {
        "description": "Elevated outdoor space",
        "content": """Rooftop terrace with city skyline in background, evening or twilight lighting, modern outdoor furniture, potted plants and decorative lighting, sophisticated urban atmosphere"""
    },
    
    "Library Interior": {
        "description": "Quiet reading space",
        "content": """Traditional library with tall bookshelves filled with books, warm desk lamps providing focused lighting, wooden furniture and reading tables, quiet scholarly atmosphere, rich warm tones"""
    },
    
    "Mountain Vista": {
        "description": "Scenic mountain view",
        "content": """Mountain landscape with dramatic peaks in background, clear natural daylight, alpine vegetation or rocky terrain, vast open sky, expansive inspiring atmosphere"""
    },
    
    "Rainy Window": {
        "description": "Indoor looking out at rain",
        "content": """View from inside looking at rain through window, soft diffused overcast lighting, rain droplets on glass, blurred outdoor scene, cozy melancholic atmosphere, cool color temperature"""
    },
    
    "Dance Studio": {
        "description": "Practice space with mirrors",
        "content": """Dance or ballet studio with large mirrors covering walls, wooden floor, ballet barre along walls, bright even lighting, minimal decor, focused practice atmosphere"""
    },
    
    "Garden Patio": {
        "description": "Outdoor garden setting",
        "content": """Charming garden patio with flowering plants and greenery, natural sunlight with dappled shade, patio furniture and decorative elements, brick or stone paving, peaceful garden atmosphere"""
    },
    
    "Tech Startup": {
        "description": "Modern startup office",
        "content": """Contemporary tech startup office with open workspace, colorful modern furniture and bean bags, whiteboards with ideas, exposed brick or industrial elements, creative energetic atmosphere"""
    },
    
    "Concert Stage": {
        "description": "Performance venue",
        "content": """Concert stage with dramatic stage lighting (spotlights and colored lights), amplifiers and musical equipment visible, crowd in background, energetic performance atmosphere, dynamic lighting"""
    },
    
    "Autumn Path": {
        "description": "Fall season outdoor scene",
        "content": """Pathway lined with autumn trees displaying orange, red, and yellow leaves, fallen leaves on ground, soft autumn sunlight, cool crisp atmosphere, warm fall color palette"""
    },
    
    "Minimalist White": {
        "description": "Clean white background",
        "content": """Pure white minimalist background with soft even lighting, no distracting elements, clean professional studio atmosphere, simple and focused"""
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
        Dict with 'content' key, or None if not found
    """
    return TEMPLATES.get(name)


def get_template_description(name):
    """Get template description.
    
    Args:
        name: Template name
        
    Returns:
        Description string or empty string if not found
    """
    template = TEMPLATES.get(name)
    return template.get("description", "") if template else ""
