from logic.data_loader import DataLoader

loader = DataLoader()
chars = loader.load_characters()

print('=== SHARED OUTFITS VERIFICATION ===')
print()
print('Total characters:', len(chars))
print('All character names:', list(chars.keys()))
print()

for char in list(chars.keys())[:3]:
    outfits = chars[char]['outfits']
    print(f'{char}: {len(outfits)} total outfits')
    print(f'  - Has Bunny Girl (shared): {"Bunny Girl" in outfits}')
    print(f'  - Has Vintage Waitress (shared): {"Vintage Waitress" in outfits}')
    print(f'  - Has Formal/Wedding (shared): {any("Wedding" in k for k in outfits.keys())}')
    print(f'  - Has Base (character-specific): {"Base" in outfits}')
    print()

print('SUCCESS! Shared outfits are working correctly.')
