import re
import os

def strip_framing_tags(filepath):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # List of framing tags to remove
    framing_tags = [
        "Full Body", "Upper Body", "Mid Shot", "Mid-Shot", 
        "Close-Up", "Close Up", "Portrait", "Wide Shot", "Cowboy Shot"
    ]
    
    for tag in framing_tags:
        # regex to find tag followed by a comma and optional space
        content = re.sub(re.compile(rf'{tag},\s*', re.IGNORECASE), '', content)
        # regex to find comma and optional space followed by tag
        content = re.sub(re.compile(rf',\s*{tag}', re.IGNORECASE), '', content)
        # regex to find standalone tag inside parentheses
        content = re.sub(re.compile(rf'\({tag}\)', re.IGNORECASE), '()', content)
        # regex to find tag preceded by open paren
        content = re.sub(re.compile(rf'\(\s*{tag}', re.IGNORECASE), '(', content)
        # regex to find tag followed by close paren
        content = re.sub(re.compile(rf'{tag}\s*\)', re.IGNORECASE), ')', content)

    # Clean up empty parentheses and double spaces/commas
    content = re.sub(r'\(\s*\)', '', content)
    content = re.sub(r'\(\s*,', '(', content)
    content = re.sub(r',\s*\)', ')', content)
    content = re.sub(r'\( ', '(', content)
    content = re.sub(r' \)', ')', content)
    # Remove any empty parentheses that might have been left
    content = re.sub(r' \(\)', '', content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
        print(f"Stripped framing tags from {filepath}")

if __name__ == "__main__":
    strip_framing_tags(r'c:\Users\parking\Desktop\promptbuilder\data\poses.md')
    strip_framing_tags(r'c:\Users\parking\Desktop\promptbuilder\data\interactions.md')
