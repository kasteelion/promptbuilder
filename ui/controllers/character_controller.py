# -*- coding: utf-8 -*-
"""Controller for character-related business logic."""

import shutil
from tkinter import messagebox
from typing import List

from utils import logger


class CharacterController:
    """Handles character operations, file updates, and coordination."""

    def __init__(self, app):
        """Initialize CharacterController.

        Args:
            app: PromptBuilderApp instance
        """
        self.app = app
        self.ctx = app.ctx
        self.data_loader = app.ctx.data_loader

    def add_character(self, name: str, selected_list: List[dict]) -> bool:
        """Add a character to the selected list with validation and defaults.

        Returns:
            bool: True if character was added, False otherwise.
        """
        if not name:
            return False

        # Ensure modifier/gender is present
        if not self._ensure_character_validity(name):
            return False

        # Check for duplicates in current selection
        if any(c["name"] == name for c in selected_list):
            from utils.notification import notify
            notify(self.app.root, "Already Added", f"{name} is already in the prompt", level="info")
            return False

        # Determine default outfit
        char_def = self.ctx.characters.get(name, {})
        outfits = char_def.get("outfits", {})
        outfit = "Base" if "Base" in outfits else (sorted(list(outfits.keys()))[0] if outfits else "")

        # Add to list
        selected_list.append({
            "name": name,
            "outfit": outfit,
            "pose_category": "",
            "pose_preset": "",
            "action_note": "",
        })
        return True

    def duplicate_character(self, idx: int, selected_list: List[dict]):
        """Duplicate a character at the given index."""
        if 0 <= idx < len(selected_list):
            import copy
            char = copy.deepcopy(selected_list[idx])
            selected_list.insert(idx + 1, char)

    def remove_character(self, idx: int, selected_list: List[dict]) -> bool:
        """Remove a character after confirmation."""
        if not (0 <= idx < len(selected_list)):
            return False
            
        char_name = selected_list[idx].get("name", "this character")
        if messagebox.askyesno("Remove Character", f"Remove {char_name} from the prompt?"):
            selected_list.pop(idx)
            return True
        return False

    def _ensure_character_validity(self, name: str) -> bool:
        """Ensure character has required metadata, prompt user if missing."""
        char_def = self.ctx.characters.get(name, {})
        if char_def and (char_def.get("modifier") or char_def.get("gender_explicit")):
            return True

        # Metadata missing, prompt user
        choice = self.app.characters_tab._prompt_modifier_choice(name)
        if not choice:
            return False

        if choice == "editor":
            from ui.character_creator import CharacterCreatorDialog
            dialog = CharacterCreatorDialog(self.app.root, self.data_loader, self.app.reload_data, edit_character=name)
            dialog.show()
            self.app.reload_data()
            return self._ensure_character_validity(name) # Re-check after edit
        else:
            # Inline update
            return self._update_character_modifier_file(name, choice)

    def _update_character_modifier_file(self, name: str, choice: str) -> bool:
        """Update the character's markdown file with the chosen modifier."""
        fp = self.app.characters_tab._find_character_file(name)
        if not fp:
            return False

        try:
            # Backup
            bak = fp.with_suffix(fp.suffix + ".bak")
            shutil.copy(fp, bak)

            text = fp.read_text(encoding="utf-8")
            lines = text.splitlines()
            
            # Find insertion point
            insert_idx = 0
            for i, line in enumerate(lines[:20]):
                if line.strip().lower().startswith("**photo:"):
                    insert_idx = i + 1
                    break
            
            # Replace or insert
            new_lines = []
            replaced = False
            for line in lines:
                if line.strip().startswith("**Gender:**"):
                    new_lines.append(f"**Modifier:** {choice}")
                    replaced = True
                else:
                    new_lines.append(line)
            
            if not replaced:
                new_lines = lines[:insert_idx] + ["", f"**Modifier:** {choice}"] + lines[insert_idx:]
                
            fp.write_text("\n".join(new_lines), encoding="utf-8")
            self.app.reload_data()
            return True
        except Exception:
            logger.exception(f"Failed to update modifier for {name}")
            return False
