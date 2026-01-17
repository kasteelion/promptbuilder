import re
import os

def strip_full_body(filepath):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # regex to find (tag, tag, full body, tag) and remove just 'full body'
    # 1. Remove "Full Body" followed by a comma and optional space
    content = re.sub(re.compile(r'Full Body,\s*', re.IGNORECASE), '', content)
    # 2. Remove comma and optional space followed by "Full Body"
    content = re.sub(re.compile(r',\s*Full Body', re.IGNORECASE), '', content)
    # 3. Remove standalone "Full Body" inside parentheses
    content = re.sub(re.compile(r'\(Full Body\)', re.IGNORECASE), '()', content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
        print(f"Stripped 'Full Body' from {filepath}")

if __name__ == "__main__":
    strip_full_body(r'c:\Users\parking\Desktop\promptbuilder\data\poses.md')
    strip_full_body(r'c:\Users\parking\Desktop\promptbuilder\data\interactions.md')
