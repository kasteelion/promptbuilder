from logic.data_loader import DataLoader
import json

dl = DataLoader()
outfits = dl.load_outfits()

print(f"Loaded {len(outfits)} gender categories from outfits directory.")
for gender, cats in outfits.items():
    print(f"Gender {gender}: {len(cats)} categories")
    for cat, items in list(cats.items())[:2]:
        print(f"  Category {cat}: {len(items)} items")
        for item_name, data in list(items.items())[:1]:
            print(f"    Item {item_name}: tags={data.get('tags')}")

# Test character loading
chars = dl.load_characters()
char_name = list(chars.keys())[0]
char_data = chars[char_name]
print(f"\nCharacter {char_name}: {len(char_data['outfits'])} outfits merged.")
print(f"First few outfit names: {list(char_data['outfits'].keys())[:5]}")
