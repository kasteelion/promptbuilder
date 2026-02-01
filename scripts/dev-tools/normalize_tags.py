
import os
import glob

def normalize_tags():
    # Define path to character files
    # Assuming script is run from project root or dev-tools
    # Try to find the data directory relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    char_dir = os.path.join(project_root, "data", "characters")
    
    if not os.path.exists(char_dir):
        print(f"Error: Could not find character directory at {char_dir}")
        return

    print(f"Scanning {char_dir}...")
    files = glob.glob(os.path.join(char_dir, "*.md"))
    
    updated_count = 0
    
    for file_path in files:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        new_lines = []
        modified = False
        
        for line in lines:
            # Clean strict start check to handle **Tags:** or Tags:
            clean_line = line.strip().lower()
            if clean_line.startswith("tags:") or clean_line.startswith("**tags:**") or clean_line.startswith("**tags**:"):
                # Found the tags line
                # Remove the prefix part (everything before the first colon + the colon itself)
                _, tags_part = line.split(":", 1)
                
                # Split, clean, lowercase, deduplicate
                # Also remove markdown bold/italic markers (*, _) from the tags themselves
                tags = []
                for t in tags_part.split(","):
                    clean_t = t.strip().lower()
                    clean_t = clean_t.replace("*", "").replace("_", "")
                    if clean_t:
                        tags.append(clean_t)
                
                unique_tags = sorted(list(set(tags)))
                
                # Preserve the original prefix format (e.g. "**Tags:** ") by using what we split, 
                # but simplified let's just use the standard "**Tags:**" for consistency if we are touching it.
                new_tags_line = f"**Tags:** {', '.join(unique_tags)}\n"
                
                if new_tags_line != line:
                    new_lines.append(new_tags_line)
                    modified = True
                    # Calculate what changed for log
                    old_set = set([t.strip() for t in tags_part.split(",") if t.strip()])
                    print(f" [FIX] {os.path.basename(file_path)}: Normalized {len(unique_tags)} tags.")
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            updated_count += 1
            
    print(f"\nCompleted. Updated {updated_count} character files.")

if __name__ == "__main__":
    normalize_tags()
