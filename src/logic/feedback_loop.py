import json
import os
import threading
from typing import List, Dict, Any
from utils.logger import logger


class FeedbackLoop:
    """Manages the persistent 'lessons learned' for the AI pipeline.
    
    Uses a singleton pattern to avoid redundant disk I/O when multiple
    components (ScoringEngine, AutomationController, llm_export) access
    the same feedback data within a single session.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, file_path: str = None):
        with cls._lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                instance._initialized = False
                cls._instance = instance
            return cls._instance

    def __init__(self, file_path: str = None):
        if self._initialized:
            return

        if file_path is None:
            # Check assets/data/config first, fallback to module directory
            base_data_path = os.path.join(os.getcwd(), "assets", "data", "config", "lessons_learned.json")
            if os.path.exists(base_data_path):
                file_path = base_data_path
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                fallback_path = os.path.join(base_dir, "lessons_learned.json")
                file_path = base_data_path if not os.path.exists(fallback_path) else fallback_path

        self.file_path = file_path
        self.data = self._load()
        # Cache low-quality names to avoid recomputing on every call
        self._low_quality_cache = None
        self._initialized = True

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load lessons_learned.json: {e}")

        return {
            "clashes": [],
            "hall_of_fame": [],
            "low_quality_assets": []
        }

    def save(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
            self._low_quality_cache = None  # Invalidate cache on write
        except Exception as e:
            logger.error(f"Failed to save lessons_learned.json: {e}")

    def record_clash(self, reasoning: str, tags: List[str]):
        """Record a thematic clash identified by the Critic."""
        entry = {
            "reasoning": reasoning,
            "tags": sorted(list(set(t.lower() for t in tags))),
            "timestamp": None
        }

        # Avoid exact duplicates
        if entry not in self.data["clashes"]:
            self.data["clashes"].append(entry)
            # Cap at 100 entries for performance
            if len(self.data["clashes"]) > 100:
                self.data["clashes"].pop(0)
            self.save()

    def record_success(self, prompt: str, score: float, tags: List[str]):
        """Record a high-scoring prompt for few-shot learning."""
        entry = {
            "prompt": prompt,
            "score": score,
            "tags": sorted(list(set(t.lower() for t in tags)))
        }

        # Avoid duplicates
        if not any(e["prompt"] == prompt for e in self.data["hall_of_fame"]):
            self.data["hall_of_fame"].append(entry)
            # Sort by score and keep top 20
            self.data["hall_of_fame"].sort(key=lambda x: x["score"], reverse=True)
            self.data["hall_of_fame"] = self.data["hall_of_fame"][:20]
            self.save()

    def flag_low_quality(self, asset_name: str, reason: str):
        """Flag an asset (Outfit, Character, etc.) as low quality."""
        entry = {"name": asset_name, "reason": reason}
        if not any(e["name"] == asset_name for e in self.data["low_quality_assets"]):
            self.data["low_quality_assets"].append(entry)
            self.save()

    def get_hall_of_fame(self, limit: int = 3) -> List[str]:
        """Return top prompts for few-shot injection."""
        return [e["prompt"] for e in self.data["hall_of_fame"][:limit]]

    def is_clashing(self, active_tags: set) -> bool:
        """Check if current tags match a known clash pattern."""
        active_lower = {t.lower() for t in active_tags}
        for clash in self.data["clashes"]:
            clash_tags = set(clash["tags"])
            if clash_tags and clash_tags.issubset(active_lower):
                return True
        return False

    def get_low_quality_names(self) -> List[str]:
        """Return list of asset names to filter out (cached)."""
        if self._low_quality_cache is None:
            self._low_quality_cache = [e["name"] for e in self.data["low_quality_assets"]]
        return self._low_quality_cache
