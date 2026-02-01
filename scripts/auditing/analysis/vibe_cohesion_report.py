import os
import sys
from collections import defaultdict

def parse_metadata(file_path):
    metadata = {'scene': None, 'interaction': None, 'outfits': []}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            in_metadata = False
            for line in f:
                line = line.strip()
                if line == "# METADATA":
                    in_metadata = True
                    continue
                if not in_metadata or not line: continue
                if line.startswith("Scene:"): metadata['scene'] = line.split(":", 1)[1].strip()
                elif line.startswith("Interaction:"): metadata['interaction'] = line.split(":", 1)[1].strip()
                elif line.startswith("Character:"):
                    parts = line.split("|")
                    if len(parts) > 1:
                        outfit = parts[1].split(":", 1)[1].strip()
                        if outfit != "None": metadata['outfits'].append(outfit)
    except: pass
    return metadata

# Define Vibe Mappings (Keyword-based)
VIBE_KEYWORDS = {
    'Athletic': ['gym', 'stadium', 'field', 'combat', 'wrestling', 'boxing', 'athletic', 'track', 'fitness', 'sport'],
    'Academic': ['school', 'classroom', 'hallway', 'academy', 'library', 'university', 'study'],
    'Domestic/Casual': ['kitchen', 'bedroom', 'living room', 'cozy', 'domestic', 'home', 'apartment', 'morning'],
    'Formal/Social': ['reception', 'restaurant', 'ballroom', 'formal', 'social', 'gala', 'party', 'hall'],
    'Clinical/Cold': ['surgical', 'medical', 'hospital', 'lab', 'sterile', 'clean room'],
    'Gritty/Noir': ['alleyway', 'street at night', 'gritty', 'underground', 'subway', 'dark metal'],
    'Nature/Serene': ['meadow', 'forest', 'waterfall', 'lake', 'park', 'sunset', 'garden']
}

OUTFIT_VIBE_KEYWORDS = {
    'Athletic': ['boxing', 'wrestling', 'gym', 'athletic', 'soccer', 'baseball', 'cheerleading', 'mma', 'track'],
    'Cozy/Casual': ['cardigan', 'sweater', 'relaxed', 'pajama', 'comfort', 'hoodie'],
    'Formal': ['gown', 'suit', 'tuxedo', 'dress', 'blazer', 'power suit'],
    'Historical': ['victorian', 'ninja', 'knight', 'samurai', 'renaissance', 'monk'],
    'Clinical': ['scrubs', 'lab coat', 'surgical']
}

INTERACTION_VIBE_KEYWORDS = {
    'Romantic': ['catch', 'ai-ai gasa', 'umbrella', 'kiss', 'embrace', 'blush', 'eyes meeting', 'physical closeness'],
    'Wholesome/School': ['earbuds', 'whisper', 'museum', 'aquarium', 'sharing', 'notebook', 'hallway']
}

def get_vibe(text, mapping):
    if not text: return 'Unknown'
    text = text.lower()
    for vibe, keywords in mapping.items():
        if any(kw in text for kw in keywords):
            return vibe
    return 'Unknown'

def analyze_vibe_cohesion(directory):
    stats = defaultdict(lambda: defaultdict(int))
    mismatches = []
    
    for filename in os.listdir(directory):
        if not filename.endswith('.txt'): continue
        meta = parse_metadata(os.path.join(directory, filename))
        
        scene_vibe = get_vibe(meta['scene'], VIBE_KEYWORDS)
        int_vibe = get_vibe(meta['interaction'], INTERACTION_VIBE_KEYWORDS)
        
        # Track "Vibe Mixes"
        if scene_vibe != 'Unknown' and int_vibe != 'Unknown':
            vibe_pair = f"{scene_vibe} + {int_vibe}"
            stats['mixes'][vibe_pair] += 1
            
        # Check for obvious mismatches
        for outfit in meta['outfits']:
            outfit_vibe = get_vibe(outfit, OUTFIT_VIBE_KEYWORDS)
            if scene_vibe != 'Unknown' and outfit_vibe != 'Unknown':
                # Flag dissonant pairings
                if scene_vibe == 'Clinical/Cold' and outfit_vibe == 'Athletic':
                    mismatches.append(f"Dissonance: Athletic {outfit} in Clinical {meta['scene']} ({filename})")
                elif scene_vibe == 'Nature/Serene' and outfit_vibe == 'Formal':
                    # This is actually a cool contrast (Eco-Social), maybe not a mismatch but a "Contrast Vibe"
                    stats['contrasts'][f"{scene_vibe} + {outfit_vibe}"] += 1
                elif scene_vibe == 'Gritty/Noir' and outfit_vibe == 'Cozy/Casual':
                    mismatches.append(f"Mismatch: Cozy {outfit} in Gritty {meta['scene']} ({filename})")

    # Generate Report
    print("# Vibe Cohesion & Diversity Report")
    print(f"\n## Top Vibe Mixes (Multi-faceted Prompts)")
    sorted_mixes = sorted(stats['mixes'].items(), key=lambda x: x[1], reverse=True)
    for mix, count in sorted_mixes:
        print(f"- **{mix}**: {count} prompts")
        
    print(f"\n## Potential Thematic Mismatches")
    if not mismatches:
        print("- No major thematic mismatches detected! (High Vibe Cohesion)")
    else:
        for m in mismatches[:10]:
            print(f"- ⚠️ {m}")

if __name__ == "__main__":
    import io
    from contextlib import redirect_stdout
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up two levels to reach auditing root (from auditing/analysis), then into reports
    audit_root = os.path.dirname(os.path.dirname(script_dir)) 
    output_dir = os.path.join(audit_root, "auditing", "reports") # Wait, if script_dir is analysis, dirname is auditing, dirname is root. 
    # Let's use relative path explicitly or explicit project structure
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_dir = os.path.join(project_root, "auditing", "reports")
    
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "vibe_cohesion_report.md")
    
    directory = sys.argv[1] if len(sys.argv) > 1 else "output/prompts"
    
    output_buffer = io.StringIO()
    with redirect_stdout(output_buffer):
        analyze_vibe_cohesion(directory)
    
    report_content = output_buffer.getvalue()
    print(report_content)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
