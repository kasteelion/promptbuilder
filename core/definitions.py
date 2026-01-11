from typing import TypedDict, List, Dict, Optional, Any

class OutfitData(TypedDict, total=False):
    """Data structure for an outfit definition."""
    description: str
    modifiers: Dict[str, str]
    tags: List[str]
    # Legacy/flexible fields
    Bottom: Optional[str]
    one_piece: bool

class CharacterData(TypedDict, total=False):
    """Data structure for a character definition."""
    appearance: str
    summary: Optional[str]
    tags: List[str]
    outfits: Dict[str, Any]  # Value can be str or OutfitData
    photo: Optional[str]
    gender: str
    gender_explicit: bool
    modifier: Optional[str]
    signature_color: Optional[str]
    traits: Dict[str, str]

class SelectedCharacterConfig(TypedDict, total=False):
    """Configuration for a single selected character in the prompt."""
    name: str
    outfit: str
    pose_category: str
    pose_preset: str
    action_note: str # custom pose
    framing_mode: str
    outfit_traits: List[str]
    outfit_modifier: str
    custom_modifiers: Dict[str, str]
    color_scheme: str
    use_signature_color: bool
    character_traits: List[str]

class PromptConfig(TypedDict, total=False):
    """Top-level configuration for prompt generation."""
    selected_characters: List[SelectedCharacterConfig]
    base_prompt: str
    scene: str
    notes: str
    # Other potential top-level config keys
