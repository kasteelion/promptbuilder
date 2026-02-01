import os
import sys

# Ensure we can import from the root directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from logic.randomizer import PromptRandomizer

def generate_tag_map():
    # Access the aliases directly from the class
    aliases = PromptRandomizer.TAG_ALIASES
    
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports", "tag_network_map.md")
    
    # Define Clusters based on keywords found in TARGETS (Right-hand side)
    clusters = {
        "Fantasy & Magic": ["fantasy", "magic", "mythology", "nature", "forest"],
        "Sci-Fi & Tech": ["sci-fi", "tech", "futuristic", "cyberpunk", "modern", "urban"],
        "Historical & Vintage": ["historical", "vintage", "retro", "classic", "victorian", "noir"],
        "Action & Combat": ["combat", "action", "dynamic", "intense", "sport", "athletic", "active"],
        "Fashion & Lifestyle": ["fashion", "luxury", "elegant", "casual", "chic", "boho", "streetwear"],
        "Art & Mood": ["art", "creative", "artistic", "soft", "calm", "dramatic"],
    }
    
    # Bucketize connections
    clustered_conns = {k: [] for k in clusters}
    other_conns = []
    
    for source, targets in aliases.items():
        clean_source = "t_" + source.replace(" ", "_").replace("-", "_").replace(":", "_")
        
        # Determine primary cluster for this source based on its TARGETS
        primary_cluster = None
        for target in targets:
            t_lower = target.lower()
            for cluster_name, keywords in clusters.items():
                if t_lower in keywords:
                    primary_cluster = cluster_name
                    break
            if primary_cluster:
                break
        
        # Format strings
        conn_lines = []
        for target in targets:
            clean_target = "t_" + target.replace(" ", "_").replace("-", "_").replace(":", "_")
            conn_lines.append(f"    {clean_source}({source}) --> {clean_target}({target})")
            
        if primary_cluster:
            clustered_conns[primary_cluster].extend(conn_lines)
        else:
            other_conns.extend(conn_lines)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Tag Network Map\n\n")
        f.write("Visualizing how specific tags map to broader categories.\n\n")
        f.write("```mermaid\n")
        f.write("graph LR\n")
        
        # Styles
        f.write("    classDef source fill:#e1f5fe,stroke:#01579b,stroke-width:1px;\n")
        f.write("    classDef target fill:#fff9c4,stroke:#fbc02d,stroke-width:2px;\n")
        
        # Write Clusters
        for cluster_name, lines in clustered_conns.items():
            if not lines: continue
            f.write(f"\n    subgraph {cluster_name.replace(' ', '_')}\n")
            # f.write(f"    direction TB\n") # Optional: force internal direction
            for line in sorted(lines):
                f.write(line + "\n")
            f.write("    end\n")
            
        # Write Others
        if other_conns:
            f.write("\n    subgraph Uncategorized\n")
            for line in sorted(other_conns):
                f.write(line + "\n")
            f.write("    end\n")

        f.write("```\n")
        
    print(f"Tag map generated at: {output_path}")

if __name__ == "__main__":
    generate_tag_map()
