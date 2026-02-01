
import flet as ft
import sys
import os

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.sections.roster import RosterSection

class MockContext:
    def __init__(self):
        self.characters = {
            "TestChar": {
                 "outfits_categorized": {
                     "Cat1": {
                         "Outfit1": {"modifiers": {"Variant1": "desc"}}
                     }
                 },
                 "traits": {"Trait1": True},
                 "signature_color": "red"
            }
        }
        self.poses = {"PoseCat1": {"Pose1": {}}}

class MockState:
    def __init__(self):
        self.ctx = MockContext()
        self.state = {
            "selected_characters": [
                {
                    "name": "TestChar",
                    "outfit": "Outfit1",
                    "outfit_category": "Cat1", 
                    "_expanded": True
                }
            ]
        }
    def get_character_summary(self, idx):
        return "SUMMARY"

class MockApp:
    def __init__(self):
        self.state = MockState()
    
    def update_preview(self): pass
    def remove_character(self, name): pass

def main(page: ft.Page):
    print("Starting Roster Test...")
    try:
        app = MockApp()
        roster = RosterSection(app)
        page.add(roster)
        
        # Test Refresh
        roster.refresh()
        print("Roster Refresh: OK")
        
        # Test Toggle (Simulate handler logic manually or strictly calling it)
        # We can't easily simulate the click event object without a real interaction, 
        # but we can verify the method references exist.
        
        print("TEST COMPLETE: No Crash")
        # page.window_close() # Unavailable in some versions
        sys.exit(0)
    except Exception as e:
        import traceback
        with open("test_error.log", "w") as f:
            f.write(traceback.format_exc())
        print("TEST FAILED")
        sys.exit(1)

if __name__ == "__main__":
    ft.app(target=main)
