# -*- coding: utf-8 -*-
"""Preset manager for saving/loading prompt configurations."""

import json
from pathlib import Path
from datetime import datetime


class PresetManager:
    """Manages preset configurations for prompts."""
    
    def __init__(self, presets_dir="presets"):
        """Initialize preset manager.
        
        Args:
            presets_dir: Directory for storing presets
        """
        self.presets_dir = Path(presets_dir)
        self.presets_dir.mkdir(exist_ok=True)
    
    def save_preset(self, name, config):
        """Save a preset configuration.
        
        Args:
            name: Preset name
            config: Configuration dictionary containing:
                - selected_characters: List of character dicts
                - base_prompt: Base prompt name
                - scene: Scene text
                - notes: Notes text
        
        Returns:
            Path to saved preset file
        """
        preset_data = {
            "name": name,
            "created": datetime.now().isoformat(),
            "config": config
        }
        
        # Sanitize filename
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        filename = f"{safe_name}.json"
        filepath = self.presets_dir / filename
        
        # Handle duplicate names
        counter = 1
        while filepath.exists():
            filename = f"{safe_name}_{counter}.json"
            filepath = self.presets_dir / filename
            counter += 1
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(preset_data, f, indent=2)
        
        return filepath
    
    def load_preset(self, filename):
        """Load a preset configuration.
        
        Args:
            filename: Preset filename
            
        Returns:
            Configuration dictionary or None if error
        """
        filepath = self.presets_dir / filename
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                preset_data = json.load(f)
                return preset_data.get("config")
        except Exception as e:
            print(f"Error loading preset: {e}")
            return None
    
    def get_presets(self):
        """Get list of available presets.
        
        Returns:
            List of tuples (filename, name, created_date)
        """
        presets = []
        for filepath in self.presets_dir.glob("*.json"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    presets.append((
                        filepath.name,
                        data.get("name", filepath.stem),
                        data.get("created", "Unknown")
                    ))
            except Exception:
                continue
        
        # Sort by created date (newest first)
        presets.sort(key=lambda x: x[2], reverse=True)
        return presets
    
    def delete_preset(self, filename):
        """Delete a preset.
        
        Args:
            filename: Preset filename
            
        Returns:
            True if deleted successfully
        """
        filepath = self.presets_dir / filename
        try:
            filepath.unlink()
            return True
        except Exception as e:
            print(f"Error deleting preset: {e}")
            return False
    
    def export_preset(self, filename, export_path):
        """Export preset to a different location.
        
        Args:
            filename: Preset filename
            export_path: Path to export to
            
        Returns:
            True if exported successfully
        """
        filepath = self.presets_dir / filename
        try:
            import shutil
            shutil.copy(filepath, export_path)
            return True
        except Exception as e:
            print(f"Error exporting preset: {e}")
            return False
    
    def import_preset(self, import_path):
        """Import preset from external file.
        
        Args:
            import_path: Path to preset file
            
        Returns:
            Imported preset filename or None
        """
        try:
            import shutil
            dest = self.presets_dir / Path(import_path).name
            
            # Handle duplicate names
            if dest.exists():
                stem = dest.stem
                counter = 1
                while dest.exists():
                    dest = self.presets_dir / f"{stem}_{counter}.json"
                    counter += 1
            
            shutil.copy(import_path, dest)
            return dest.name
        except Exception as e:
            print(f"Error importing preset: {e}")
            return None
