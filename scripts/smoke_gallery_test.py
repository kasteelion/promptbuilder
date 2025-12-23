import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import tkinter as tk

from logic.data_loader import DataLoader
from ui.character_card import CharacterGalleryPanel
from utils.preferences import PreferencesManager

root = tk.Tk()
root.withdraw()

loader = DataLoader()
prefs = PreferencesManager()
chars = loader.load_characters()
panel = CharacterGalleryPanel(root, loader, prefs, lambda name: print("add", name))
panel.pack()
panel.load_characters(chars)
print("Loaded gallery with", len(chars), "characters")
root.destroy()
