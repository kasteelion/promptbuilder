import os
import sys
import re
from collections import defaultdict
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from logic.data_loader import DataLoader
from logic.randomizer import PromptRandomizer

class HubConnectivityAuditor:
    """Analyzes Hub & Spoke connectivity to ensure thematic coverage and character reach."""

    def __init__(self):
        self.loader = DataLoader()
        self.data = {}
        self.tag_index = defaultdict(lambda: defaultdict(list)) # tag -> category -> [names]
        self.char_reach = {}
        self.dead_ends = []

    def load_all_data(self):
        print("Loading all assets...")
        self.data['Characters'] = self.loader.load_characters()
        self.data['Styles'] = self.loader.load_base_prompts()
        self.data['Scenes'] = self.loader.load_presets("scenes.md")
        self.data['Poses'] = self.loader.load_presets("poses.md")
        self.data['Interactions'] = self.loader.load_interactions()
        
        # Load Outfits separately to get raw tags easily
        self.data['Outfits'] = self.loader.load_outfits()

    def _get_tags(self, item_data):
        if isinstance(item_data, dict):
            return [t.lower().strip() for t in item_data.get("tags", [])]
        return []

    def index_tags(self):
        print("Indexing tags across assets...")
        
        # Styles
        for name, d in self.data['Styles'].items():
            for t in self._get_tags(d):
                self.tag_index[t]['Style'].append(name)
        
        # Scenes
        for cat, items in self.data['Scenes'].items():
            for name, d in items.items():
                for t in self._get_tags(d):
                    self.tag_index[t]['Scene'].append(f"{cat}: {name}")
        
        # Outfits
        # Structure of load_outfits(): {"F": { Cat: { Name: Data } }, ...}
        for dim, categories in self.data['Outfits'].items():
            for cat, outfits in categories.items():
                for name, d in outfits.items():
                    for t in self._get_tags(d):
                        # Dedup outfits across dimensions if they have same tags
                        if name not in self.tag_index[t]['Outfit']:
                            self.tag_index[t]['Outfit'].append(name)
        
        # Interactions
        for cat, items in self.data['Interactions'].items():
            for name, d in items.items():
                for t in self._get_tags(d):
                    self.tag_index[t]['Interaction'].append(f"{cat}: {name}")

    def analyze_hub_health(self):
        print("Analyzing Hub Health...")
        hubs = {}
        for tag, counts in self.tag_index.items():
            style_count = len(counts['Style'])
            scene_count = len(counts['Scene'])
            outfit_count = len(counts['Outfit'])
            int_count = len(counts['Interaction'])
            
            # Hub Requirement: 1 Style, 2 Scenes, 3 Outfits, 3 Interactions
            is_hub = style_count >= 1 and scene_count >= 2 and outfit_count >= 3 and int_count >= 3
            
            hubs[tag] = {
                "Style": style_count,
                "Scene": scene_count,
                "Outfit": outfit_count,
                "Interaction": int_count,
                "is_hub": is_hub,
                "coverage_score": style_count + scene_count + outfit_count + int_count
            }
        return hubs

    def analyze_character_reach(self, hubs):
        print("Analyzing Character Reach...")
        hub_tags = {t for t, h in hubs.items() if h['is_hub']}
        
        # Correctly map keys for PromptRandomizer
        rng_data = {
            "characters": self.data['Characters'],
            "base_prompts": self.data['Styles'],
            "poses": self.data['Poses'],
            "scenes": self.data['Scenes'],
            "interactions": self.data['Interactions']
        }
        
        # Use Randomizer's expansion logic
        rng = PromptRandomizer(**rng_data, color_schemes={}, modifiers={}, framing={})
        
        reach_report = {}
        for char_name, char_data in self.data['Characters'].items():
            raw_tags = {t.lower().strip() for t in char_data.get("tags", [])}
            expanded_tags = rng._expand_tags(raw_tags)
            
            # Find accessible hubs
            accessible_hubs = expanded_tags.intersection(hub_tags)
            
            reach_report[char_name] = {
                "Hubs": sorted(list(accessible_hubs)),
                "Hub Count": len(accessible_hubs),
                "Total Tags": len(raw_tags)
            }
        return reach_report

    def find_dead_ends(self):
        print("Finding Dead Ends...")
        # Assets that have tags that don't overlap with any other asset category
        # For simplicity, let's just find tags that only exist in ONE category
        for tag, categories in self.tag_index.items():
            if len(categories) == 1:
                # This tag is a potential dead end if it's the ONLY tag on an asset
                pass # logic for specific asset check could go here
        return []

    def generate_report(self, hubs, reach):
        report_path = PROJECT_ROOT / "auditing" / "reports" / "hub_connectivity.md"
        print(f"Generating hub report: {report_path}")
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# Hub & Spoke Connectivity Audit\n\n")
            
            # 1. Master Hubs
            f.write("## 🏛️ Established Hubs\n")
            f.write("Tags meeting the 1/2/3/3 coverage threshold.\n\n")
            f.write("| Hub Tag | Score | Style | Scene | Outfit | Int |\n")
            f.write("|---|---|---|---|---|---|\n")
            
            sorted_hubs = sorted(hubs.items(), key=lambda x: x[1]['coverage_score'], reverse=True)
            for tag, h in sorted_hubs:
                if h['is_hub']:
                    f.write(f"| **{tag}** | {h['coverage_score']} | {h['Style']} | {h['Scene']} | {h['Outfit']} | {h['Interaction']} |\n")
            
            # 2. Weak/Potential Hubs
            f.write("\n## ⚠️ Weak/Potential Hubs\n")
            f.write("Tags that are almost hubs but missing coverage in 1-2 categories.\n\n")
            f.write("| Potential Tag | Missing Category |\n")
            f.write("|---|---|\n")
            for tag, h in sorted_hubs:
                if not h['is_hub'] and h['coverage_score'] > 5:
                    missing = []
                    if h['Style'] == 0: missing.append("Style")
                    if h['Scene'] < 2: missing.append("Scene")
                    if h['Outfit'] < 3: missing.append("Outfit")
                    if h['Interaction'] < 3: missing.append("Interaction")
                    
                    if 1 <= len(missing) <= 2:
                        f.write(f"| {tag} | {', '.join(missing)} |\n")

            # 3. Character Accessibility
            f.write("\n## 👥 Character Reach\n")
            f.write("How many thematic Hubs each character can access.\n\n")
            f.write("| Character | Hub Count | Accessible Hubs |\n")
            f.write("|---|---|---|\n")
            
            sorted_reach = sorted(reach.items(), key=lambda x: x[1]['Hub Count'])
            for name, r in sorted_reach:
                h_str = ", ".join(r['Hubs']) if r['Hubs'] else "❌ NONE"
                f.write(f"| {name} | {r['Hub Count']} | {h_str} |\n")

    def run_all(self):
        self.load_all_data()
        self.index_tags()
        hubs = self.analyze_hub_health()
        reach = self.analyze_character_reach(hubs)
        self.generate_report(hubs, reach)

if __name__ == "__main__":
    auditor = HubConnectivityAuditor()
    auditor.run_all()
