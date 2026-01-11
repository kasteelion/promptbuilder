import os
import re
import json
from collections import defaultdict

class TagInventory:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.tags_by_source = {
            "Characters": defaultdict(int),
            "Scenes": defaultdict(int),
            "Base Prompts": defaultdict(int),
            "Outfits": defaultdict(int)
        }
        self.tag_locations = defaultdict(list) # tag -> list of source files/sections

    def extract_tags_from_text(self, text, source_name):
        """Extract tags from text lines like 'Tags: (Tag1, Tag2)' or '## Name (Tag1, Tag2)'"""
        tags = []
        match = re.search(r'\((.*?)\)', text)
        if match:
            content = match.group(1)
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
            # Filter distinct variations excluding just prefix differences if base is same case
            # Actually we want to catch "Sport" vs "sport" vs "Sports"
            
            # Simple conflict: if > 1 distinct string representation matches this base (ignoring prefix for now? No, include them to show consistency)
            if len(originals) > 1:
                conflicts[base] = originals
            else:
                 # Check plural vs singular
                 if base.endswith('s') and base[:-1] in normalized_map:
                     conflicts[base] = originals + normalized_map[base[:-1]]

        return {
            "conflicts": conflicts,
            "stats": self.tags_by_source,
            "locations": self.tag_locations
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
    inventory.generate_report(analysis, os.path.join(root_dir, "output", "reports", "tag_inventory.md"))