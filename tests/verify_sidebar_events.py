
import flet as ft
import sys
import os

# Create mock context
class MockContext:
    def __init__(self):
        self.scenes = {"Fantasy": {"Forest": "Tree"}}
        self.interactions = {"Action": {"Run": "Fast"}}
        self.base_prompts = {"Style1": "Prompt"}

class MockState:
    def __init__(self):
        self.ctx = MockContext()
        self.state = {}

class MockApp:
    def __init__(self):
        self.state = MockState()
    
    def update_preview(self): 
        print("DEBUG_MOCK: update_preview called")
    
    def handle_randomize(self, e): pass
    def show_dashboard(self): pass

# Import Sidebar
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui.sections.sidebar import SidebarSection

def main(page: ft.Page):
    print("Starting Sidebar Event Test...")
    try:
        app = MockApp()
        sidebar = SidebarSection(app)
        sidebar.populate_data()
        
        page.add(sidebar)
        page.update()
        
        # Verify initial state
        print(f"Initial Scene Cat Options: {[o.key for o in sidebar.scene_cat_dd.options]}")
        
        # We can't simulate a click event easily without UI automation, 
        # but we can verify the handler IS attached.
        print(f"Handler attached to Scene Cat: {sidebar.scene_cat_dd.on_change}")
        
        # Verify correct method reference
        if sidebar.scene_cat_dd.on_change == sidebar.handle_scene_cat_change:
            print("Binding Check: PASSED")
        else:
            print("Binding Check: FAILED")
            
        # Simulate the event call manually to ensure logic works
        class MockEvent:
            def __init__(self, val):
                self.control = type("obj", (object,), {"value": val})
                
        print("Simulating Event Click -> 'Fantasy'")
        sidebar.handle_scene_cat_change(MockEvent("Fantasy"))
        
        print("TEST COMPLETE")
        # page.window_close()
        sys.exit(0)
    except Exception as e:
        import traceback
        with open("test_sidebar_error.log", "w") as f:
            f.write(traceback.format_exc())
            f.write(str(e))
        print("TEST FAILED")
        sys.exit(1)

if __name__ == "__main__":
    ft.app(target=main)
