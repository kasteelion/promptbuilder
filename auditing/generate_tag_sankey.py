
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
        
        # Link Char Tags -> Scene Tags
        for ct in tags['char_tags']:
            for st in tags['scene_tags']:
                c2s[(ct, st)] += 1
                
        # Link Scene Tags -> Style Tags
        for st in tags['scene_tags']:
            for sty in tags['style_tags']:
                s2st[(st, sty)] += 1
                
        # Link Style Tags -> Outfit Tags
        for sty in tags['style_tags']:
            for ot in tags['outfit_tags']:
                st2o[(sty, ot)] += 1
                
    # Filter for top connections to avoid visual clutter
    TOP_N = 200
    
    def get_top_links(link_dict, limit):
        return sorted(link_dict.items(), key=lambda x: x[1], reverse=True)[:limit]
        
    top_c2s = get_top_links(c2s, TOP_N)
    top_s2st = get_top_links(s2st, TOP_N)
    top_st2o = get_top_links(st2o, TOP_N)
    
    # Build Node List
    labels = []
    label_map = {}
    
    def get_id(label, prefix):
        full_label = f"{prefix}: {label.title()}"
        if full_label not in label_map:
            label_map[full_label] = len(labels)
            labels.append(full_label)
        return label_map[full_label]
        
    sources = []
    targets = []
    values = []
    
    # C -> S
    for (src, dst), count in top_c2s:
        s_id = get_id(src, "Char")
        t_id = get_id(dst, "Scene")
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
        
    # Sty -> O
    for (src, dst), count in top_st2o:
        s_id = get_id(src, "Style")
        t_id = get_id(dst, "Outfit")
        sources.append(s_id)
        targets.append(t_id)
        values.append(count)
        
    # Plot
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            # Color logic: Purple (Char), Blue (Scene), Yellow (Style), Green (Outfit)
            color=["#e1bee7" if "Char:" in l else 
                   "#e1f5fe" if "Scene:" in l else 
                   "#fff9c4" if "Style:" in l else 
                   "#e8f5e9" for l in labels]
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values
        )
    )])
    
    fig.update_layout(
        title_text="Tag Distribution Flow (Character -> Scene -> Style -> Outfit)",
        font_size=10,
        height=800,
        width=1600
    )
    
    output_path = Path("output/reports/tag_distribution_sankey.html")
    img_path = Path("output/reports/tag_distribution_sankey.png")
    
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
    mermaid_c2s = get_top_links(c2s, MERMAID_N)
    mermaid_s2st = get_top_links(s2st, MERMAID_N)
    mermaid_st2o = get_top_links(st2o, MERMAID_N)

    mermaid_path = Path("output/reports/tag_distribution_flow.md")
    generate_mermaid(mermaid_c2s, mermaid_s2st, mermaid_st2o, mermaid_path)
    print(f"Saved Mermaid Markdown to {mermaid_path}")

def generate_mermaid(c2s, s2st, st2o, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Tag Distribution Flow\n\n")
        f.write("```mermaid\n")
        f.write("graph LR\n")
        
        # Styling
        f.write("  classDef char fill:#e1bee7,stroke:#4a148c,stroke-width:2px,color:#000;\n")
        f.write("  classDef scene fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000;\n")
        f.write("  classDef artstyle fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,color:#000;\n")
        f.write("  classDef outfit fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#000;\n\n")
        
        def clean_id(label):
            # Create a safe ID for Mermaid
            clean = "".join(c for c in label if c.isalnum())
            return clean if clean else "node"

        # Char -> Scene
        f.write("  %% Character Tags -> Scene Tags\n")
        for (src, dst), count in c2s:
            s_id = "C_" + clean_id(src)
            t_id = "S_" + clean_id(dst)
            f.write(f"  {s_id}([{src}]) -->|{count}| {t_id}([{dst}])\n")
            f.write(f"  class {s_id} char\n")
            f.write(f"  class {t_id} scene\n")
            
        # Scene -> Style
        f.write("\n  %% Scene Tags -> Style Tags\n")
        for (src, dst), count in s2st:
            s_id = "S_" + clean_id(src)
            t_id = "St_" + clean_id(dst)
            f.write(f"  {s_id} -->|{count}| {t_id}[{dst}]\n")
            f.write(f"  class {s_id} scene\n")
            f.write(f"  class {t_id} artstyle\n")

        # Style -> Outfit
        f.write("\n  %% Style Tags -> Outfit Tags\n")
        for (src, dst), count in st2o:
            s_id = "St_" + clean_id(src)
            t_id = "O_" + clean_id(dst)
            f.write(f"  {s_id} -->|{count}| {t_id}({dst})\n")
            f.write(f"  class {s_id} artstyle\n")
            f.write(f"  class {t_id} outfit\n")
            
        f.write("```\n")

if __name__ == "__main__":
    generate_sankey()
