import sys
import os

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    print("Checking outfit_templates.py...")
    from src.utils import outfit_templates
    print("outfit_templates imported successfully.")
    print(f"Templates: {outfit_templates.get_template_names()}")

    print("\nChecking outfit_builder_dialog.py...")
    # Mocking ThemeManager if needed, but imports should work if file exists
    # If ThemeManager is not in path, it might fail. Let's see.
    from src.ui.dialogs.outfit_builder_dialog import OutfitBuilderDialog
    print("OutfitBuilderDialog imported successfully.")

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
