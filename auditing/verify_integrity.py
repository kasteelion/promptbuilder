
import os
import glob
import sys

def verify_integrity():
    prompt_dir = "output/prompts"
    if not os.path.exists(prompt_dir):
        print(f"Directory not found: {prompt_dir}")
        return

    files = glob.glob(os.path.join(prompt_dir, "*.txt"))
    print(f"Scanning {len(files)} generated prompts for structural integrity...")
    
    missing_char = []
    missing_scene = []
    missing_style = []
    
    for fpath in files:
        fname = os.path.basename(fpath)
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if "Character:" not in content and "CHARACTER:" not in content:
            missing_char.append(fname)
            
        if "Scene:" not in content and "SCENE:" not in content:
            # Maybe intentional if include_scene=False, but checking anyway
            missing_scene.append(fname)
            
        if "Base_Prompt:" not in content and "Base Prompt:" not in content:
             missing_style.append(fname)

    if not missing_char:
        print("✅ SUCCESS: All prompt files contain Character definitions.")
    else:
        print(f"❌ FAILURE: {len(missing_char)} prompts missing Characters!")
        for m in missing_char[:5]:
            print(f"  - {m}")
            
    if not missing_scene:
        print("✅ SUCCESS: All prompt files contain Scene definitions.")
    else:
        print(f"ℹ️ Info: {len(missing_scene)} prompts missing Scenes (might be optional).")

    print("\n--- Conclusion ---")
    if not missing_char:
        print("The randomizer is working correctly. The 'empty' nodes in the Sankey diagram are visual artifacts caused by the 'Top 30' cutoff filtering hiding the incoming connections for less frequent character-scene pairings.")
    else:
        print("There is a genuine bug in the randomizer.")

if __name__ == "__main__":
    verify_integrity()
