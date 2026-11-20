import re
import yaml
import os
from core.config import THEMES as FALLBACK_THEMES
from utils import logger

def load_themes_from_markdown(file_path):
    """
    Parses a markdown file to extract theme definitions.
    
    Expected format:
    ## Theme Name
    ```yaml
    key: value
    ...
    ```
    """
    if not os.path.exists(file_path):
        logger.warning(f"Themes file not found at {file_path}. Using fallback themes.")
        return FALLBACK_THEMES

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        themes = {}
        # improved regex to capture header and subsequent yaml block
        # looks for "## Name" followed by content until "```yaml" ... "```"
        
        # Strategy: Split by "## " to get sections
        sections = content.split("## ")
        
        for section in sections:
            if not section.strip():
                continue
            
            # First line is title
            lines = section.split('\n')
            title = lines[0].strip()
            
            # Find yaml block
            yaml_match = re.search(r'```yaml\s+(.*?)\s+```', section, re.DOTALL)
            if yaml_match:
                yaml_content = yaml_match.group(1)
                try:
                    theme_data = yaml.safe_load(yaml_content)
                    if isinstance(theme_data, dict):
                        themes[title] = theme_data
                except yaml.YAMLError as e:
                    logger.error(f"Error parsing YAML for theme '{title}': {e}")
        
        if not themes:
            logger.warning("No themes found in markdown. Using fallback.")
            return FALLBACK_THEMES
            
        return themes

    except Exception as e:
        logger.error(f"Failed to load themes from {file_path}: {e}")
        return FALLBACK_THEMES
