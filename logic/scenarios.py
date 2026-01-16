"""Scenario-First Architecture components for PromptRandomizer."""
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional

@dataclass
class Role:
    """A specific character role within a scenario."""
    name: str
    required_tags: List[str] = field(default_factory=list)
    blocked_tags: List[str] = field(default_factory=list)
    preferred_outfits: List[str] = field(default_factory=list)
    preferred_poses: List[str] = field(default_factory=list)
    interaction_tags: List[str] = field(default_factory=list)
    allowed_outfit_categories: List[str] = field(default_factory=list) # STRICT WHITELIST
    allowed_pose_categories: List[str] = field(default_factory=list)   # STRICT WHITELIST

@dataclass
class Scenario:
    """A global thematic context for a prompt generation."""
    name: str
    vibe_tags: List[str]
    allowed_scene_categories: List[str]
    roles: List[Role]
    blocked_global_tags: List[str] = field(default_factory=list)
    default_style_tags: List[str] = field(default_factory=list)
    exclusive_notes: bool = True # If True, ONLY items matching vibe_tags are allowed
    min_characters: int = 1
    max_characters: int = 3
    force_interaction: bool = False
    role_slots: List[str] = field(default_factory=list) # Ordered list of Role names to fill first

class ScenarioRegistry:
    """Registry of available scenarios."""
    
    def __init__(self):
        self.scenarios = {}
        self._initialize_defaults()

    def register(self, scenario: Scenario):
        self.scenarios[scenario.name] = scenario

    def get_random(self) -> Scenario:
        import random
        return random.choice(list(self.scenarios.values()))

    def _initialize_defaults(self):
        # 1. NEON NOIR / CYBERPUNK
        self.register(Scenario(
            name="Neon Noir Heist",
            vibe_tags=["cyberpunk", "neon", "rainy", "tech", "urban", "night", "gritty"],
            allowed_scene_categories=["Urban", "Street", "City", "Industrial", "Night", "Cyberpunk & Futuristic"],
            min_characters=2,
            max_characters=3,
            force_interaction=True,
            role_slots=["The Specialist", "The Handler"],
            roles=[
                Role(
                    name="The Specialist",
                    required_tags=["tactical", "leather", "techgear", "dark"],
                    blocked_tags=["bright", "floral", "preppy"],
                    preferred_poses=["Action", "Tactical", "Standing"],
                    allowed_outfit_categories=["Tactical", "Cyberpunk", "Leather"],
                    allowed_pose_categories=["Dynamic & Movement Poses", "Badass & Tactical", "Fashion & Portrait Poses"]
                ),
                Role(
                    name="The Handler",
                    required_tags=["business", "sleek", "tech", "glasses"],
                    blocked_tags=["messy", "athletic"],
                    preferred_poses=["Sitting", "Intellectual", "Monitoring"],
                    allowed_outfit_categories=["Business", "Cyberpunk", "Sleek"],
                    allowed_pose_categories=["Basic Poses", "Artistic & Dramatic Poses", "Sci-Fi & Cyberpunk"]
                )
            ],
            default_style_tags=["Cyberpunk", "Neon City"]
        ))

        # 2. HIGH FANTASY
        self.register(Scenario(
            name="Fantasy Quest",
            vibe_tags=["fantasy", "medieval", "magic", "nature", "epic", "cinematic"],
            allowed_scene_categories=["Forest", "Mountain", "River", "Waterfall", "Temple", "Castle", "Fantasy & DND"],
            min_characters=2,
            max_characters=4,
            force_interaction=True,
            role_slots=["Warrior", "Mage"],
            roles=[
                Role(
                    name="Warrior",
                    required_tags=["armor", "leather", "rugged", "combat"],
                    blocked_tags=["modern", "office", "tech"],
                    preferred_poses=["Action", "Combat", "Standing"],
                    allowed_outfit_categories=["Armor", "Fantasy", "Leather"],
                    allowed_pose_categories=["Dynamic & Movement Poses", "Badass & Tactical", "Fantasy & Combat Stances"]
                ),
                Role(
                    name="Mage",
                    required_tags=["robe", "silk", "mystical", "jewelry"],
                    blocked_tags=["heavy armor", "modern", "sport"],
                    preferred_poses=["Mystical", "Casting", "Regal"],
                    allowed_outfit_categories=["Fantasy", "Silk", "Robes"],
                    allowed_pose_categories=["Basic Poses", "Artistic & Dramatic Poses", "Aura & Power", "Fantasy & Combat Stances"]
                )
            ],
            default_style_tags=["High Fantasy", "Cinematic Epic"]
        ))

        # 3. ATHLETIC TRAINING
        self.register(Scenario(
            name="Elite Training",
            vibe_tags=["athletic", "sweat", "focus", "fitness", "dynamic"],
            allowed_scene_categories=["Gym", "Stadium", "Track", "Park", "Basketball Court", "Volleyball Court", "Sports & Athletics"],
            min_characters=1,
            max_characters=2,
            roles=[
                Role(
                    name="Athlete",
                    required_tags=["sport", "athletic", "activewear", "sweat"],
                    blocked_tags=["formal", "business", "jeans", "pajamas"],
                    preferred_poses=["Athletic", "Action", "Training", "Stretching"],
                    allowed_outfit_categories=["Activewear", "Sport", "Gym"],
                    allowed_pose_categories=["Dynamic & Movement Poses", "Team Sports", "Combat Sports", "Gym & Fitness"]
                )
            ],
            default_style_tags=["Realistic", "High Detail"]
        ))

        # 4. COZY DOMESTIC
        self.register(Scenario(
            name="Cozy Morning",
            vibe_tags=["warm", "soft", "morning", "cozy", "domestic", "relaxed"],
            allowed_scene_categories=["Bedroom", "Kitchen", "Living Room", "Indoors", "Domestic & Home"],
            min_characters=1,
            max_characters=2,
            roles=[
                Role(
                    name="Waking Up",
                    required_tags=["pajamas", "soft", "loungewear", "mornings"],
                    blocked_tags=["armor", "formal", "outdoor", "shoes"],
                    preferred_poses=["Sleep", "Sitting", "Stretching", "Relaxed"],
                    allowed_outfit_categories=["Lounge", "Sleepwear", "Casual"],
                    allowed_pose_categories=["Basic Poses", "Relaxed & Intimate Poses", "Soft & Aesthetic Poses"]
                )
            ],
            default_style_tags=["Soft Lighting", "Warm Tones"]
        ))

        # 5. HIGH FASHION GALA
        self.register(Scenario(
            name="Red Carpet Gala",
            vibe_tags=["formal", "luxury", "glamour", "elegant", "high-fashion"],
            allowed_scene_categories=["Gala", "Ballroom", "Art Gallery", "Museum", "Palace", "Indoor Social Spaces"],
            min_characters=1,
            max_characters=3,
            roles=[
                Role(
                    name="Star",
                    required_tags=["formal", "evening", "gown", "tuxedo", "elegant", "jewelry"],
                    blocked_tags=["casual", "sport", "pajamas", "distressed"],
                    preferred_poses=["Glamour", "Regal", "Confident", "Standing"],
                    allowed_outfit_categories=["Formal", "Evening", "Luxury"],
                    allowed_pose_categories=["Basic Poses", "Fashion & Portrait Poses", "Artistic & Dramatic Poses", "Cultural & Traditional Poses"]
                )
            ],
            default_style_tags=["High Fashion", "Luxe"]
        ))

        # 6. RUGGED EXPLORATION
        self.register(Scenario(
            name="Mountain Expedition",
            vibe_tags=["rugged", "adventure", "hiking", "nature", "outdoor", "cold"],
            allowed_scene_categories=["Mountain", "Forest", "Snow", "Canyon", "Waterfall", "Nature & Outdoors"],
            min_characters=1,
            max_characters=3,
            role_slots=["Lead Explorer"],
            roles=[
                Role(
                    name="Lead Explorer",
                    required_tags=["hiking", "boots", "jacket", "rugged", "backpack"],
                    blocked_tags=["formal", "dress", "heels", "swimwear", "pajamas"],
                    preferred_poses=["Action", "Standing", "Watchful"],
                    allowed_outfit_categories=["Outdoor", "Rugged", "Hiking"],
                    allowed_pose_categories=["Basic Poses", "Dynamic & Movement Poses", "Badass & Tactical"]
                ),
                Role(
                    name="Support",
                    required_tags=["utility", "vest", "rugged", "pants"],
                    blocked_tags=["formal", "business", "swimwear"],
                    preferred_poses=["Sitting", "Relaxed", "Watchful"],
                    allowed_outfit_categories=["Outdoor", "Utility", "Casual"],
                    allowed_pose_categories=["Basic Poses", "Relaxed & Intimate Poses"]
                )
            ],
            default_style_tags=["National Geographic", "Cinematic Landscape"]
        ))

        # 7. CYBERPUNK CLUB
        self.register(Scenario(
            name="After Hours Club",
            vibe_tags=["cyberpunk", "neon", "party", "dance", "electronic", "urban"],
            allowed_scene_categories=["Nightclub", "Bar", "Underground", "Street", "Nightlife & Bars"],
            min_characters=2,
            max_characters=5,
            force_interaction=True,
            role_slots=["Dancer", "Bouncer"],
            roles=[
                Role(
                    name="Dancer",
                    required_tags=["party", "neon", "latex", "fashion", "edgy"],
                    blocked_tags=["formal", "office", "armor", "hiking"],
                    preferred_poses=["Dance", "Dynamic", "Confident"],
                    allowed_outfit_categories=["Cyberpunk", "Party", "Edgy"],
                    allowed_pose_categories=["Dynamic & Movement Poses", "Fashion & Portrait Poses", "Dance & Performance Poses"]
                ),
                Role(
                    name="Bouncer",
                    required_tags=["tactical", "leather", "tough", "black"],
                    blocked_tags=["bright", "floral", "preppy"],
                    preferred_poses=["Standing", "Watchful", "Guarding"],
                    allowed_outfit_categories=["Tactical", "Leather", "Security"],
                    allowed_pose_categories=["Basic Poses", "Badass & Tactical"]
                )
            ],
            default_style_tags=["Cyberpunk Night", "Vibrant Neon"]
        ))
