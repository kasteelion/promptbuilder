from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, PrivateAttr

class OutfitItem(BaseModel):
    """Represents a component of an outfit (e.g., Top, Bottom)."""
    description: str
    tags: List[str] = Field(default_factory=list)
    one_piece: bool = False
    modifiers: Dict[str, str] = Field(default_factory=dict)
    # Add other common fields found in outfit dictionaries
    Top: Optional[str] = None
    Bottom: Optional[str] = None
    Footwear: Optional[str] = None
    Accessories: Optional[str] = None
    Hair: Optional[str] = None
    Makeup: Optional[str] = None

class CharacterMetadata(BaseModel):
    """Lightweight metadata for gallery display."""
    name: str
    tags: List[str] = Field(default_factory=list)
    photo: Optional[str] = None
    vibe: Optional[str] = None
    bearing: Optional[str] = None
    age_presentation: Optional[str] = None
    gender: str = "F"
    mtime: float = 0.0
    file_size: int = 0

class CharacterDetails(BaseModel):
    """Full character details for prompt generation."""
    name: str
    appearance: str
    summary: Optional[str] = None
    photo: Optional[str] = None
    gender: str = "F"
    gender_explicit: bool = False
    modifier: Optional[str] = None
    signature_color: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    age_presentation: Optional[str] = None
    vibe: Optional[str] = None
    bearing: Optional[str] = None
    traits: Dict[str, str] = Field(default_factory=dict)
    outfits: Dict[str, Union[str, Dict[str, Any]]] = Field(default_factory=dict)
    outfits_categorized: Dict[str, Dict[str, Union[str, Dict[str, Any]]]] = Field(default_factory=dict)

class SelectedCharacterConfig(BaseModel):
    """Configuration for a character selected in the roster."""
    name: str
    outfit: str = "Base"
    outfit_category: Optional[str] = None
    outfit_traits: List[str] = Field(default_factory=list)
    outfit_modifier: Optional[str] = None
    custom_modifiers: Dict[str, str] = Field(default_factory=dict)
    pose_category: Optional[str] = None
    pose_preset: Optional[str] = None
    action_note: Optional[str] = None
    framing_mode: Optional[str] = None
    color_scheme: Optional[str] = None
    use_signature_color: bool = False
    character_traits: List[str] = Field(default_factory=list)
    _expanded: bool = PrivateAttr(default=True)

class PromptConfig(BaseModel):
    """Configuration for global prompt generation."""
    base_prompt: str = "Detailed"
    scene: str = ""
    notes: str = ""
    selected_characters: List[SelectedCharacterConfig] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
