import sys
import os
import traceback
from unittest.mock import MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from ui.sections.roster import RosterSection
    
    class MockApp:
        def __init__(self):
            self.state = MagicMock()
            self.state.state = {
                "selected_characters": [
                    {
                        "name": "Sarah", 
                        "_expanded": True, 
                        "outfit_category": "Casual", 
                        "outfit": "Jeans",
                        "character_traits": [],
                        "outfit_traits": []
                    }
                ]
            }
            self.state.ctx = MagicMock()
            self.state.ctx.characters = {
                "Sarah": {
                    "traits": {"Happy": {}},
                    "outfits_categorized": {"Casual": {"Jeans": {"modifiers": {"Ripped": {}}}}},
                    "signature_color": "blue"
                }
            }
            self.state.get_character_summary.return_value = "Summary"

    print("Import successful. Instantiating...")
    app = MockApp()
    r = RosterSection(app)
    print("Instantiation successful.")
    
    print("Calling refresh()...")
    r.refresh()
    print("Refresh successful.")
    
except Exception:
    traceback.print_exc()
