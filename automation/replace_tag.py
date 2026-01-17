import os
import argparse
import glob

# Configuration
DATA_DIR = r"c:\Users\parking\Desktop\promptbuilder\data"

def replace_in_outfits(old_tag, new_tag, dry_run=True):
    print(f"\n--- Scanning Outfits for '{old_tag}' -> '{new_tag}' ---")
    outfit_files = glob.glob(os.path.join(DATA_DIR, "outfits", "**", "*.txt"), recursive=True)
    
    for fp in outfit_files:
        with open(fp, 'r', encoding='utf-8') as f:
            content = f.read()
            
        lines = content.splitlines()
        modified = False
        new_lines = []
        
        for line in lines:
            if line.strip().startswith("tags:"):
                # Parse tags
                prefix, tag_part = line.split(":", 1)
                # Remove brackets [ ] if present
                clean_part = tag_part.strip().strip("[]")
                current_tags = [t.strip() for t in clean_part.split(",")]
                
                new_tags_list = []
                for t in current_tags:
                    if t.lower() == old_tag.lower():
                        if new_tag: # If new_tag is None/Empty, we are deleting
                            # Avoid duplicate if new_tag already exists
                            if not any(nt.lower() == new_tag.lower() for nt in current_tags):
                                new_tags_list.append(new_tag)
                            elif new_tag in current_tags:
                                # existing
                                pass
                        modified = True
                    else:
                        new_tags_list.append(t)
                
                # Reconstruct line
                params = ", ".join(new_tags_list)
                new_line = f"tags: [{params}]"
                new_lines.append(new_line)
            else:
                new_lines.append(line)
        
        if modified:
            print(f"[MATCH] {os.path.basename(fp)}")
            if not dry_run:
                with open(fp, 'w', encoding='utf-8') as f:
                    f.write("\n".join(new_lines))
                print(f"  > Updated.")

def replace_in_scenes(old_tag, new_tag, dry_run=True):
    print(f"\n--- Scanning Scenes for '{old_tag}' -> '{new_tag}' ---")
    fp = os.path.join(DATA_DIR, "scenes.md")
    if not os.path.exists(fp):
        return

    with open(fp, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    modified = False
    new_lines = []
    
    for line in lines:
        # Format: ### Name (Tag, Tag)
        if line.strip().startswith("### ") and "(" in line and ")" in line:
            pre, rest = line.split("(", 1)
            inner, post = rest.rsplit(")", 1)
            
            current_tags = [t.strip() for t in inner.split(",")]
            new_tags_list = []
            line_mod = False
            
            for t in current_tags:
                if t.lower() == old_tag.lower():
                    if new_tag and not any(nt.lower() == new_tag.lower() for nt in current_tags):
                        new_tags_list.append(new_tag)
                    line_mod = True
                else:
                    new_tags_list.append(t)
            
            if line_mod:
                modified = True
                new_inner = ", ".join(new_tags_list)
                new_lines.append(f"{pre}({new_inner}){post}")
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
            
    if modified:
        print(f"[MATCH] scenes.md")
        if not dry_run:
            with open(fp, 'w', encoding='utf-8') as f:
                f.write("".join(new_lines))
            print("  > Updated scenes.md")

def replace_in_interactions(old_tag, new_tag, dry_run=True):
    print(f"\n--- Scanning Interactions for '{old_tag}' -> '{new_tag}' ---")
    fp = os.path.join(DATA_DIR, "interactions.md")
    if not os.path.exists(fp):
        return

    with open(fp, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    modified = False
    new_lines = []
    
    for line in lines:
        # Format: - **Name** (Tag, Tag, ...): Desc
        if line.strip().startswith("- **") and "(" in line and "):" in line:
            pre, rest = line.split("(", 1)
            inner, post = rest.split("):", 1)
            
            current_tags = [t.strip() for t in inner.split(",")]
            new_tags_list = []
            line_mod = False
            
            for t in current_tags:
                if t.lower() == old_tag.lower():
                    if new_tag and not any(nt.lower() == new_tag.lower() for nt in current_tags):
                        new_tags_list.append(new_tag)
                    line_mod = True
                else:
                    new_tags_list.append(t)
            
            if line_mod:
                modified = True
                new_inner = ", ".join(new_tags_list)
                new_lines.append(f"{pre}({new_inner}):{post}")
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    if modified:
        print(f"[MATCH] interactions.md")
        if not dry_run:
            with open(fp, 'w', encoding='utf-8') as f:
                f.write("".join(new_lines))
            print("  > Updated interactions.md")

def replace_in_poses(old_tag, new_tag, dry_run=True):
    print(f"\n--- Scanning Poses for '{old_tag}' -> '{new_tag}' ---")
    fp = os.path.join(DATA_DIR, "poses.md")
    if not os.path.exists(fp):
        return

    with open(fp, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    modified = False
    new_lines = []
    
    for line in lines:
        # Format: - **Name** (Tag, Tag, ...): Desc
        if line.strip().startswith("- **") and "(" in line and "):" in line:
            pre, rest = line.split("(", 1)
            inner, post = rest.split("):", 1)
            
            current_tags = [t.strip() for t in inner.split(",")]
            new_tags_list = []
            line_mod = False
            
            for t in current_tags:
                if t.lower() == old_tag.lower():
                    if new_tag and not any(nt.lower() == new_tag.lower() for nt in current_tags):
                        new_tags_list.append(new_tag)
                    line_mod = True
                else:
                    new_tags_list.append(t)
            
            if line_mod:
                modified = True
                new_inner = ", ".join(new_tags_list)
                new_lines.append(f"{pre}({new_inner}):{post}")
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    if modified:
        print(f"[MATCH] poses.md")
        if not dry_run:
            with open(fp, 'w', encoding='utf-8') as f:
                f.write("".join(new_lines))
            print("  > Updated poses.md")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Replace tags in assets")
    parser.add_argument("old_tag", help="Tag to find")
    parser.add_argument("new_tag", help="Tag to replace with (use 'DELETE' to remove)")
    parser.add_argument("--run", action="store_true", help="Execute changes")
    
    args = parser.parse_args()
    
    target = args.new_tag
    if target == "DELETE":
        target = None
        
    dry = not args.run
    
    if dry:
        print("--- DRY RUN MODE (Use --run to execute) ---")
        
    replace_in_outfits(args.old_tag, target, dry)
    replace_in_scenes(args.old_tag, target, dry)
    replace_in_interactions(args.old_tag, target, dry)
    replace_in_poses(args.old_tag, target, dry)
