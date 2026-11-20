import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "src"))

from logic.data_loader import DataLoader
from utils.gemma_client import GemmaClient
import re

def safe_print(text):
    try:
        print(text, flush=True)
    except UnicodeEncodeError:
        print(text.encode('ascii', 'replace').decode(), flush=True)

def generate_affinities():
    dl = DataLoader()
    gemma = GemmaClient()
    
    safe_print("Loading data...")
    chars_meta = dl.load_characters_metadata()
    
    # Load available options to provide to Gemma
    base_prompts = list(dl.load_base_prompts().keys())
    scenes = dl.load_presets("scenes.md")
    scene_categories = list(scenes.keys())
    
    outfits = dl.load_outfits()
    # Collect all unique outfit tags
    outfit_tags = set()
    for gender, categories in outfits.items():
        if isinstance(categories, dict):
            for cat, items in categories.items():
                if isinstance(items, dict):
                    for item_name, data in items.items():
                        if isinstance(data, dict) and "tags" in data:
                            outfit_tags.update(data["tags"])
    outfit_tags_list = list(outfit_tags)[:50] # Limit to 50 for context size
    
    safe_print(f"Found {len(chars_meta)} characters.")
    safe_print(f"Available Styles: {len(base_prompts)}")
    safe_print(f"Available Scene Categories: {len(scene_categories)}")
    
    for name, meta in chars_meta.items():
        char_file = dl._character_file_map.get(name)
        if not char_file or not char_file.exists():
            continue
            
        text = char_file.read_text(encoding="utf-8")
        if "**Affinities:**" in text:
            safe_print(f"Skipping {name}, already has Affinities.")
            continue
            
        safe_print(f"Generating affinities for {name}...")
        
        prompt = f"""
You are an expert character analyst. Your task is to analyze the following character and determine their preferred aesthetic "Affinities".
You must choose the affinities from the provided lists of available options.

AVAILABLE STYLES: {', '.join(base_prompts)}
AVAILABLE SCENE CATEGORIES: {', '.join(scene_categories)}
AVAILABLE OUTFIT TAGS: {', '.join(outfit_tags_list)}

CHARACTER PROFILE:
Name: {name}
Gender: {meta.gender}
Tags: {', '.join(meta.tags)}
Vibe: {meta.vibe}
Bearing: {meta.bearing}
Age Presentation: {meta.age_presentation}

Based on this character's vibe, tags, and bearing, select:
1. 2 to 4 Styles that best match their aesthetic.
2. 2 to 4 Scene Categories they would naturally fit into.
3. 3 to 5 Outfit Tags that match their fashion sense.

OUTPUT FORMAT:
Respond ONLY with the following exact markdown block, replacing the brackets with your comma-separated choices. Do not include any other text, explanation, or code blocks.

**Affinities:**
- Styles: [Style1, Style2]
- Scenes: [Category1, Category2]
- Outfit_Tags: [Tag1, Tag2]
"""
        
        try:
            result = gemma.generate(prompt)
            # Clean up response
            result = re.sub(r"^```markdown\n?", "", result)
            result = re.sub(r"```$", "", result).strip()
            
            if "**Affinities:**" in result:
                # Append to file
                new_text = text + "\n\n" + result + "\n"
                char_file.write_text(new_text, encoding="utf-8")
                safe_print(f"Successfully added affinities for {name}")
            else:
                safe_print(f"Failed to parse response for {name}:\n{result}")
                
        except Exception as e:
            safe_print(f"Error processing {name}: {e}")

if __name__ == "__main__":
    generate_affinities()
