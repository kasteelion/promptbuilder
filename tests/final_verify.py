import sys
import os
import traceback
from unittest.mock import MagicMock, patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    
    # Patch Control.update globally
    patcher = patch('flet.Control.update')
    mock_update = patcher.start()
    
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
                    },
                    {"name": "Mike", "_expanded": False}
                ]
            }
            self.state.ctx = MagicMock()
            # Mock valid context data
            self.state.ctx.characters = {
                "Sarah": {
                    "traits": {"Happy": {}, "Sad": {}},
                    "outfits_categorized": {
                        "Casual": {"Jeans": {"modifiers": {"Ripped": {}}}, "T-Shirt": {}}
                    },
                    "signature_color": "blue"
                },
                "Mike": {}
            }
            self.state.ctx.poses = {"Standing": {"Default": {}}}
            
            # Method mocks
            self.remove_character = MagicMock()
            self.clear_all_characters = MagicMock()
            self.handle_solo_randomize = MagicMock()
            self.update_preview = MagicMock()
            self.show_toast = MagicMock()
            
            # State helper mocks
            self.state.get_character_summary.return_value = "Summary"
            self.state.move_character = MagicMock()

    print("--- STARTING VERIFICATION ---")
    app = MockApp()
    roster = RosterSection(app)
    
    print("1. Refresh...")
    roster.refresh()
    if len(roster.controls) != 2:
        raise Exception(f"Refresh failed: Expected 2 controls, got {len(roster.controls)}")
    print("   Refresh OK.")

    print("2. Accordion Toggle...")
    roster.handle_toggle_accordion(0)
    if app.state.state["selected_characters"][0]["_expanded"]:
         raise Exception("Accordion toggle failed (still True)")
    print("   Accordion Toggle OK.")

    print("3. Move Character...")
    roster.handle_move(0, 1)
    app.state.move_character.assert_called_with(0, 1)
    print("   Move Character OK.")

    print("4. Bulk Apply...")
    roster.bulk_cat_dd.value = "Casual"
    roster.bulk_outfit_dd.value = "T-Shirt"
    roster.bulk_sig_toggle.value = True
    roster.handle_bulk_apply(None)
    
    char0 = app.state.state["selected_characters"][0]
    if char0["outfit"] != "T-Shirt":
         raise Exception(f"Bulk Apply Outfit failed: {char0['outfit']}")
    if not char0["use_signature_color"]:
         raise Exception("Bulk Apply Sig Color failed")
    print("   Bulk Apply OK.")
    
    print("\n--- ALL TESTS PASSED SUCCESSFULLY ---\n")
    
except Exception:
    traceback.print_exc()
finally:
    patcher.stop()
