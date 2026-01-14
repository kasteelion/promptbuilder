import os
import sys
from collections import defaultdict
import plotly.graph_objects as go

# --- AESTHETIC CONFIG (Inspired by Reference) ---
COLOR_BLUE = '#5C42E2'   # Dominant/Success
COLOR_PURPLE = '#A163E5' # Secondary/Social
COLOR_PINK = '#FF6B8B'   # Spotlight/Interaction
COLOR_LIGHT_GRAY = '#F0F0F0'
# ------------------------------------------------

def parse_prompt_metadata(file_path):
    """Parse metadata from a generated prompt file."""
    metadata = {
        'scene': None,
        'base_prompt': None,
        'characters': [],
        'outfits': [],
        'poses': [],
        'interaction': None,
        'score': 0
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        in_metadata = False
        for line in lines:
            line = line.strip()
            
            if line == "# METADATA":
                in_metadata = True
                continue
            
            if not in_metadata or not line:
                if in_metadata and not line:
                    break  # End of metadata section
                continue
            
            if line.startswith("Scene:"):
                metadata['scene'] = line.split(":", 1)[1].strip()
            elif line.startswith("Base_Prompt:"):
                metadata['base_prompt'] = line.split(":", 1)[1].strip()
            elif line.startswith("Character:"):
                # Format: Character: Name | Outfit: OutfitName | Pose: PoseName
                parts = line.split("|")
                char_name = parts[0].split(":", 1)[1].strip()
                outfit = parts[1].split(":", 1)[1].strip() if len(parts) > 1 else "None"
                pose = parts[2].split(":", 1)[1].strip() if len(parts) > 2 else "None"
                
                metadata['characters'].append(char_name)
                metadata['outfits'].append(outfit)
                metadata['poses'].append(pose)
            elif line.startswith("Interaction:"):
                metadata['interaction'] = line.split(":", 1)[1].strip()
            elif line.startswith("Score:"):
                try:
                    metadata['score'] = int(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
    
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    
    return metadata

def create_sankey_diagram(style_to_scene, scene_to_outfit, outfit_to_interaction, output_path):
    """Create Sankey diagram: Style → Scene → Outfit → Interaction."""
    
    # Build Sankey data
    labels = []
    label_to_idx = {}
    
    def get_or_create_label(label):
        if label not in label_to_idx:
            label_to_idx[label] = len(labels)
            labels.append(label)
        return label_to_idx[label]
    
    sources = []
    targets = []
    values = []
    
    # 1. Style -> Scene
    for (style, scene), count in sorted(style_to_scene.items(), key=lambda x: x[1], reverse=True)[:100]:
        source_idx = get_or_create_label(f"Style: {style}")
        target_idx = get_or_create_label(f"Scene: {scene}")
        sources.append(source_idx)
        targets.append(target_idx)
        values.append(count)

    # 2. Scene -> Outfit
    for (scene, outfit), count in sorted(scene_to_outfit.items(), key=lambda x: x[1], reverse=True)[:100]:
        source_idx = get_or_create_label(f"Scene: {scene}")
        target_idx = get_or_create_label(f"Outfit: {outfit}")
        sources.append(source_idx)
        targets.append(target_idx)
        values.append(count)

    # 3. Outfit -> Interaction
    for (outfit, interaction), count in sorted(outfit_to_interaction.items(), key=lambda x: x[1], reverse=True)[:100]:
        source_idx = get_or_create_label(f"Outfit: {outfit}")
        target_idx = get_or_create_label(f"Vibe: {interaction}")
        sources.append(source_idx)
        targets.append(target_idx)
        values.append(count)
    
    # Sort logically for cleaner vertical layout (Dominant flows top)
    # We want "Style" and "Scene: Athletic" to appear high up
    def get_node_color(l):
        l_lower = l.lower()
        if "scene: athletic" in l_lower or "style: photo" in l_lower: return COLOR_BLUE
        if "scene: other" in l_lower: return COLOR_LIGHT_GRAY
        if "scene:" in l_lower: return COLOR_PURPLE
        if "vibe:" in l_lower: return COLOR_PINK
        if "outfit:" in l_lower: return COLOR_BLUE
        return "#CCCCCC"

    # Assign X-coordinates to force layer separation
    # Layer 1 (Styles): x=0.0, Layer 2 (Scenes): x=0.33, Layer 3 (Outfits): x=0.66, Layer 4 (Interactions): x=1.0
    node_x = []
    node_y = []
    for label in labels:
        if label.startswith("Style:"):
            node_x.append(0.0)
        elif label.startswith("Scene:"):
            node_x.append(0.33)
        elif label.startswith("Outfit:"):
            node_x.append(0.66)
        elif label.startswith("Vibe:"):
            node_x.append(1.0)
        else:
            node_x.append(0.5)  # Fallback
        node_y.append(0.5)  # Let Plotly auto-arrange vertically

    # Create Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        arrangement='snap',  # Force nodes to snap to X coordinates
        node=dict(
            pad=20,
            thickness=15,
            line=dict(color="#333", width=1),
            label=labels,
            color=[get_node_color(l) for l in labels],
            x=node_x,
            y=node_y
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            label=[str(v) for v in values], # Add link labels (counts)
            color="rgba(161, 99, 229, 0.4)" # Purple wash for links
        )
    )])
    
    fig.update_layout(
        title_text="Prompt Flow: Style → Scene → Outfit → Interaction",
        font_size=10,
        height=800,
        width=1800
    )
    
    # Save as image
    try:
        fig.write_image(output_path)
        print(f"📊 Sankey diagram saved to: {output_path}")
    except Exception as e:
        print(f"Warning: Could not save static image (kaleido might be missing): {e}")
    
    # Also save as HTML for interactive viewing
    html_path = output_path.replace('.png', '.html')
    fig.write_html(html_path)
    print(f"🌐 Interactive HTML saved to: {html_path}")

def create_mermaid_diagram(style_to_scene, scene_to_outfit, outfit_to_interaction, output_path):
    """Generate Mermaid diagram: Style → Scene → Outfit → Interaction."""
    
    import json
    with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write("# Prompt Distribution Flow\n\n")
        f.write("```mermaid\n")
        f.write("sankey-beta\n")
        
        def clean_label(text):
            # 1. Broadly filter but allow / and - for readability
            safe = "".join(c for c in text if c.isalnum() or c in " /->")
            return f'"{safe[:30].strip()}"'

        # 1. Style -> Scene (add layer prefixes)
        for (style, scene), count in sorted(style_to_scene.items(), key=lambda x: x[1], reverse=True)[:100]:
            f.write(f"{clean_label('1. ' + style)},{clean_label('2. ' + scene)},{count}\n")
        
        # 2. Scene -> Outfit (add layer prefixes)
        for (scene, outfit), count in sorted(scene_to_outfit.items(), key=lambda x: x[1], reverse=True)[:100]:
            f.write(f"{clean_label('2. ' + scene)},{clean_label('3. ' + outfit)},{count}\n")

        # 3. Outfit -> Interaction (add layer prefixes)
        for (outfit, interaction), count in sorted(outfit_to_interaction.items(), key=lambda x: x[1], reverse=True)[:100]:
            f.write(f"{clean_label('3. ' + outfit)},{clean_label('4. ' + interaction)},{count}\n")
            
        f.write("```\n")
        
    print(f"📊 Mermaid diagram saved to: {output_path}")

def create_style_census(style_counts, output_path):
    """Create a simple markdown table of style frequencies."""
    with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write("# Style Representation Census\n\n")
        f.write("| Base Style | Count | Percentage |\n")
        f.write("| :--- | :--- | :--- |\n")
        
        total = sum(style_counts.values())
        for style, count in sorted(style_counts.items(), key=lambda x: x[1], reverse=True):
            percent = (count / total) * 100
            f.write(f"| {style} | {count} | {percent:.1f}% |\n")
            
    print(f"📊 Style census saved to: {output_path}")

if __name__ == "__main__":
    # Default to generated_prompts_only directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir))) # auditing/visualizations -> auditing -> root -> UP one more? No.
    # __file__ = auditing/visualizations/script.py
    # dirname = auditing/visualizations
    # dirname(dirname) = auditing
    # dirname(dirname(dirname)) = project_root
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    default_dir = os.path.join(project_root, "output", "prompts")
    
    directory = sys.argv[1] if len(sys.argv) > 1 else default_dir
    
    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' does not exist.")
        sys.exit(1)
    
    output_dir = os.path.join(project_root, "auditing", "reports")
    os.makedirs(output_dir, exist_ok=True)
    output_image = os.path.join(output_dir, "prompt_distribution_sankey.png")
    output_mermaid = os.path.join(output_dir, "prompt_distribution_flow.md")
    output_census = os.path.join(output_dir, "style_census.md")
    
    print(f"Analyzing prompts in: {directory}")
    
    # Vibe/Category Mappings
    SCENE_CATEGORIES = {
        'Athletic/Combat': ['gym', 'stadium', 'field', 'combat', 'wrestling', 'boxing', 'athletic', 'track', 'ring', 'court', 'pool', 'arena', 'dojo', 'training'],
        'Academic/School': ['school', 'classroom', 'hallway', 'academy', 'library', 'study', 'lecture', 'campus'],
        'Domestic/Casual': ['kitchen', 'bedroom', 'living room', 'cozy', 'domestic', 'home', 'apartment', 'attic', 'balcony', 'patio'],
        'Formal/Social': ['reception', 'restaurant', 'ballroom', 'formal', 'social', 'gala', 'party', 'hall', 'venue', 'lounge', 'club'],
        'Clinical/Medical': ['surgical', 'medical', 'hospital', 'lab', 'office', 'clinic', 'examination'],
        'Nature/Serene': ['forest', 'waterfall', 'lake', 'park', 'mountain', 'meadow', 'river', 'island', 'beach', 'garden', 'pond', 'trail'],
        'Urban/Gritty': ['alleyway', 'street', 'subway', 'station', 'neon', 'urban', 'downtown', 'rooftop', 'fire escape', 'sidewalk'],
        'Performance/Entertainment': ['stage', 'concert', 'theater', 'backstage', 'spotlight', 'runway', 'auditorium'],
        'Industrial/Warehouse': ['warehouse', 'factory', 'industrial', 'garage', 'workshop', 'hangar']
    }

    INTERACTION_CATEGORIES = {
        'Social/Bonding': ['bff', 'sharing', 'prayer', 'greet', 'handshake', 'toast', 'chat', 'talk', 'standing', 'whisper', 'promise', 'conversation', 'laugh'],
        'Combat/Action': ['defense', 'formation', 'mma', 'dodge', 'staredown', 'relay', 'duel', 'fight', 'action', 'passing', 'training', 'sparring', 'strike'],
        'Daily/Wholesome': ['pointing', 'earbuds', 'walking', 'path', 'morning', 'routine', 'hanging', 'reading', 'studying', 'eating'],
        'Specialized/Work': ['prototype', 'surgical', 'medical', 'procedur', 'technical', 'hacking', 'office', 'coaching', 'dice', 'presentation', 'meeting'],
        'Romantic/Intimate': ['snowy', 'aquarium', 'bench', 'hug', 'kiss', 'romantic', 'couple', 'intimate', 'leaning', 'cuddl', 'embrace', 'holding hands'],
        'Performance/Pose': ['posing', 'modeling', 'runway', 'photoshoot', 'performance', 'dancing', 'singing']
    }

    OUTFIT_CATEGORIES = {
        'Athletic/Sports': ['gymnastics', 'football', 'beach volleyball', 'track', 'mma', 'boxing', 'athletic', 'tennis', 'swim', 'athleisure', 'compression', 'esports', 'volleyball', 'wrestling', 'soccer', 'basketball'],
        'Formal/Social': ['gown', 'tie', 'formal', 'cocktail', 'met gala', 'symphony', 'suit', 'tuxedo', 'parisian', 'italian', 'opera', 'dealer', 'blazer', 'dress shirt'],
        'Vintage/Retro': ['vintage', 'period', '1900', '1950', '1970', 'server', 'pinup', 'disco', 'newsboy', 'retro', 'western shirt', 'cowgirl', 'cowboy', 'ranch', 'denim'],
        'Fantasy/Historical': ['samurai', 'monk', 'knight', 'bard', 'mage', 'priest', 'warrior', 'druid', 'beastmaster', 'healer', 'sorceress', 'alchemist', ' shinobi', 'paladin', 'ranger', 'rogue'],
        'Futuristic/Alt': ['cyberpunk', 'neo', 'steampunk', 'netrunner', 'bioluminescent', 'goth', 'edgy', 'grunge', 'academia', 'tactical', 'punk', 'rocker', 'harness'],
        'Casual/Daily': ['streetwear', 'casual', 'tracksuit', 'skater', 'lumberjack', 'denim', 'knit', 'hoodie', 'thermal', 'bohemian', 'turtleneck', 'briefs', 'cardigan', 'comfortable', 'cozy'],
        'Stage/Performance': ['runway', 'showgirl', 'burlesque', 'cabaret', 'pop', 'idol', 'performer', 'entertainer'],
        'Lingerie/Glamour': ['lingerie', 'angel', 'lace', 'satin', 'silk', 'negligee', 'corset', 'boudoir']
    }

    def get_category(name, mapping, default="Other", layer_suffix=""):
        if not name or name == "None": 
            return f"None ({layer_suffix})" if layer_suffix else "None"
        n = name.lower()
        for cat, keywords in mapping.items():
            if any(kw in n for kw in keywords): return cat
        return f"{default} ({layer_suffix})" if layer_suffix else default

    # Data structures for aggregated flow: Style -> Scene -> Outfit -> Interaction
    style_to_scene_cat = defaultdict(int)
    scene_cat_to_outfit = defaultdict(int)
    outfit_to_interaction = defaultdict(int)
    style_frequency = defaultdict(int)
    
    # Parse data
    file_count = 0
    for filename in os.listdir(directory):
        if not filename.endswith('.txt'):
            continue
        
        file_count += 1
        file_path = os.path.join(directory, filename)
        metadata = parse_prompt_metadata(file_path)
        
        if metadata['scene'] and metadata['base_prompt']:
            # Simplify style name and fix double spaces (e.g., "Standard  Neutral" -> "Standard / Neutral")
            raw_style = metadata['base_prompt'].split(":")[0]
            style = raw_style.replace("  ", " / ").strip()
            
            scene = metadata['scene']
            scene_cat = get_category(scene, SCENE_CATEGORIES, "Other", "Scene")
            
            # Count for census
            style_frequency[style] += 1
            
            interaction = metadata['interaction'] or "None"
            interaction_vibe = get_category(interaction, INTERACTION_CATEGORIES, "Other", "Interaction")
            
            # 1. Style -> Scene Category
            style_to_scene_cat[(style, scene_cat)] += 1
            
            for i, char_name in enumerate(metadata['characters']):
                if i < len(metadata['outfits']):
                    outfit = metadata['outfits'][i]
                    outfit_cat = get_category(outfit, OUTFIT_CATEGORIES, "Other", "Outfit")
                    
                    if outfit and outfit != "None":
                         # 2. Scene Category -> Outfit Category
                         scene_cat_to_outfit[(scene_cat, outfit_cat)] += 1
                         
                         # 3. Outfit Category -> Interaction Vibe
                         # Outfit is SOURCE (no suffix), Interaction is TARGET
                         outfit_to_interaction[(outfit_cat, interaction_vibe)] += 1

    print(f"Processed {file_count} prompt files.")
    
    # DEBUG: Print all unique nodes to identify circular references
    all_sources = set()
    all_targets = set()
    
    for (src, dst), count in style_to_scene_cat.items():
        all_sources.add(src)
        all_targets.add(dst)
    
    for (src, dst), count in scene_cat_to_outfit.items():
        all_sources.add(src)
        all_targets.add(dst)
        
    for (src, dst), count in outfit_to_interaction.items():
        all_sources.add(src)
        all_targets.add(dst)
    
    print("\n=== DEBUG: Sankey Node Analysis ===")
    print(f"Total unique source nodes: {len(all_sources)}")
    print(f"Total unique target nodes: {len(all_targets)}")
    
    # Find nodes that appear as both source AND target (potential circular refs)
    both = all_sources.intersection(all_targets)
    print(f"\nNodes appearing as BOTH source and target ({len(both)}):")
    for node in sorted(both):
        print(f"  - {node}")
    
    # Check for exact duplicates
    print("\n=== Checking for duplicate node names ===")
    all_nodes = list(all_sources.union(all_targets))
    duplicates = [node for node in set(all_nodes) if all_nodes.count(node) > 1]
    if duplicates:
        print(f"WARNING: Found {len(duplicates)} duplicate nodes!")
        for dup in duplicates:
            print(f"  - {dup}")
    else:
        print("✓ No duplicate node names found")
    
    print("=" * 50 + "\n")

    # No longer tracking outfit->character flow, removed this section

    # Generate Image/HTML
    create_sankey_diagram(style_to_scene_cat, scene_cat_to_outfit, outfit_to_interaction, output_image)
    
    # Generate Mermaid
    create_mermaid_diagram(style_to_scene_cat, scene_cat_to_outfit, outfit_to_interaction, output_mermaid)

    # Generate Census
    create_style_census(style_frequency, output_census)
