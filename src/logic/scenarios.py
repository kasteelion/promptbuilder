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
    blocked_global_tags: List[str] = field(default_factory=list)
    default_style_tags: List[str] = field(default_factory=list)
    exclusive_notes: bool = True # If True, ONLY items matching vibe_tags are allowed
    required_scene_tags: List[str] = field(default_factory=list) # [NEW] Strict scene filtering
    min_characters: int = 2
    max_characters: int = 3
    force_interaction: bool = False
    role_slots: List[str] = field(default_factory=list) # Ordered list of Role names to fill first
    weight: float = 1.0 # Selection weight (1.0 = normal, <1.0 = less likely, >1.0 = more likely)

class ScenarioRegistry:
    """Registry of available scenarios."""
    
    def __init__(self):
        self.scenarios = {}
        self._initialize_defaults()

    def register(self, scenario: Scenario):
        self.scenarios[scenario.name] = scenario

    def get_all(self) -> List[Scenario]:
        """Returns all registered scenarios."""
        return list(self.scenarios.values())

    def get_random(self) -> Scenario:
        import random
        # Weighted random selection based on scenario weights
        scenarios_list = self.get_all()
        weights = [s.weight for s in scenarios_list]
        return random.choices(scenarios_list, weights=weights, k=1)[0]

    def _initialize_defaults(self):
        # =====================================================================
        # RIGID BRANCH 1: URBAN NOIR (The "Neon" Branch)
        # =====================================================================
        self.register(Scenario(
            name="Urban Noir Operation",
            vibe_tags=["cyberpunk", "neon", "rainy", "tech", "urban", "night", "gritty"],
            allowed_scene_categories=["Urban", "Street", "City", "Industrial", "Night", "Cyberpunk & Futuristic", "Nightlife & Bars"],
            min_characters=2,
            max_characters=3,
            force_interaction=True,
            role_slots=["Operative", "Informant"],
            roles=[
                Role(
                    name="Operative",
                    required_tags=["combat_tactical", "leather", "techgear", "dark"],
                    blocked_tags=["bright", "floral", "preppy", "vintage"],
                    preferred_poses=["Action", "Tactical", "Standing"],
                    allowed_outfit_categories=["Combat & Tactical", "Cyberpunk & Sci-Fi", "Leather", "Alternative & Edgy"],
                    allowed_pose_categories=["Action & Motion", "Combat & Tactical", "Fashion & Glamour"]
                ),
                Role(
                    name="Informant",
                    required_tags=["edgy", "fashion", "tech", "streetwear"],
                    blocked_tags=["messy", "athletic", "medieval"],
                    preferred_poses=["Sitting", "Lean", "Smoking"],
                    allowed_outfit_categories=["Alternative & Edgy", "Cyberpunk & Sci-Fi", "Casual & Everyday"],
                    allowed_pose_categories=["Casual & Daily Life", "Fashion & Glamour", "Thematic & Cinematic"]
                )
            ],
            default_style_tags=["Cyberpunk", "Neon Noir", "Film Noir"],
            blocked_global_tags=["basketball", "football", "mma", "boxing", "baseball", "softball", "tennis", "soccer", "volleyball", "bowling", "track", "gymnastics", "swimming", "combat_sport"],
            weight=1.0
        ))

        # =====================================================================
        # RIGID BRANCH 2: HIGH FANTASY (The "Mythic" Branch)
        # =====================================================================
        self.register(Scenario(
            name="Mythic Quest",
            vibe_tags=["fantasy", "medieval", "magic", "nature", "epic", "cinematic"],
            allowed_scene_categories=["Fantasy & DND", "Castle", "Ruins", "Nature & Outdoors", "Forest", "Mountain"],
            blocked_global_tags=["modern", "tech", "office", "car", "phone", "computer", "gun", "neon", "basketball", "football", "mma", "boxing", "baseball", "softball", "tennis", "soccer", "volleyball", "bowling", "track", "gymnastics", "swimming", "combat_sport"], # STRICT MODERN/SPORT BLOCK
            min_characters=2,
            max_characters=4,
            force_interaction=True,
            role_slots=["Adventurer", "Spellcaster"],
            roles=[
                Role(
                    name="Adventurer",
                    required_tags=["armor", "leather", "rugged", "weapon_combat", "medieval"],
                    blocked_tags=["modern", "office", "tech", "jeans", "sneakers"],
                    preferred_poses=["Action", "Combat", "Standing", "Heroic"],
                    allowed_outfit_categories=["Fantasy & Sci-Fi", "History & Culture", "Combat & Tactical"],
                    allowed_pose_categories=["Action & Motion", "Combat & Tactical", "Fantasy & Sci-Fi"]
                ),
                Role(
                    name="Spellcaster",
                    required_tags=["robe", "silk", "mystical", "jewelry", "medieval"],
                    blocked_tags=["heavy armor", "modern", "sport", "jeans"],
                    preferred_poses=["Mystical", "Casting", "Regal"],
                    allowed_outfit_categories=["Fantasy & Sci-Fi", "History & Culture", "Intimate & Sensual"],
                    allowed_pose_categories=["Casual & Daily Life", "Arts & Performance", "Fantasy & Sci-Fi"]
                )
            ],
            default_style_tags=["Classic Fantasy Oil", "High Fantasy", "Digital Painting"],
            weight=1.0
        ))

        # =====================================================================
        # RIGID BRANCH 3: MODERN SLICE-OF-LIFE (The "Casual" Branch)
        # =====================================================================
        self.register(Scenario(
            name="City Living",
            vibe_tags=["modern", "casual", "urban", "relaxed", "daily", "soft"],
            allowed_scene_categories=["Domestic & Home", "Indoor Social Spaces", "Nightlife & Bars", "Nature & Outdoors", "Street"],
            blocked_global_tags=["fantasy", "medieval", "armor", "weapon", "weapon_combat", "combat_tactical", "combat_sport", "basketball", "football", "mma", "boxing", "baseball", "softball", "tennis", "soccer", "volleyball", "bowling", "track", "gymnastics", "swimming"], # STRICT FANTASY/COMBAT/SPORT BLOCK
            min_characters=1,
            max_characters=3,
            roles=[
                Role(
                    name="Resident",
                    required_tags=["casual", "modern", "comfortable", "daily"],
                    blocked_tags=["armor", "combat_tactical", "weapon_combat", "fantasy", "uniform"],
                    preferred_poses=["Relaxed", "Sitting", "Standing", "Walking"],
                    allowed_outfit_categories=["Casual & Everyday", "Formal & Fashion", "Intimate & Sensual"],
                    allowed_pose_categories=["Casual & Daily Life", "Intimate & Sensual", "Thematic & Cinematic"]
                )
            ],
            default_style_tags=["Soft Semi-Realistic", "Standard / Neutral", "Ligne Claire"],
            weight=1.2
        ))

        # =====================================================================
        # RIGID BRANCH 4: HIGH SOCIETY (The "Luxe" Branch)
        # =====================================================================
        self.register(Scenario(
            name="Gala Event",
            vibe_tags=["formal", "luxury", "glamour", "elegant", "high-fashion", "wealth"],
            allowed_scene_categories=["Indoor Social Spaces", "Gala", "Museum", "Ballroom", "Luxury", "Arts & Performance"],
            blocked_global_tags=["casual", "ragged", "dirty", "tactical", "armor", "basketball", "football", "mma", "boxing", "baseball", "softball", "tennis", "soccer", "volleyball", "bowling", "track", "gymnastics", "swimming", "combat_sport"],
            min_characters=2,
            max_characters=3,
            force_interaction=True,
            roles=[
                Role(
                    name="VIP",
                    required_tags=["formal", "evening", "gown", "tuxedo", "elegant", "luxury"],
                    blocked_tags=["casual", "sport", "pajamas", "distressed", "armor"],
                    preferred_poses=["Glamour", "Regal", "Confident", "Standing", "Social"],
                    allowed_outfit_categories=["Formal & Fashion", "History & Culture"],
                    allowed_pose_categories=["Casual & Daily Life", "Fashion & Glamour", "Arts & Performance"]
                )
            ],
            default_style_tags=["High Fashion", "Cinematic", "Artgerm Style"],
            weight=0.8
        ))

        # =====================================================================
        # RIGID BRANCH 5: TACTICAL OPERATIONS (The "Combat" Branch)
        # =====================================================================
        self.register(Scenario(
            name="Tactical Mission",
            vibe_tags=["combat_tactical", "military", "action", "combat", "intense", "gritty"],
            allowed_scene_categories=["Tactical & Military", "Urban", "Industrial", "Ruins", "Cyberpunk & Futuristic", "Nature & Outdoors"],
            blocked_global_tags=["formal", "gown", "dress", "pajamas", "fantasy", "magic", "basketball", "football", "mma", "boxing", "baseball", "softball", "tennis", "soccer", "volleyball", "bowling", "track", "gymnastics", "swimming"],
            min_characters=2,
            max_characters=4,
            force_interaction=True,
            role_slots=["Commander", "Soldier"],
            roles=[
                Role(
                    name="Commander",
                    required_tags=["combat_tactical", "military", "uniform", "tech"],
                    blocked_tags=["messy", "casual", "civilian"],
                    preferred_poses=["Standing", "Pointing", "Commanding"],
                    allowed_outfit_categories=["Combat & Tactical", "Cyberpunk & Sci-Fi"],
                    allowed_pose_categories=["Combat & Tactical", "Action & Motion"]
                ),
                Role(
                    name="Soldier",
                    required_tags=["combat_tactical", "vest", "utility"],
                    blocked_tags=["formal", "civilian", "bright"],
                    preferred_poses=["Action", "Aiming", "Crouching", "Cover"],
                    allowed_outfit_categories=["Combat & Tactical", "Rugged & Outdoor"],
                    allowed_pose_categories=["Combat & Tactical", "Action & Motion"]
                )
            ],
            default_style_tags=["Action Movie", "Gritty Realism", "Concept Art"],
            weight=0.8
        ))

        # =====================================================================
        # RIGID BRANCH 6: HISTORICAL & PERIOD (The "Time Travel" Branch)
        # =====================================================================
        self.register(Scenario(
            name="Period Piece",
            vibe_tags=["vintage", "historical", "retro", "cultural", "classic"],
            allowed_scene_categories=["History & Culture", "Indoor Social Spaces", "Library", "Street", "Nightlife & Bars"],
            blocked_global_tags=["modern", "tech", "neon", "cyberpunk", "combat_tactical", "combat_sport", "basketball", "football", "mma", "boxing", "baseball", "softball", "tennis", "soccer", "volleyball", "bowling", "track", "gymnastics", "swimming"], # STRICT MODERN/SPORT BLOCK
            min_characters=1,
            max_characters=3,
            roles=[
                Role(
                    name="Classic Figure",
                    required_tags=["vintage", "retro", "historical", "classic"],
                    blocked_tags=["modern", "print", "graphic", "neon"],
                    preferred_poses=["Standing", "Sitting", "Elegant"],
                    allowed_outfit_categories=["History & Culture", "Formal & Fashion", "Casual & Everyday"],
                    allowed_pose_categories=["History & Culture", "Casual & Daily Life", "Arts & Performance"]
                )
            ],
            default_style_tags=["Vintage Film", "Sepia", "Oil Painting"],
            weight=0.8
        ))

        # =====================================================================
        # RIGID BRANCH 7: INTIMATE & BOUDOIR (The "Private" Branch)
        # =====================================================================
        self.register(Scenario(
            name="Private Moments",
            vibe_tags=["intimate", "sensual", "boudoir", "soft", "romance"],
            allowed_scene_categories=["Bedroom", "Domestic & Home", "Luxury", "Indoors"],
            blocked_global_tags=["armor", "tactical", "weapon", "dirty", "crowd", "basketball", "football", "mma", "boxing", "baseball", "softball", "tennis", "soccer", "volleyball", "bowling", "track", "gymnastics", "swimming", "combat_sport"],
            min_characters=1,
            max_characters=2,
            roles=[
                Role(
                    name="Subject",
                    required_tags=["intimate", "sensual", "lingerie", "soft"],
                    blocked_tags=["armor", "heavy", "outerwear"],
                    preferred_poses=["Lying", "Sitting", "Stretching", "Intimate"],
                    allowed_outfit_categories=["Intimate & Sensual", "Casual & Daily Life"],
                    allowed_pose_categories=["Intimate & Sensual", "Fashion & Glamour", "Casual & Daily Life"]
                )
            ],
            default_style_tags=["Soft Focus", "Cinematic Romance", "Warm Lighting"],
            weight=0.6
        ))
        # 10. BARBERSHOP QUARTET
        self.register(Scenario(
            name="Barbershop Performance",
            vibe_tags=["vintage", "music", "performance", "barbershop", "quartet"],
            allowed_scene_categories=["Theatre", "Stage", "Music Hall", "History & Culture", "Arts & Performance"],
            min_characters=4,
            max_characters=4,
            force_interaction=True,
            role_slots=["Lead", "Tenor", "Baritone", "Bass"],
            roles=[
                Role(
                    name="Lead",
                    required_tags=["vintage", "costume", "performer"],
                    allowed_outfit_categories=["History & Culture", "Character  Costume"],
                    allowed_pose_categories=["Arts & Performance", "History & Culture"]
                ),
                Role(
                    name="Tenor",
                    required_tags=["vintage", "costume", "performer"],
                    allowed_outfit_categories=["History & Culture", "Character  Costume"],
                    allowed_pose_categories=["Arts & Performance", "History & Culture"]
                ),
                Role(
                    name="Baritone",
                    required_tags=["vintage", "costume", "performer"],
                    allowed_outfit_categories=["History & Culture", "Character  Costume"],
                    allowed_pose_categories=["Arts & Performance", "History & Culture"]
                ),
                Role(
                    name="Bass",
                    required_tags=["vintage", "costume", "performer"],
                    allowed_outfit_categories=["History & Culture", "Character  Costume"],
                    allowed_pose_categories=["Arts & Performance", "History & Culture"]
                )
            ],
            default_style_tags=["Vintage Photography", "High Detail"],
            blocked_global_tags=["modern", "tech", "combat_tactical", "basketball", "football", "mma", "boxing", "baseball", "softball", "tennis", "soccer", "volleyball", "bowling", "track", "gymnastics", "swimming", "combat_sport"]
        ))

        # =====================================================================
        # ATHLETIC COMPETITION (Consolidated Sports)
        # =====================================================================
        # Replaces: Football, Basketball, Baseball, Softball, Tennis, Volleyball,
        # Bowling, Track, MMA, Boxing, Soccer, Gymnastics, Swimming (13 scenarios)
        
        self.register(Scenario(
            name="Athletic Competition",
            vibe_tags=["athletic", "competitive", "sport", "dynamic", "active"],
            allowed_scene_categories=["Sports & Athletics"],
            blocked_global_tags=[
                "fantasy", "medieval", "magic", "formal", "elegant", 
                "vintage", "historical", "esports", "sci-fi", "cyberpunk",
                "survival", "post-apocalyptic"
            ],
            min_characters=1,
            max_characters=4,
            force_interaction=False,  # Sport-dependent (team vs individual)
            roles=[
                Role(
                    name="Athlete",
                    required_tags=["athletic"],
                    blocked_tags=["formal", "business", "fantasy", "armor", "vintage", "elegant"],
                    allowed_outfit_categories=["Athletic & Sports"],
                    allowed_pose_categories=["Action & Motion", "Athletics & Sports"]
                )
            ],
            default_style_tags=["Sports Action", "High Detail", "Dynamic"],
            weight=0.5  # Combined weight for all sports (was 0.3 × 13 = 3.9)
        ))

