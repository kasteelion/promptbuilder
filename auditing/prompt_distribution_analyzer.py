import os
import sys
from collections import defaultdict

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

def analyze_prompt_distribution(directory):
    """Analyze all prompt files in a directory and generate distribution stats."""
    
    # Counters
    scene_counts = defaultdict(int)
    base_prompt_counts = defaultdict(int)
    outfit_counts = defaultdict(int)
    pose_counts = defaultdict(int)
    interaction_counts = defaultdict(int)
    
    total_prompts = 0
    
    # Parse all .txt files
    for filename in os.listdir(directory):
        if not filename.endswith('.txt'):
            continue
        
        file_path = os.path.join(directory, filename)
        metadata = parse_prompt_metadata(file_path)
        
        if metadata['scene']:
            total_prompts += 1
            scene_counts[metadata['scene']] += 1
            
            if metadata['base_prompt']:
                base_prompt_counts[metadata['base_prompt']] += 1
            
            for outfit in metadata['outfits']:
                if outfit and outfit != "None":
                    outfit_counts[outfit] += 1
            
            for pose in metadata['poses']:
                if pose and pose != "None":
                    pose_counts[pose] += 1
            
            if metadata['interaction']:
                interaction_counts[metadata['interaction']] += 1
    
    print(f"\n# Prompt Distribution Analysis")
    print(f"\nTotal Prompts Analyzed: {total_prompts}\n")
    
    def print_dist(title, data, total, limit=10):
        print(f"\n## {title}")
        sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)
        
        for item, count in sorted_items[:limit]:
            percentage = (count / total) * 100
            flag = ""
            if percentage > 20 and len(data) > 3: # Simple overweight heuristic
                 flag = " ⚠️ OVERWEIGHTED"
            print(f"  {item}: {count} ({percentage:.1f}%){flag}")

    print_dist("Top 10 Scenes", scene_counts, total_prompts)
    print_dist("Top 10 Base Prompts (Art Styles)", base_prompt_counts, total_prompts)
    
    # Outfits might not be present in every prompt, but we use total_prompts as denominator for impact
    print_dist("Top 10 Outfits", outfit_counts, total_prompts)
    print_dist("Top 10 Poses", pose_counts, total_prompts)
    print_dist("Interactions", interaction_counts, total_prompts)
    
    # Generate Mermaid Sankey (simplified - top items only)
    print("\n## Mermaid Distribution Flow\n")
    print("```mermaid")
    print("graph LR")
    print("  classDef scene fill:#f9f,stroke:#333,stroke-width:2px;")
    print("  classDef style fill:#bbf,stroke:#333,stroke-width:2px;")
    print("  classDef outfit fill:#bfb,stroke:#333,stroke-width:2px;")
    
    # Top 5 scenes -> Top 5 styles
    top_scenes = sorted(scene_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    top_styles = sorted(base_prompt_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    for scene, count in top_scenes:
        scene_id = scene.replace(" ", "_").replace("-", "_")
        print(f"  S_{scene_id}[{scene}]")
        print(f"  class S_{scene_id} scene")
    
    for style, count in top_styles:
        style_id = style.replace(" ", "_").replace("-", "_")
        # Connect scenes to styles (simplified - just show flow)
        for scene, _ in top_scenes[:2]:  # Connect top 2 scenes to each style
            scene_id = scene.replace(" ", "_").replace("-", "_")
            print(f"  S_{scene_id} --> ST_{style_id}[{style}]")
        print(f"  class ST_{style_id} style")
    
    print("```")

if __name__ == "__main__":
    # Default to generated_prompts_only directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)  # Go up one level from utils/
    # Updated default paths
    default_dir = os.path.join(parent_dir, "output", "prompts")
    
    directory = sys.argv[1] if len(sys.argv) > 1 else default_dir
    
    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' does not exist.")
        sys.exit(1)
    
    # Create output file path
    output_dir = os.path.join(script_dir, "reports")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "prompt_distribution_report.md")
    
    # Redirect stdout to both console and file
    import io
    from contextlib import redirect_stdout
    
    # Capture output
    output_buffer = io.StringIO()
    
    with redirect_stdout(output_buffer):
        analyze_prompt_distribution(directory)
    
    # Get the captured output
    report_content = output_buffer.getvalue()
    
    # Print to console
    print(report_content)
    
    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"\n📊 Report saved to: {output_file}")
