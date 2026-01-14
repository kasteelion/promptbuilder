import os
import sys
from collections import defaultdict

# Ensure we can import from the root directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from logic.data_loader import DataLoader

def audit_tags():
    loader = DataLoader()
    
    # Load everything
    chars = loader.load_characters()
    scenes = loader.load_presets("scenes.md")
    poses = loader.load_presets("poses.md")
    interactions = loader.load_interactions()
    outfits_dir = os.path.join("data", "outfits")
    
    # We need to manually traverse outfits since DataLoader doesn't give us a flat list easily
    from logic.outfit_parser import OutfitParser
    parser = OutfitParser()
    outfits_data = parser.parse_outfits_directory(outfits_dir)
    
    # Core Themes to track
    THEMES = [
        "Fantasy", "Cyberpunk", "Sci-Fi", "Sports", "Formal", "Casual", 
        "Urban", "Nature", "Historical", "Alternative", "Gym", "Domestic",
        "Military", "Royal", "Dark", "Cute", "Sexy"
    ]
    
    distribution = {
        "Scenes": defaultdict(int),
        "Outfits": defaultdict(int),
        "Poses": defaultdict(int),
        "Interactions": defaultdict(int)
    }
    
    # Helpers to get tags
    def get_tag_list(data):
        if isinstance(data, dict):
            return data.get("tags", [])
        return []

    # Audit Scenes
    for cat, items in scenes.items():
        for name, data in items.items():
            tags = [t.lower() for t in get_tag_list(data)]
            for theme in THEMES:
                if theme.lower() in tags or theme.lower() in cat.lower() or theme.lower() in name.lower():
                    distribution["Scenes"][theme] += 1

    # Audit Outfits (Unified)
    for modifier, categories in outfits_data.items():
        for cat, outfits in categories.items():
            for name, data in outfits.items():
                tags = [t.lower() for t in get_tag_list(data)]
                for theme in THEMES:
                    if theme.lower() in tags or theme.lower() in cat.lower() or theme.lower() in name.lower():
                        distribution["Outfits"][theme] += 1

    # Audit Poses
    for cat, items in poses.items():
        for name, data in items.items():
            tags = [t.lower() for t in get_tag_list(data)]
            for theme in THEMES:
                if theme.lower() in tags or theme.lower() in cat.lower() or theme.lower() in name.lower():
                    distribution["Poses"][theme] += 1

    # Audit Interactions
    for cat, items in interactions.items():
        for name, data in items.items():
            tags = [t.lower() for t in get_tag_list(data)]
            for theme in THEMES:
                if theme.lower() in tags or theme.lower() in cat.lower():
                    distribution["Interactions"][theme] += 1

    # Print Report
    print("# Tag Distribution Audit Report\n")
    print("| Theme | Scenes | Outfits | Poses | Interactions |")
    print("| :--- | :---: | :---: | :---: | :---: |")
    for theme in THEMES:
        row = [
            theme,
            distribution["Scenes"][theme],
            distribution["Outfits"][theme],
            distribution["Poses"][theme],
            distribution["Interactions"][theme]
        ]
        print(f"| {' | '.join(map(str, row))} |")

    # Generate Mermaid Flowchart (More compatible than Sankey)
    print("\n## Mermaid Tag Flow (Scenes -> Themes -> Outfits)\n")
    print("```mermaid")
    print("graph LR")
    
    # Styles
    print("  classDef scene fill:#f9f,stroke:#333,stroke-width:2px;")
    print("  classDef theme fill:#bbf,stroke:#333,stroke-width:2px;")
    print("  classDef outfit fill:#bfb,stroke:#333,stroke-width:2px;")

    for theme in THEMES:
        t_id = theme.replace(" ", "_")
        
        # Scenes to Theme
        s_count = distribution["Scenes"][theme]
        if s_count > 0:
            print(f"  S_{t_id}[Scene: {theme}] -- {s_count} --> T_{t_id}({theme})")
            print(f"  class S_{t_id} scene")
        
        # Theme to Outfits
        o_count = distribution["Outfits"][theme]
        if o_count > 0:
            if s_count == 0: # Ensure theme node exists if no scenes
                print(f"  T_{t_id}({theme})")
            print(f"  T_{t_id} -- {o_count} --> O_{t_id}[Outfit: {theme}]")
            print(f"  class T_{t_id} theme")
            print(f"  class O_{t_id} outfit")
            
    print("```")

if __name__ == "__main__":
    audit_tags()
