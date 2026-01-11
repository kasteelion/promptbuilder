import pathlib
import sys
import tkinter as tk

# Ensure repo root is on sys.path for imports when running scripts directly
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tkinter import ttk

from logic.data_loader import DataLoader
from ui.characters_tab import CharactersTab
from ui.themes.theme_manager import ThemeManager
from ui.controllers.character_controller import CharacterController

root = tk.Tk()
root.withdraw()
notebook = ttk.Notebook(root)
style = ttk.Style(root)
tm = ThemeManager(root, style)

class MockApp:
    def __init__(self, root, dl, ct_tab=None):
        self.root = root
        self.ctx = type('obj', (object,), {'characters': {}, 'base_prompts': {}, 'poses': {}, 'color_schemes': {}, 'modifiers': {}, 'data_loader': dl})
        self.data_loader = dl
        self.characters_tab = ct_tab
    def reload_data(self): print("Mock reload")

dl = DataLoader()
app = MockApp(root, dl)
cc = CharacterController(app)

chars = dl.load_characters()
base = dl.load_base_prompts()
poses = dl.load_presets("poses.md")

ct = CharactersTab(
    notebook,
    dl,
    tm,
    cc,
    lambda: print("on_change called"),
    lambda: print("reload called"),
    lambda: print("save undo"),
)
app.characters_tab = ct
ct.load_data(chars, base, poses)

# Choose two characters from loaded chars
names = list(chars.keys())[:2]
print("Using characters:", names)
ct.selected_characters = [
    {"name": names[0], "outfit": "", "pose_category": "", "pose_preset": "", "action_note": ""},
    {"name": names[1], "outfit": "", "pose_category": "", "pose_preset": "", "action_note": ""},
]
ct._refresh_list()

# Choose a shared outfit name from bulk_outfit_combo values
vals = ct.bulk_outfit_combo.all_values
print("Bulk outfits count:", len(vals))
if vals:
    ct.bulk_outfit_var.set(vals[0])
    print("Applying outfit", vals[0])
    ct._apply_bulk_to_all()
    print("After apply:", ct.selected_characters)
else:
    print("No outfits available")

root.destroy()
