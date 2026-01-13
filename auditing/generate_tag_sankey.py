
import os
import sys
import plotly.graph_objects as go
from collections import defaultdict
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

from logic.data_loader import DataLoader

def parse_metadata(file_path):
    """Parse metadata from a generated prompt file."""
    metadata = {
        'scene': None,
        'base_prompt': None,
        'characters': [],
        'outfits': []
    }
    
    try:
        text = Path(file_path).read_text(encoding="utf-8")
        lines = text.splitlines()
        
        in_metadata = False
        for line in lines:
            line = line.strip()
            if line == "# METADATA":
                in_metadata = True
                continue
            
            if in_metadata:
                if line.startswith("Scene:"):
                    metadata['scene'] = line.split(":", 1)[1].strip()
                elif line.startswith("Base_Prompt:"):
                    metadata['base_prompt'] = line.split(":", 1)[1].strip()
                elif line.startswith("Character:"):
                    # Format: Character: Name | Outfit: OutfitName | Pose: PoseName
                    parts = line.split("|")
                    char_part = parts[0].split(":", 1)[1].strip()
                    # Clean character name (remove trailing quotes if any or extra spaces)
                    metadata['characters'].append(char_part)
                    
                    if len(parts) > 1:
                        outfit_part = parts[1].split(":", 1)[1].strip()
                        metadata['outfits'].append(outfit_part)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        
    return metadata

def resolve_tags(metadata, loader_data):
    """Resolve names to tags using loaded data."""
    extracted = {
        'char_tags': set(),
        'scene_tags': set(),
        'style_tags': set(),
        'outfit_tags': set()
    }
    
    # 1. Character Tags
    for char_name in metadata['characters']:
        # Try exact match or loose match
        char_data = loader_data['characters'].get(char_name)
        if not char_data:
            # Try finding by key that resembles name
             for k, v in loader_data['characters'].items():
                 if k.replace("_", " ").lower() == char_name.lower():
                     char_data = v
                     break
        
        if char_data:
            tags = char_data.get('tags', [])
            extracted['char_tags'].update([t.lower() for t in tags])

    # 2. Scene Tags (Reverse Lookup by Description)
    target_desc = metadata['scene']
    if target_desc:
        target_desc_clean = target_desc.lower()
        found_scene = False
        for category, presets in loader_data['scenes'].items():
            for name, data in presets.items():
                # data is dict with 'description' and 'tags' or just string in old format (but randomizer normalized it)
                # DataLoader normalizes to dict usually? Checking loader...
                # Loader returns: {Category: {PresetName: {description: "", tags: []}}}
                desc = data.get('description', '').lower()
                # Fuzzy match: is the metadata scene starting with or contained in the preset description?
                # Randomizer output usually matches preset description exactly OR is the preset description.
                if desc and (desc in target_desc_clean or target_desc_clean in desc):
                    extracted['scene_tags'].update([t.lower() for t in data.get('tags', [])])
                    # Add Category as a tag too, it's useful
                    extracted['scene_tags'].add(category.lower())
                    found_scene = True
                    break
            if found_scene:
                break

    # 3. Style Tags
    style_name = metadata['base_prompt']
    if style_name:
        style_data = loader_data['base_prompts'].get(style_name)
        if style_data:
             extracted['style_tags'].update([t.lower() for t in style_data.get('tags', [])])

    # 4. Outfit Tags
    # Outfits in characters are merged, but we can look up in shared outfits if generic,
    # OR look up in the character's specific outfit definition if we found the character.
    # Metadata lists all outfits, but doesn't link them to specific char (order works though).
    # Since we aggregate tags, we just dump all outfit tags found.
    
    # We need to map outfit name back to data. Use shared outfits primarily.
    shared_outfits = loader_data['outfits'] # {F: {}, M: {}} keys are suffixes
    
    for outfit_name in metadata['outfits']:
        if outfit_name == "None": continue
        
        found_outfit = False
        # Search shared
        for gender, categories in shared_outfits.items():
            # outfits is { Category: { Name: Data } }
            for category, outfit_map in categories.items():
                if outfit_name in outfit_map:
                    data = outfit_map[outfit_name]
                    extracted['outfit_tags'].update([t.lower() for t in data.get('tags', [])])
                    found_outfit = True
                    break
            if found_outfit:
                break
        
        # If not in shared, might be unique to character. 
        # But for this high-level view, shared is usually enough.
        
    return extracted

# Tag Category Mappings for Simplification
TAG_CATEGORIES = {
    'Anatomy/Body': ['curvy', 'hourglass', 'petite', 'tall', 'busty', 'thick', 'substantial', 'toned', 'muscular', 'slim', 'athletic', 'frame', 'proportions', 'shape', 'density', 'silhouett'],
    'Face/Features': ['face', 'eyes', 'lips', 'nose', 'brows', 'cheek', 'complexion', 'expression', 'chin', 'jawline', 'forehead'],
    'Hair/Style': ['hair', 'wave', 'curl', 'straight', 'density', 'volume', 'part', 'length', 'chestnut', 'espresso', 'caramel', 'blowout'],
    'Mood/Vibe': ['confident', 'sultry', 'calm', 'approach', 'friendly', 'intense', 'serious', 'happy', 'focused', 'energy', 'expression'],
    'Theme/Genre': ['fantasy', 'medieval', 'sci-fi', 'cyberpunk', 'modern', 'gothic', 'retro', 'vintage', 'historical', 'futuristic', 'noir', 'mytholog', 'traditional'],
    'Action/Pose': ['stand', 'sit', 'lean', 'run', 'walk', 'jump', 'dodge', 'fight', 'pose', 'action', 'interact', 'cradl', 'shoot', 'pitch', 'catch']
}

def get_tag_category(tag, default="Other"):
    t = tag.lower()
    for cat, keywords in TAG_CATEGORIES.items():
        if any(kw in t for kw in keywords):
            return cat
    return default

def generate_sankey():
    print("Loading data...")
    loader = DataLoader()
    
    # Load all data types
    data_store = {
        'characters': loader.load_characters(),
        'scenes': loader.load_presets('scenes.md'),
        'base_prompts': loader.load_base_prompts(),
        'outfits': loader.load_outfits()
    }
    
    prompts_dir = Path("output/prompts")
    if not prompts_dir.exists():
        print("No output/prompts directory found.")
        return

    print("Analyzing prompts...")
    
    # Flow Counters
    # CharTag -> SceneTag
    # SceneTag -> StyleTag 
    # StyleTag -> OutfitTag
    
    c2s = defaultdict(int)
    s2st = defaultdict(int)
    st2o = defaultdict(int)
    
    # We need to limit the NUMBER of tags or it will explode.
    # Approach: 
    # 1. Count global frequency of all tags. Keep top N most common tags per category.
    # 2. Or just aggregate strictly.
    
    prompt_files = list(prompts_dir.glob("*.txt"))
    print(f"Found {len(prompt_files)} prompts.")
    
    for p in prompt_files:
        meta = parse_metadata(p)
        tags = resolve_tags(meta, data_store)
        
        # Aggregate tags into categories for cleaner flow
        char_cats = {get_tag_category(t, "Char") for t in tags['char_tags']}
        scene_cats = {get_tag_category(t, "Scene") for t in tags['scene_tags']}
        style_cats = {get_tag_category(t, "Style") for t in tags['style_tags']}
        outfit_cats = {get_tag_category(t, "Outfit") for t in tags['outfit_tags']}

        # Link Scene Categories -> Style Categories
        for sc in scene_cats:
            for st in style_cats:
                s2st[(sc, st)] += 1
                
        # Link Scene Categories -> Style Categories
        for sc in scene_cats:
            for st in style_cats:
                s2st[(sc, st)] += 1
                
        # Link Style Categories -> Outfit Categories
        for st in style_cats:
            for oc in outfit_cats:
                st2o[(st, oc)] += 1
                
    # Filter for top connections to avoid visual clutter
    TOP_N = 200
    
    def get_top_links(link_dict, limit):
        return sorted(link_dict.items(), key=lambda x: x[1], reverse=True)[:limit]
        
    top_s2st = get_top_links(s2st, 500)
    top_st2o = get_top_links(st2o, 500)
    
    # Build Node List
    labels = []
    label_map = {}
    
    def get_id(label, prefix):
        full_label = f"{prefix}: {label}" # Aggregated labels don't need .title() usually
        if full_label not in label_map:
            label_map[full_label] = len(labels)
            labels.append(full_label)
        return label_map[full_label]
        
    sources = []
    targets = []
    values = []
    
    # S -> Sty
    for (src, dst), count in top_s2st:
        s_id = get_id(src, "Scene")
        t_id = get_id(dst, "Style")
        sources.append(s_id)
        targets.append(t_id)
        values.append(count)
        
    # S -> Sty
    for (src, dst), count in top_s2st:
        s_id = get_id(src, "Scene")
        t_id = get_id(dst, "Style")
        sources.append(s_id)
        targets.append(t_id)
        values.append(count)
        
    # Style -> Outfit
    for (src, dst), count in top_st2o:
        s_id = get_id(src, "Style")
        t_id = get_id(dst, "Outfit")
        sources.append(s_id)
        targets.append(t_id)
        values.append(count)
        
    # Aesthetic Palette
    COLOR_BLUE = '#5C42E2'
    COLOR_PURPLE = '#A163E5'
    COLOR_PINK = '#FF6B8B'

    # Plot
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=15,
            line=dict(color="#333", width=0.5),
            label=labels,
            # Color logic: Alignment with Section 1
            color=[COLOR_BLUE if "Scene:" in l else 
                   COLOR_PURPLE if "Style:" in l else 
                   COLOR_PINK if "Outfit:" in l else 
                   COLOR_BLUE for l in labels]
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            label=[str(v) for v in values],
            color="rgba(161, 99, 229, 0.4)"
        )
    )])
    
    fig.update_layout(
        title_text="Tag Distribution Flow (Scene -> Style -> Outfit)",
        font_size=10,
        height=800,
        width=1600
    )
    
    output_path = Path("auditing/reports/tag_distribution_sankey.html")
    img_path = Path("auditing/reports/tag_distribution_sankey.png")
    
    fig.write_html(str(output_path))
    print(f"Saved HTML to {output_path}")
    
    try:
        # Static image requires kaleido usually, might fail if not installed
        fig.write_image(str(img_path))
        print(f"Saved PNG to {img_path}")
    except Exception:
        print("Could not save PNG (kaleido might be missing), but HTML is ready.")

    # Generate Mermaid Diagram (Limit to Top 60 for edge safety)
    MERMAID_N = 60
    mermaid_s2st = get_top_links(s2st, 200)
    mermaid_st2o = get_top_links(st2o, 200)

    mermaid_path = Path("auditing/reports/tag_distribution_flow.md")
    generate_mermaid(mermaid_s2st, mermaid_st2o, mermaid_path)
    print(f"Saved Mermaid Markdown to {mermaid_path}")

def generate_mermaid(s2st, st2o, output_path):
    import json
    with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write("# Tag Distribution Flow\n\n")
        f.write("```mermaid\n")
        f.write("sankey-beta\n")
        
        def clean_label(text):
            safe = "".join(c for c in text if c.isalnum() or c in " /-")
            return f'"{safe[:30].strip()}"'

        # Scene -> Style
        for (src, dst), count in s2st:
            f.write(f"{clean_label(src)},{clean_label(dst)},{count}\n")

        # Style -> Outfit
        for (src, dst), count in st2o:
            f.write(f"{clean_label(src)},{clean_label(dst)},{count}\n")
            
        f.write("```\n")

if __name__ == "__main__":
    generate_sankey()
