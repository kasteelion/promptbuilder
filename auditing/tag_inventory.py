import os
import re
import sys
import json
from collections import defaultdict

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logic.randomizer import PromptRandomizer

class TagInventory:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.tags_by_source = {
            "Characters": defaultdict(int),
            "Scenes": defaultdict(int),
            "Base Prompts": defaultdict(int),
            "Outfits": defaultdict(int),
            "Poses": defaultdict(int),
            "Interactions": defaultdict(int)
        }
        self.tag_locations = defaultdict(list) # tag -> list of source files/sections
        self.aliases = getattr(PromptRandomizer, 'TAG_ALIASES', {})

    def extract_tags_from_text(self, text, source_name):
        """Extract tags from text lines like 'Tags: (Tag1, Tag2)' or '## Name (Tag1, Tag2)'"""
        tags = []
        # Find all occurrences of (tags)
        matches = re.findall(r'\((.*?)\)', text)
        for content in matches:
            # Skip simple numeric counts like (2), (3+), (4)
            if re.match(r'^\d+\+?$', content.strip()):
                continue
                
            raw_tags = [t.strip() for t in content.split(',')]
            for t in raw_tags:
                if t:
                    tags.append(t)
                    self.tag_locations[t].append(source_name)
        return tags

    def crawl_characters(self):
        char_dir = os.path.join(self.data_dir, "characters")
        if not os.path.exists(char_dir):
            return

        for filename in os.listdir(char_dir):
            if filename.endswith(".md"):
                try:
                    with open(os.path.join(char_dir, filename), 'r', encoding='utf-8') as f:
                        content = f.read()
                        match = re.search(r'\*\*Tags:\*\*(.*?)(?:\n|$)', content) 
                        if not match:
                            match = re.search(r'Tags:(.*?)(?:\n|$)', content)
                        
                        if match:
                            raw_tags = [t.strip() for t in match.group(1).split(',')]
                            for t in raw_tags:
                                if t:
                                    self.tags_by_source["Characters"][t] += 1
                                    self.tag_locations[t].append(f"Character:{filename}")

                except Exception as e:
                    print(f"Error reading {filename}: {e}")

    def crawl_markdown_list(self, file_path, source_category):
        if not os.path.exists(file_path):
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith("##") or line.startswith("- **"):
                    # Header line often contains tags: ## Name (Tag1, Tag2)
                    tags = self.extract_tags_from_text(line, f"{source_category}:{line.split('(')[0].strip()}")
                    for t in tags:
                        self.tags_by_source[source_category][t] += 1
                elif line.startswith("Tags:"):
                     tags = self.extract_tags_from_text(line, f"{source_category}:Header")
                     for t in tags:
                        self.tags_by_source[source_category][t] += 1

    def crawl_outfits(self):
        outfit_root = os.path.join(self.data_dir, "outfits")
        if not os.path.exists(outfit_root):
            return
        
        for root, dirs, files in os.walk(outfit_root):
            for file in files:
                if file.endswith(".txt"):
                    path = os.path.join(root, file)
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        for line in content.split('\n'):
                            if "tags:" in line.lower():
                                try:
                                    clean = line.split(":", 1)[1].strip()
                                    clean = clean.replace("[", "").replace("]", "")
                                    raw_tags = [t.strip() for t in clean.split(',')]
                                    for t in raw_tags:
                                        if t:
                                            self.tags_by_source["Outfits"][t] += 1
                                            self.tag_locations[t].append(f"Outfit:{file}")
                                except IndexError:
                                    pass

    def run_audit(self):
        print("Crawling Data...")
        self.crawl_characters()
        self.crawl_markdown_list(os.path.join(self.data_dir, "scenes.md"), "Scenes")
        self.crawl_markdown_list(os.path.join(self.data_dir, "base_prompts.md"), "Base Prompts")
        self.crawl_markdown_list(os.path.join(self.data_dir, "poses.md"), "Poses")
        self.crawl_markdown_list(os.path.join(self.data_dir, "interactions.md"), "Interactions")
        self.crawl_outfits()
        return self.analyze()

    def normalize_tag(self, tag):
        t = tag.lower()
        prefix = None
        if t.startswith("mood:"): 
            t = t[5:]
            prefix = "Mood"
        elif t.startswith("block:"): 
            t = t[6:]
            prefix = "Block"
        return t.strip(), prefix

    def analyze(self):
        all_raw_tags = set()
        for tags in self.tags_by_source.values():
            all_raw_tags.update(tags.keys())

        # Group by normalized base
        normalized_map = defaultdict(list)
        for t in all_raw_tags:
            base, prefix = self.normalize_tag(t)
            normalized_map[base].append(t)

        conflicts = {}
        for base, originals in normalized_map.items():
            if len(originals) > 1:
                conflicts[base] = originals
            else:
                 if base.endswith('s') and base[:-1] in normalized_map:
                     conflicts[base] = originals + normalized_map[base[:-1]]

        # Dead Tag Detection
        source_sets = {s: set(t.lower() for t in tags.keys()) for s, tags in self.tags_by_source.items()}
        
        # A tag is "Dead" if it exists in one but not any other (potential typo or missing link)
        dead_tags = defaultdict(list)
        missing_bridges = []
        all_lower_tags = set()
        for s in source_sets.values():
            all_lower_tags.update(s)

        # Descriptive Exclusions (UI-focused/descriptive, doesn't need bridges)
        DESCRIPTIVE_EXCLUSIONS = {
            "female", "male", "curvy", "petite", "tall", "muscular", "skinny", "thin",
            "black", "white", "latina", "japanese", "caucasian", "nordic", "romani",
            "north-african", "mediterranean", "african", "indian", "caucasian",
            "shorthair", "longhair", "tattoos", "freckled", "glasses", "beard", "stubble",
            "tan", "pale", "athletic", "strong", "toned"
        }

        for t in all_lower_tags:
            present_in = []
            for s_name, s_tags in source_sets.items():
                if t in s_tags:
                    present_in.append(s_name)
            
            if len(present_in) == 1:
                source = present_in[0]
                # Filter out descriptive tags and short tags
                if t not in DESCRIPTIVE_EXCLUSIONS and len(t) > 3:
                    # If it's only in Characters, check if it has an alias
                    if source == "Characters":
                        if t not in self.aliases:
                            # Flag as missing bridge if high frequency
                            if self.tags_by_source["Characters"].get(t, 0) >= 5:
                                missing_bridges.append(t)
                            dead_tags[source].append(t)
                    else:
                        dead_tags[source].append(t)

        return {
            "conflicts": conflicts,
            "stats": self.tags_by_source,
            "locations": self.tag_locations,
            "dead_tags": dead_tags,
            "missing_bridges": missing_bridges
        }

    def generate_report(self, analysis, output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Tag System Audit\n\n")
            
            f.write("## Potential Conflicts (Synonyms/Casing)\n")
            f.write("Tags that look similar (Singular/Plural or Capitalization mismatches):\n\n")
            
            sorted_conflicts = sorted(analysis["conflicts"].items())
            for base, originals in sorted_conflicts:
                unique_originals = sorted(list(set(originals)))
                f.write(f"- **{base}**: {', '.join(unique_originals)}\n")

            f.write("\n## 🚩 Orphaned/Potentially Dead Tags\n")
            f.write("Tags that exist in only ONE source. (Excludes descriptive/UI tags and tags with logic aliases).\n\n")
            
            if analysis["missing_bridges"]:
                f.write("### ⚠️ Missing Content Bridges (High Frequency)\n")
                f.write("Thematic tags appearing in 5+ characters with no aliases or shared assets:\n")
                for t in sorted(analysis["missing_bridges"]):
                    f.write(f"- **{t}** (Count: {analysis['stats']['Characters'][t]})\n")
                f.write("\n")

            for source, tags in sorted(analysis["dead_tags"].items()):
                # Only show top 10 per source to avoid clutter
                f.write(f"### {source} (Top 10)\n")
                for t in sorted(tags)[:10]:
                    count = analysis["stats"][source].get(t, 0) # Fallback to 0 if not found
                    if count == 0: # Try to find original casing
                        for orig, c in analysis["stats"][source].items():
                            if orig.lower() == t:
                                t = orig
                                count = c
                                break
                    f.write(f"- {t} ({count})\n")
                f.write("\n")

            f.write("\n## Tag Frequency by Source\n")
            for source, tags in analysis["stats"].items():
                f.write(f"\n### {source}\n")
                for t, count in sorted(tags.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"- {t}: {count}\n")

        print(f"Report saved to {output_path}")

if __name__ == "__main__":
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(root_dir, "data")
    inventory = TagInventory(data_dir)
    analysis = inventory.run_audit()
    inventory.generate_report(analysis, os.path.join(root_dir, "auditing", "reports", "tag_inventory.md"))