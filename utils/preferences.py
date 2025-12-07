# -*- coding: utf-8 -*-
"""User preferences manager with persistent storage."""

import json
from pathlib import Path


class PreferencesManager:
    """Manages user preferences with file-based persistence."""
    
    def __init__(self, prefs_file="preferences.json"):
        """Initialize preferences manager.
        
        Args:
            prefs_file: Filename for preferences storage
        """
        self.prefs_file = Path(prefs_file)
        self.prefs = self._load_preferences()
    
    def _load_preferences(self):
        """Load preferences from file.
        
        Returns:
            Dictionary of preferences
        """
        default_prefs = {
            "window_geometry": None,
            "last_theme": "Light",
            "last_base_prompt": None,
            "font_adjustment": 0,
            "recent_characters": [],
            "favorite_characters": [],
            "favorite_outfits": [],
            "recent_presets": [],
            "show_welcome": True,
            "sash_position": None,
            "auto_theme": False
        }
        
        if not self.prefs_file.exists():
            return default_prefs
        
        try:
            with open(self.prefs_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                # Merge with defaults to handle new keys
                default_prefs.update(loaded)
                return default_prefs
        except Exception as e:
            print(f"Error loading preferences: {e}")
            return default_prefs
    
    def save_preferences(self):
        """Save preferences to file."""
        try:
            with open(self.prefs_file, 'w', encoding='utf-8') as f:
                json.dump(self.prefs, f, indent=2)
        except Exception as e:
            print(f"Error saving preferences: {e}")
    
    def get(self, key, default=None):
        """Get preference value.
        
        Args:
            key: Preference key
            default: Default value if key not found
            
        Returns:
            Preference value
        """
        return self.prefs.get(key, default)
    
    def set(self, key, value):
        """Set preference value and save.
        
        Args:
            key: Preference key
            value: Value to set
        """
        self.prefs[key] = value
        self.save_preferences()
    
    def add_recent(self, list_key, item, max_items=10):
        """Add item to recent list.
        
        Args:
            list_key: Key for the recent list
            item: Item to add
            max_items: Maximum number of items to keep
        """
        recent = self.prefs.get(list_key, [])
        # Remove if already exists
        if item in recent:
            recent.remove(item)
        # Add to front
        recent.insert(0, item)
        # Trim to max
        recent = recent[:max_items]
        self.prefs[list_key] = recent
        self.save_preferences()
    
    def toggle_favorite(self, list_key, item):
        """Toggle item in favorites list.
        
        Args:
            list_key: Key for the favorites list
            item: Item to toggle
            
        Returns:
            True if item is now favorited, False otherwise
        """
        favorites = self.prefs.get(list_key, [])
        if item in favorites:
            favorites.remove(item)
            is_favorited = False
        else:
            favorites.append(item)
            is_favorited = True
        self.prefs[list_key] = sorted(favorites)
        self.save_preferences()
        return is_favorited
    
    def is_favorite(self, list_key, item):
        """Check if item is in favorites.
        
        Args:
            list_key: Key for the favorites list
            item: Item to check
            
        Returns:
            True if favorited
        """
        return item in self.prefs.get(list_key, [])
