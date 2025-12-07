from pydantic import BaseModel
from typing import Dict, Optional

class Outfit(BaseModel):
    Top: Optional[str] = None
    Bottom: Optional[str] = None
    Footwear: Optional[str] = None
    Accessories: Optional[str] = None
    Hair: Optional[str] = None
    Makeup: Optional[str] = None
    extras: Dict[str, str] = {}

class Character(BaseModel):
    name: str
    appearance: str
    outfits: Dict[str, Outfit]

class BasePrompt(BaseModel):
    name: str
    text: str

class Pose(BaseModel):
    category: str
    preset: str
    description: str
