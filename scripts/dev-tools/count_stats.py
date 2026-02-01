import re
from collections import defaultdict

with open('output/reports/prompt_distribution_flow.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all artstyle class definitions
artstyle_nodes = set(re.findall(r'class (\w+) artstyle', content))

# Now find all links that POINT to an artstyle node
links = re.findall(r'-->\|(\d+)\| (\w+)(?:\[|")', content)
stats = defaultdict(int)

node_names = {
    "PhotorealisticHighFi": "Photorealistic",
    "SportsActionFrozenVe": "Sports Action",
    "DigitalPaintingExpre": "Digital Painting",
    "WatercolorImpression": "Watercolor",
    "LowPoly3D": "Low-Poly 3D",
    "AnimeStyleDynamicCel": "Anime",
    "ArtgermStyleLuminous": "Artgerm",
    "ClassicAnimeCleanCel": "Classic Anime",
    "WesternComicBook": "Western Comic",
    "CyberpunkNeon": "Cyberpunk",
    "VintageFilmAnalogNos": "Vintage Film",
    "VintagePinUpGlamorou": "Vintage Pin-Up",
    "ChibiStyleSuperDefor": "Chibi",
    "FilmNoirShadowsandSm": "Film Noir",
    "ClassicFantasyOil": "Classic Fantasy Oil",
    "SketchStyleEnergetic": "Sketch Style"
}

for count, node in links:
    if node in artstyle_nodes:
        friendly = node_names.get(node, node)
        stats[friendly] += int(count)

print("Art Style Distribution:")
total = sum(stats.values())
for style, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
    pct = (count / total) * 100 if total > 0 else 0
    print(f"{style}: {count} ({pct:.1f}%)")
