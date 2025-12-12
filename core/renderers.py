"""Renderers for converting prompt data into formatted text.

This module provides specialized renderers for different prompt components:
- OutfitRenderer: Formats outfit dictionaries into text
- PoseRenderer: Formats pose descriptions
- SceneRenderer: Formats scene/setting information
- NotesRenderer: Formats additional notes
- CharacterRenderer: Formats complete character information

Each renderer follows a consistent interface with a static render() method.
"""

import re


def strip_html_comments(text: str) -> str:
    """Remove HTML comment blocks from text.
    
    Args:
        text: Input text potentially containing HTML comments
    
    Returns:
        Text with all <!-- ... --> blocks removed
    """
    if not text:
        return text
    # Remove HTML comments (including multiline)
    return re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL).strip()


class OutfitRenderer:
    """Renders outfit data into formatted text.
    
    Supports both detailed (multi-line) and compact (single-line) output modes.
    Handles structured outfit dictionaries with standard keys (Top, Bottom, etc.)
    and custom fields.
    """
    
    @staticmethod
    def render(outfit: dict, mode: str = "detailed") -> str:
        """Render outfit dictionary to formatted text.
        
        Args:
            outfit: Dictionary with outfit components. Standard keys include:
                   - Top: Upper body clothing
                   - Bottom: Lower body clothing
                   - Footwear: Shoes, boots, etc.
                   - Accessories: Jewelry, bags, etc.
                   - Hair: Hairstyle description
                   - Makeup: Makeup description
                   Additional keys are treated as custom fields.
            mode: Output mode - "detailed" for multi-line format with labels,
                 anything else for compact single-line format
        
        Returns:
            Formatted outfit text. Empty string if outfit is empty or None.
            
        Examples:
            >>> outfit = {"Top": "Blue shirt", "Bottom": "Jeans"}
            >>> OutfitRenderer.render(outfit, "detailed")
            '- Top: Blue shirt\\n- Bottom: Jeans'
            
            >>> OutfitRenderer.render(outfit, "compact")
            'Blue shirt; Jeans'
        """
        if not outfit:
            return ""
        if isinstance(outfit, dict):
            keys = ["Top", "Bottom", "Footwear", "Accessories", "Hair", "Makeup"]
            present = [f"- {k}: {outfit[k]}" for k in keys if outfit.get(k)]
            extras = [f"- {k}: {v}" for k, v in outfit.items() if k not in keys]
            lines = present + extras
            return "\n".join(lines) if mode == "detailed" else "; ".join([entry.split(": ")[1] for entry in lines])
        return outfit


class PoseRenderer:
    """Renders pose/action descriptions.
    
    Simple passthrough renderer that returns the pose description as-is.
    """
    
    @staticmethod
    def render(pose_description: str) -> str:
        """Render pose description.
        
        Args:
            pose_description: Text description of the pose or action
        
        Returns:
            The pose description unchanged, or empty string if None
        """
        return pose_description or ""


class SceneRenderer:
    """Renders scene/setting information with formatting.
    
    Adds markdown-style headers and separators to scene descriptions.
    """
    
    @staticmethod
    def render(scene: str) -> str:
        """Render scene description with header and separator.
        
        Args:
            scene: Text description of the scene/setting
        
        Returns:
            Formatted scene text with **SCENE/SETTING:** header and separator.
            Empty string if scene is empty or whitespace-only.
            
        Example:
            >>> SceneRenderer.render("Coffee shop interior")
            '**SCENE/SETTING:**\\nCoffee shop interior\\n---'
        """
        if not scene.strip():
            return ""
        return f"**SCENE/SETTING:**\n{scene}\n---"


class NotesRenderer:
    """Renders additional notes with formatting.
    
    Adds markdown-style headers to notes sections.
    """
    
    @staticmethod
    def render(notes: str) -> str:
        """Render additional notes with header.
        
        Args:
            notes: Additional notes or instructions text
        
        Returns:
            Formatted notes with **Additional Notes:** header.
            Empty string if notes is empty or whitespace-only.
            
        Example:
            >>> NotesRenderer.render("Focus on lighting")
            '**Additional Notes:**\\nFocus on lighting'
        """
        return f"**Additional Notes:**\n{notes}" if notes.strip() else ""


class CharacterRenderer:
    """Renders complete character information.
    
    Combines character appearance, outfit, and pose into a formatted block
    with appropriate headers and separators.
    """
    
    @staticmethod
    def render(idx: int, character_name: str, appearance: str, outfit: str, pose: str) -> str:
        """Render complete character information block.
        
        Args:
            idx: Character index (0-based). Used to determine header format.
                First character (0) gets "CHARACTER:", others get "CHARACTER N:"
            character_name: Name of the character
            appearance: Physical appearance description
            outfit: Formatted outfit text (from OutfitRenderer)
            pose: Pose/action description (from PoseRenderer)
        
        Returns:
            Formatted character block with header, appearance, outfit, pose,
            and trailing separator (---).
            
        Example:
            >>> CharacterRenderer.render(
            ...     0, "Alice", "Tall woman", "- Top: Blue dress", "Standing"
            ... )
            '**CHARACTER: Alice**\\n**Appearance:**\\nTall woman\\n**Outfit:**\\n- Top: Blue dress\\n**Pose/Action:**\\nStanding\\n---'
        """
        header = f"**CHARACTER {idx+1}: {character_name}**" if idx > 0 else f"**CHARACTER: {character_name}**"
        parts = [header]
        
        # Strip HTML comments from appearance text
        if appearance:
            clean_appearance = strip_html_comments(appearance)
            if clean_appearance:
                parts.append(f"**Appearance:**\n{clean_appearance}")
        
        if outfit:
            parts.append(f"**Outfit:**\n{outfit}")
        if pose:
            parts.append(f"**Pose/Action:**\n{pose}")
        parts.append("---")
        return "\n".join(parts)
