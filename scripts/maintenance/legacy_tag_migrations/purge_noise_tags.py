import re
import os

def purge_noise_tags(filepath):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # List of tags to purge completely
    purge_list = [
        "Full Body", "Upper Body", "Mid Shot", "Mid-Shot", 
        "Close-Up", "Close Up", "Portrait", "Wide Shot", "Cowboy Shot",
        "Static", "Precise"
    ]
    
    for tag in purge_list:
        # Case insensitive regex to find the tag in parentheses contexts
        # Handles: (Tag, ...), (..., Tag, ...), (..., Tag)
        
        # 1. Tag followed by comma and space
        content = re.sub(re.compile(rf'{tag},\s*', re.IGNORECASE), '', content)
        # 2. Comma and space followed by Tag
        content = re.sub(re.compile(rf',\s*{tag}', re.IGNORECASE), '', content)
        # 3. Standalone Tag in parentheses
        content = re.sub(re.compile(rf'\({tag}\)', re.IGNORECASE), '()', content)
        # 4. Leading Tag in parentheses
        content = re.sub(re.compile(rf'\(\s*{tag}', re.IGNORECASE), '(', content)
        # 5. Trailing Tag in parentheses
        content = re.sub(re.compile(rf'{tag}\s*\)', re.IGNORECASE), ')', content)

    # Clean up artifacts
    # Empty parentheses
    content = re.sub(r'\(\s*\)', '', content)
    # Double spaces/commas inside parents or in general
    content = re.sub(r'\(\s*,', '(', content)
    content = re.sub(r',\s*\)', ')', content)
    # Remove any leading spaces inside parentheses
    content = re.sub(r'\( ', '(', content)
    # Remove any trailing spaces inside parentheses
    content = re.sub(r' \)', ')', content)
    # Remove empty parens with a space before them
    content = re.sub(r' \(\)', '', content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
        print(f"Purged noise tags from {filepath}")

if __name__ == "__main__":
    data_files = [
        r'c:\Users\parking\Desktop\promptbuilder\data\poses.md',
        r'c:\Users\parking\Desktop\promptbuilder\data\interactions.md',
        r'c:\Users\parking\Desktop\promptbuilder\data\scenes.md',
        r'c:\Users\parking\Desktop\promptbuilder\data\base_prompts.md'
    ]
    for df in data_files:
        purge_noise_tags(df)
