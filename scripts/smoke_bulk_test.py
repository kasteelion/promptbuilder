import sys
import pathlib
import tkinter as tk

# Ensure repo root is on sys.path for imports when running scripts directly
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from logic.data_loader import DataLoader
from ui.characters_tab import CharactersTab
from tkinter import ttk

root = tk.Tk()
root.withdraw()
notebook = ttk.Notebook(root)

dl = DataLoader()
chars = dl.load_characters()
base = dl.load_base_prompts()
poses = dl.load_presets('poses.md')

ct = CharactersTab(notebook, dl, lambda: print('on_change called'), lambda: print('reload called'), lambda: print('save undo'))
ct.load_data(chars, base, poses)

# Choose two characters from loaded chars
names = list(chars.keys())[:2]
print('Using characters:', names)
ct.selected_characters = [{'name': names[0], 'outfit':'', 'pose_category':'', 'pose_preset':'','action_note':''},{'name':names[1],'outfit':'','pose_category':'','pose_preset':'','action_note':''}]
ct._refresh_list()

# Choose a shared outfit name from bulk_outfit_combo values
vals = ct.bulk_outfit_combo['values']
print('Bulk outfits count:', len(vals))
if vals:
    ct.bulk_outfit_var.set(vals[0])
    print('Applying outfit', vals[0])
    ct._apply_bulk_to_all()
    print('After apply:', ct.selected_characters)
else:
    print('No outfits available')

root.destroy()
