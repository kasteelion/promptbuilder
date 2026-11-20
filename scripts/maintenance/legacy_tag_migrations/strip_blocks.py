import re
import os

def strip_blocks(filepath):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Remove block:Tag followed by a comma and space
    content = re.sub(r'block:[^,\)]+,\s*', '', content)
    # 2. Remove comma and space followed by block:Tag
    content = re.sub(r',\s*block:[^,\)]+', '', content)
    # 3. Remove standalone block:Tag
    content = re.sub(r'block:[^,\)]+', '', content)
    
    # Clean up empty parentheses
    content = re.sub(r'\(\s+\)', '()', content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
        print(f"Stripped blocks from {filepath}")

if __name__ == "__main__":
    strip_blocks(r'c:\Users\parking\Desktop\promptbuilder\data\scenes.md')
    strip_blocks(r'c:\Users\parking\Desktop\promptbuilder\data\base_prompts.md')
