
import sys
import os

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "src"))

modules = [
    "ui.components.character_card",
    "ui.components.icon_button",
    "ui.sections.toolbar",
    "ui.sections.gallery",
    "ui.sections.roster",
    "ui.sections.sidebar",
    "ui.sections.console",
    "ui.sections.dashboard",
    "logic.data_loader",
    "logic.randomizer",
    "logic.automation_controller",
    "core.builder"
]

for m in modules:
    try:
        __import__(m)
        print(f"PASS: {m}")
    except Exception as e:
        print(f"FAIL: {m} -> {e}")
