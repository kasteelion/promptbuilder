import os
import sys
from collections import defaultdict
import plotly.graph_objects as go

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

def create_sankey_diagram(directory, output_path):
    """Create a Sankey diagram showing the flow from scenes to styles to outfits."""
    
    # Counters for connections
    scene_to_style = defaultdict(int)
    style_to_outfit = defaultdict(int)
    
    # Parse all .txt files
    for filename in os.listdir(directory):
        if not filename.endswith('.txt'):
            continue
        
        file_path = os.path.join(directory, filename)
        metadata = parse_prompt_metadata(file_path)
        
        if metadata['scene'] and metadata['base_prompt']:
            # Track scene -> style connections
            scene_to_style[(metadata['scene'], metadata['base_prompt'])] += 1
            
            # Track style -> outfit connections
            for outfit in metadata['outfits']:
                if outfit and outfit != "None":
                    style_to_outfit[(metadata['base_prompt'], outfit)] += 1
    
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
    
    # Add scene -> style connections
    for (scene, style), count in sorted(scene_to_style.items(), key=lambda x: x[1], reverse=True)[:20]:
        source_idx = get_or_create_label(f"Scene: {scene[:30]}...")
        target_idx = get_or_create_label(f"Style: {style[:30]}...")
        sources.append(source_idx)
        targets.append(target_idx)
        values.append(count)
    
    # Add style -> outfit connections
    for (style, outfit), count in sorted(style_to_outfit.items(), key=lambda x: x[1], reverse=True)[:20]:
        source_idx = get_or_create_label(f"Style: {style[:30]}...")
        target_idx = get_or_create_label(f"Outfit: {outfit[:30]}...")
        sources.append(source_idx)
        targets.append(target_idx)
        values.append(count)
    
    # Create Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color=["#f9f" if "Scene:" in l else "#bbf" if "Style:" in l else "#bfb" for l in labels]
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values
        )
    )])
    
    fig.update_layout(
        title_text="Prompt Generation Distribution (Scene → Style → Outfit)",
        font_size=10,
        height=800,
        width=1400
    )
    
    # Save as image
    fig.write_image(output_path)
    print(f"📊 Sankey diagram saved to: {output_path}")
    
    # Also save as HTML for interactive viewing
    # Also save as HTML for interactive viewing
    html_path = output_path.replace('.png', '.html')
    fig.write_html(html_path)
    print(f"🌐 Interactive HTML saved to: {html_path}")

def create_mermaid_diagram(char_to_scene, scene_to_style, style_to_outfit, output_path):
    """Generate a Mermaid markdown file for IDE viewing."""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Prompt Distribution Flow\n\n")
        f.write("```mermaid\n")
        f.write("graph LR\n")
        
        # Styling (Softer Palette)
        f.write("  classDef char fill:#e1bee7,stroke:#4a148c,stroke-width:2px,color:#000;\n")
        f.write("  classDef scene fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000;\n")
        f.write("  classDef artstyle fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,color:#000;\n")
        f.write("  classDef outfit fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#000;\n\n")
        
        # Nodes and Edges
        # Limit to top connections to keep diagram readable in IDE
        
        # Character -> Scene
        f.write("  %% Character -> Scene Flows\n")
        for (char, scene), count in sorted(char_to_scene.items(), key=lambda x: x[1], reverse=True)[:60]:
             safe_char = "".join(x for x in char if x.isalnum())[:20]
             safe_scene = "".join(x for x in scene if x.isalnum())[:20]
             
             clean_char = char.replace('"', "'")
             # Truncate/Clean Scene
             clean_scene = scene.replace('"', "'").replace("(", "").replace(")", "")
             if "," in clean_scene:
                  short_scene = clean_scene.split(",")[0]
             else:
                  short_scene = clean_scene
             if len(short_scene) > 40:
                  short_scene = short_scene[:37] + "..."
             
             f.write(f"  {safe_char}([\"{clean_char}\"]) -->|{count}| {safe_scene}([\"{short_scene}\"])\n")
             f.write(f"  class {safe_char} char\n")
             f.write(f"  class {safe_scene} scene\n")
        
        # Scene -> Style
        f.write("  %% Scene -> Style Flows\n")
        for (scene, style), count in sorted(scene_to_style.items(), key=lambda x: x[1], reverse=True)[:60]:
            safe_scene = "".join(x for x in scene if x.isalnum())[:20]
            safe_style = "".join(x for x in style if x.isalnum())[:20]
            
            # Sanitize labels for Mermaid (replace quotes, etc.)
            clean_scene = scene.replace('"', "'").replace("(", "").replace(")", "")
            # Truncate Scene for readability (First 40 chars or first comma)
            if "," in clean_scene:
                 short_scene = clean_scene.split(",")[0]
            else:
                 short_scene = clean_scene
            if len(short_scene) > 40:
                 short_scene = short_scene[:37] + "..."
            
            clean_style = style.replace('"', "'").replace("(", "").replace(")", "")
            
            f.write(f"  {safe_scene}([\"{short_scene}\"]) -->|{count}| {safe_style}[\"{clean_style}\"]\n")
            f.write(f"  class {safe_scene} scene\n")
            f.write(f"  class {safe_style} artstyle\n")
            
        # Style -> Outfit
        f.write("\n  %% Style -> Outfit Flows\n")
        for (style, outfit), count in sorted(style_to_outfit.items(), key=lambda x: x[1], reverse=True)[:60]:
            safe_style = "".join(x for x in style if x.isalnum())[:20]
            safe_outfit = "".join(x for x in outfit if x.isalnum())[:20]
            
            clean_style = style.replace('"', "'").replace("(", "").replace(")", "")
            clean_outfit = outfit.replace('"', "'").replace("(", "").replace(")", "")
            
            f.write(f"  {safe_style} -->|{count}| {safe_outfit}(\"{clean_outfit}\")\n")
            f.write(f"  class {safe_outfit} outfit\n")
            
        f.write("```\n")
        
    print(f"📊 Mermaid diagram saved to: {output_path}")

if __name__ == "__main__":
    # Default to generated_prompts_only directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    # Updated default paths
    default_dir = os.path.join(parent_dir, "output", "prompts")
    
    directory = sys.argv[1] if len(sys.argv) > 1 else default_dir
    
    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' does not exist.")
        sys.exit(1)
    
    output_dir = os.path.join(parent_dir, "output", "reports")
    os.makedirs(output_dir, exist_ok=True)
    output_image = os.path.join(output_dir, "prompt_distribution_sankey.png")
    output_mermaid = os.path.join(output_dir, "prompt_distribution_flow.md")
    
    print(f"Analyzing prompts in: {directory}")
    
    # We need to access the data structures from create_sankey_diagram
    # Ideally refactor, but for now we'll duplicate the loop logic slightly or modify create_sankey_diagram to return data
    # Let's modify create_sankey_diagram to be reusable or split the logic.
    # Refactoring slightly inline:
    
    char_to_scene = defaultdict(int)
    scene_to_style = defaultdict(int)
    style_to_outfit = defaultdict(int)
    
    # Parse data first
    for filename in os.listdir(directory):
        if not filename.endswith('.txt'):
            continue
        
        file_path = os.path.join(directory, filename)
        metadata = parse_prompt_metadata(file_path)
        
        if metadata['scene'] and metadata['base_prompt']:
            # Track character -> scene connections
            for char_name in metadata['characters']:
                 char_to_scene[(char_name, metadata['scene'])] += 1

            # Track scene -> style connections
            scene_to_style[(metadata['scene'], metadata['base_prompt'])] += 1
            
            # Track style -> outfit connections
            for outfit in metadata['outfits']:
                if outfit and outfit != "None":
                    style_to_outfit[(metadata['base_prompt'], outfit)] += 1

    # Generate Image/HTML
    create_sankey_diagram(directory, output_image)
    
    # Generate Mermaid (Updated signature to accept char_to_scene)
    create_mermaid_diagram(char_to_scene, scene_to_style, style_to_outfit, output_mermaid)
