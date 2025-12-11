# -*- coding: utf-8 -*-
"""Quick test script to verify new features are working."""

import sys
import os

def test_imports():
    """Test that all new modules can be imported."""
    print("Testing imports...")
    try:
        from utils import UndoManager, PreferencesManager, PresetManager, create_tooltip
        print("✅ Utils imports successful")
        
        from ui.searchable_combobox import SearchableCombobox
        print("✅ SearchableCombobox import successful")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_undo_manager():
    """Test undo manager functionality."""
    print("\nTesting UndoManager...")
    try:
        from utils import UndoManager
        
        manager = UndoManager()
        
        # Test save state
        state1 = {"test": "value1"}
        manager.save_state(state1)
        
        state2 = {"test": "value2"}
        manager.save_state(state2)
        
        # Test undo
        assert manager.can_undo()
        undone = manager.undo()
        assert undone["test"] == "value1"
        
        # Test redo
        assert manager.can_redo()
        redone = manager.redo()
        assert redone["test"] == "value2"
        
        print("✅ UndoManager working correctly")
        return True
    except Exception as e:
        print(f"❌ UndoManager test failed: {e}")
        return False

def test_preferences_manager():
    """Test preferences manager."""
    print("\nTesting PreferencesManager...")
    try:
        from utils import PreferencesManager
        
        # Use test file
        prefs = PreferencesManager("test_prefs.json")
        
        # Test set/get
        prefs.set("test_key", "test_value")
        assert prefs.get("test_key") == "test_value"
        
        # Test recent items
        prefs.add_recent("recent_test", "item1")
        prefs.add_recent("recent_test", "item2")
        recent = prefs.get("recent_test")
        assert recent[0] == "item2"
        
        # Test favorites
        is_fav = prefs.toggle_favorite("fav_test", "item1")
        assert is_fav == True
        assert prefs.is_favorite("fav_test", "item1")
        
        # Cleanup
        import os
        if os.path.exists("test_prefs.json"):
            os.remove("test_prefs.json")
        
        print("✅ PreferencesManager working correctly")
        return True
    except Exception as e:
        print(f"❌ PreferencesManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_preset_manager():
    """Test preset manager."""
    print("\nTesting PresetManager...")
    try:
        from utils import PresetManager
        import shutil
        
        # Use test directory
        test_dir = "test_presets"
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
        
        manager = PresetManager(test_dir)
        
        # Test save
        config = {
            "selected_characters": [{"name": "Test"}],
            "base_prompt": "Test Style"
        }
        filepath = manager.save_preset("Test Preset", config)
        assert filepath.exists()
        
        # Test load
        loaded = manager.load_preset(filepath.name)
        assert loaded["base_prompt"] == "Test Style"
        
        # Test get presets
        presets = manager.get_presets()
        assert len(presets) == 1
        
        # Cleanup
        shutil.rmtree(test_dir)
        
        print("✅ PresetManager working correctly")
        return True
    except Exception as e:
        print(f"❌ PresetManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config():
    """Test that config has new constants."""
    print("\nTesting config...")
    try:
        from config import TOOLTIPS, WELCOME_MESSAGE
        
        assert "base_prompt" in TOOLTIPS
        assert len(WELCOME_MESSAGE) > 0
        
        print("✅ Config has new constants")
        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("PROMPT BUILDER - FEATURE VERIFICATION TESTS")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("UndoManager", test_undo_manager()))
    results.append(("PreferencesManager", test_preferences_manager()))
    results.append(("PresetManager", test_preset_manager()))
    results.append(("Config", test_config()))
    
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("=" * 60)
    print(f"TOTAL: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All tests passed! Features are working correctly.")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please review errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
