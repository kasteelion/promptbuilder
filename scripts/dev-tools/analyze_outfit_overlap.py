
import re
import os

def parse_outfit_names(filepath):
    names = set()
    categories = {}
    current_category = "Uncategorized"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith("## "):
                current_category = line[3:].strip()
            elif line.startswith("### "):
                # Extract name, ignoring tags for matching purposes
                raw_name = line[4:].strip()
                name_match = re.match(r"([^(]+)(\s*\(.*\))?", raw_name)
                if name_match:
                    name = name_match.group(1).strip()
                    names.add(name)
                    if name not in categories:
                        categories[name] = current_category
    return names, categories

base_path = r"C:\Users\parking\Desktop\promptbuilder\data"
f_names, f_cats = parse_outfit_names(os.path.join(base_path, "outfits_f.md"))
m_names, m_cats = parse_outfit_names(os.path.join(base_path, "outfits_m.md"))
h_names, h_cats = parse_outfit_names(os.path.join(base_path, "outfits_h.md"))

common_fm = f_names.intersection(m_names)
common_fh = f_names.intersection(h_names)
common_mh = m_names.intersection(h_names)
all_three = f_names.intersection(m_names).intersection(h_names)
all_names = f_names.union(m_names).union(h_names)

print(f"Total Unique Names: {len(all_names)}")
print(f"F Outfits: {len(f_names)}")
print(f"M Outfits: {len(m_names)}")
print(f"H Outfits: {len(h_names)}")
print(f"Common F&M: {len(common_fm)}")
print(f"Common F&H: {len(common_fh)}")
print(f"Common All Three: {len(all_three)}")

# List some mismatches to see if they are just typos or completely different
print("\nSample Mismatches (in F but not M):")
print(list(f_names - m_names)[:10])

print("\nSample Mismatches (in M but not F):")
print(list(m_names - f_names)[:10])
