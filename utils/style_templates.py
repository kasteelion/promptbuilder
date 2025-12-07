"""Base art style templates for quick style creation."""


TEMPLATES = {
    "Blank": {
        "description": "Start from scratch",
        "content": ""
    },
    
    "Photorealistic": {
        "description": "Realistic photo-quality rendering",
        "content": """**Rendering Quality:** Photorealistic, highly detailed, 8K quality, professional photography
**Character Accuracy:** Perfect anatomical proportions, realistic human features, natural skin textures
**Body Types:** Natural realistic body proportions and variations
**Hair & Clothing:** Realistic hair physics and textures, fabric behaves naturally with realistic folds and materials
**Details:** Intricate fine details, realistic lighting and shadows, natural color grading, depth of field"""
    },
    
    "Anime Style": {
        "description": "Japanese anime aesthetic",
        "content": """**Rendering Quality:** Clean anime art style, vibrant colors, sharp linework, cel-shaded
**Character Accuracy:** Anime proportions with large expressive eyes, stylized features
**Body Types:** Anime body proportions, idealized figures
**Hair & Clothing:** Anime hair with distinctive colors and gravity-defying styles, flowing fabric with dramatic folds
**Details:** Bold outlines, vibrant color palette, dramatic highlights and shadows, glossy finish"""
    },
    
    "Oil Painting": {
        "description": "Traditional oil painting style",
        "content": """**Rendering Quality:** Oil painting technique, visible brush strokes, rich color depth, artistic composition
**Character Accuracy:** Painterly interpretation of human form, classical art proportions
**Body Types:** Traditional artistic body proportions
**Hair & Clothing:** Painted texture with visible brush strokes, fabric with artistic folds
**Details:** Thick paint texture, layered colors, masterful lighting, museum quality"""
    },
    
    "Comic Book": {
        "description": "Western comic book art",
        "content": """**Rendering Quality:** Comic book illustration style, bold inking, dynamic composition, action-oriented
**Character Accuracy:** Heroic proportions, strong defined features, dramatic musculature
**Body Types:** Superhero physiques, exaggerated athletic builds
**Hair & Clothing:** Dynamic hair suggesting motion, spandex and costume materials with bold colors
**Details:** Heavy black outlines, Ben-Day dots optional, vibrant primary colors, dynamic action lines"""
    },
    
    "Watercolor": {
        "description": "Soft watercolor painting",
        "content": """**Rendering Quality:** Watercolor technique, soft edges, translucent layers, artistic fluidity
**Character Accuracy:** Gentle interpretation of features, soft proportions
**Body Types:** Natural flowing body shapes
**Hair & Clothing:** Flowing watercolor washes, soft fabric interpretation
**Details:** Color bleeding and blooming, wet-on-wet effects, delicate highlights, artistic spontaneity"""
    },
    
    "Digital Art": {
        "description": "Modern digital illustration",
        "content": """**Rendering Quality:** Clean digital artwork, smooth gradients, professional polish, contemporary style
**Character Accuracy:** Accurate proportions with slight stylization, modern beauty standards
**Body Types:** Contemporary idealized proportions
**Hair & Clothing:** Digitally rendered hair with smooth gradients, modern fashion with clean rendering
**Details:** Smooth blending, digital effects, modern color palette, professional finish"""
    },
    
    "Pixel Art": {
        "description": "Retro pixel graphics",
        "content": """**Rendering Quality:** Pixel art style, limited resolution, retro gaming aesthetic, chunky pixels
**Character Accuracy:** Simplified proportions suitable for pixel representation
**Body Types:** Simplified blocky body shapes
**Hair & Clothing:** Pixelated representation, limited color palette, iconic simplified designs
**Details:** Dithering for shading, limited color palette, crisp pixel edges, nostalgic retro feel"""
    },
    
    "Sketch Drawing": {
        "description": "Pencil sketch style",
        "content": """**Rendering Quality:** Pencil sketch technique, visible pencil strokes, rough artistic lines, study quality
**Character Accuracy:** Anatomical study proportions, gestural drawing
**Body Types:** Natural figure drawing proportions
**Hair & Clothing:** Sketched textures, loose fabric indication
**Details:** Cross-hatching for shadows, sketch lines, paper texture visible, artistic spontaneity"""
    },
    
    "3D Render": {
        "description": "CGI 3D rendered look",
        "content": """**Rendering Quality:** 3D CGI rendering, smooth surfaces, ray-traced lighting, computer-generated
**Character Accuracy:** Perfect symmetrical proportions, mathematical precision
**Body Types:** Modeled body types with smooth topology
**Hair & Clothing:** Simulated hair physics, cloth simulation with realistic draping
**Details:** Subsurface scattering, ambient occlusion, physically-based rendering, crisp details"""
    },
    
    "Manga Style": {
        "description": "Black and white manga",
        "content": """**Rendering Quality:** Black and white manga illustration, screentones, dramatic inking
**Character Accuracy:** Manga proportions, expressive faces, detailed eyes
**Body Types:** Manga figure types ranging from realistic to stylized
**Hair & Clothing:** Detailed hair with individual strands indicated, fabric with screentone shading
**Details:** Speed lines, screentones for shading, high contrast black and white, emotional expression"""
    },
    
    "Impressionist": {
        "description": "Impressionist painting style",
        "content": """**Rendering Quality:** Impressionist technique, broken color, visible brush strokes, light-focused
**Character Accuracy:** Impressionistic interpretation, suggestion rather than detail
**Body Types:** Loosely defined forms with emphasis on light
**Hair & Clothing:** Dabs of color suggesting texture, fabric indicated by color and light
**Details:** Broken brush strokes, emphasis on light effects, outdoor quality, artistic interpretation"""
    },
    
    "Art Nouveau": {
        "description": "Decorative Art Nouveau style",
        "content": """**Rendering Quality:** Art Nouveau aesthetic, flowing organic lines, decorative ornamental quality
**Character Accuracy:** Elongated graceful proportions, stylized elegant features
**Body Types:** Elegant elongated figures
**Hair & Clothing:** Flowing hair incorporated into decorative elements, fabric with sinuous folds
**Details:** Organic floral motifs, curved flowing lines, rich decorative borders, vintage color palette"""
    },
    
    "Minimalist": {
        "description": "Simple minimalist design",
        "content": """**Rendering Quality:** Minimalist style, simple shapes, flat colors, clean design
**Character Accuracy:** Simplified geometric shapes representing figures
**Body Types:** Simplified abstract forms
**Hair & Clothing:** Solid color blocks, minimal detail suggestion
**Details:** Flat colors, negative space, essential elements only, modern clean aesthetic"""
    },
    
    "Gothic Dark": {
        "description": "Dark gothic atmosphere",
        "content": """**Rendering Quality:** Gothic art style, dark moody atmosphere, dramatic contrast, mysterious
**Character Accuracy:** Pale dramatic features, gothic beauty standards
**Body Types:** Slender elegant or dramatic proportions
**Hair & Clothing:** Dark flowing hair, Victorian or gothic fashion with intricate details
**Details:** High contrast lighting, dark color palette, ornate details, mysterious shadows"""
    },
    
    "Pop Art": {
        "description": "Bold pop art style",
        "content": """**Rendering Quality:** Pop art aesthetic, bold flat colors, strong outlines, commercial art influence
**Character Accuracy:** Simplified iconic features, graphic representation
**Body Types:** Simplified graphic body shapes
**Hair & Clothing:** Solid color areas, simplified patterns, retro fashion
**Details:** Ben-Day dots, bold primary colors, strong black outlines, graphic impact"""
    },
    
    "Fantasy Illustration": {
        "description": "Epic fantasy artwork",
        "content": """**Rendering Quality:** Fantasy illustration style, rich detailed rendering, magical atmosphere
**Character Accuracy:** Idealized fantasy proportions, heroic or mystical features
**Body Types:** Fantasy archetypes from heroic to ethereal
**Hair & Clothing:** Elaborate fantasy hair, ornate armor or flowing robes with intricate details
**Details:** Magical effects, rich color palette, intricate details, epic composition"""
    },
    
    "Retro 80s": {
        "description": "1980s aesthetic",
        "content": """**Rendering Quality:** 1980s style, bright neon colors, geometric shapes, vintage quality
**Character Accuracy:** 80s beauty standards, big hair era proportions
**Body Types:** Athletic 80s physiques
**Hair & Clothing:** Big voluminous 80s hair, bold fashion with geometric patterns
**Details:** Neon color palette, grid patterns, geometric shapes, nostalgic 80s atmosphere"""
    },
    
    "Storybook": {
        "description": "Children's book illustration",
        "content": """**Rendering Quality:** Storybook illustration style, warm inviting colors, gentle rendering
**Character Accuracy:** Friendly approachable proportions, expressive faces
**Body Types:** Varied body types, inclusive representation
**Hair & Clothing:** Simple clear hair rendering, colorful comfortable clothing
**Details:** Soft edges, warm color palette, clear readable details, wholesome atmosphere"""
    },
    
    "Cyberpunk": {
        "description": "Futuristic cyberpunk style",
        "content": """**Rendering Quality:** Cyberpunk aesthetic, neon lights, high-tech details, dystopian atmosphere
**Character Accuracy:** Modern proportions with cybernetic enhancements possible
**Body Types:** Athletic or augmented builds
**Hair & Clothing:** Edgy modern hair with possible neon highlights, tech-wear and tactical fashion
**Details:** Neon lighting, holographic effects, gritty urban atmosphere, technological details"""
    },
    
    "Vintage Photograph": {
        "description": "Old photograph aesthetic",
        "content": """**Rendering Quality:** Vintage photograph style, aged quality, period-appropriate rendering
**Character Accuracy:** Natural proportions, period beauty standards
**Body Types:** Natural realistic body types
**Hair & Clothing:** Period-appropriate hairstyles and fashion, vintage styling
**Details:** Sepia or faded colors, film grain, vintage photographic effects, nostalgic quality"""
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
