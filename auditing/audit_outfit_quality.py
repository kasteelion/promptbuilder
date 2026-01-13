import os
import glob
from collections import defaultdict
import re

def audit_outfit_quality():
    outfit_dir = "data/outfits"
    total_outfits = 0
    flagged_files = [] 
    
    print(f"\n=== OUTFIT QUALITY AUDIT (Component-Scientific Standard) ===\n")

    for filepath in glob.glob(os.path.join(outfit_dir, "**/*.txt"), recursive=True):
        filename = os.path.basename(filepath)
        
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract [F] section
        if "[F]" not in content:
            continue
            
        try:
            f_section = content.split("[F]")[1].split("[M]")[0].split("[H]")[0]
        except IndexError:
            continue
            
        total_outfits += 1
        
        lines = [line.rstrip() for line in f_section.split("\n") if line.strip()]
        
        # State tracking
        current_component = None
        component_data = defaultdict(set) # { "Top": {"Fit", "Material"}, "Bottom": ... }
        found_components = set()
        
        for line in lines:
            # Check for Component Root (e.g., "- **Top:**")
            # Must check One-Piece first or handle distinctly
            
            top_match = re.search(r"^\s*-\s*\*\*Top:\*\*", line, re.IGNORECASE)
            bottom_match = re.search(r"^\s*-\s*\*\*Bottom:\*\*", line, re.IGNORECASE)
            onepiece_match = re.search(r"^\s*-\s*\*\*One-Piece:\*\*", line, re.IGNORECASE)
            # Support Body/Dress legacy or alternatives if needed, but strict standard is specific
            
            if top_match:
                current_component = "Top"
                found_components.add("Top")
                continue
            elif bottom_match:
                current_component = "Bottom"
                found_components.add("Bottom")
                continue
            elif onepiece_match:
                current_component = "Top" # Treat One-Piece as Top for validation purposes
                found_components.add("Top") 
                continue
                
            # Check for Indented Dimensions (e.g., "  - **Fit:**")
            if current_component:
                fit_match = re.search(r"^\s+-\s*\*\*Fit:\*\*", line, re.IGNORECASE)
                mat_match = re.search(r"^\s+-\s*\*\*Material:\*\*", line, re.IGNORECASE)
                
                if fit_match:
                    component_data[current_component].add("Fit")
                if mat_match:
                    component_data[current_component].add("Material")

        # Validation Logic
        failures = []
        
        # Rule 1: Must have a Top element (or One-Piece which we mapped to Top)
        if "Top" not in found_components:
            failures.append("Missing Component: Top")
        else:
            # Rule 2: Top must have Fit
            if "Fit" not in component_data["Top"]:
                failures.append("Top Missing: Fit")
            # Rule 3: Top must have Material
            if "Material" not in component_data["Top"]:
                failures.append("Top Missing: Material")
                
        # Rule 4: If Bottom tags exists, it must have dimensions too?
        # Actually, if Top exists, Bottom *should* exist unless it's a dress/One-Piece.
        # But our standard says "Component Schema". 
        # If Bottom is present, enforce schema.
        if "Bottom" in found_components:
            if "Fit" not in component_data["Bottom"]:
                failures.append("Bottom Missing: Fit")
            if "Material" not in component_data["Bottom"]:
                failures.append("Bottom Missing: Material")
            
        if failures:
            flagged_files.append((filename, failures))

    # REPORTING
    print(f"Scanned {total_outfits} Outfits.\n")
    print("\n--- Non-Compliant Outfits (Nested Standard) ---")
    flagged_files.sort()
    for fname, errs in flagged_files:
        err_str = ", ".join(errs)
        print(f"[{fname}] {err_str}")
        
    print(f"\nTotal Flagged Entries: {len(flagged_files)}")

if __name__ == "__main__":
    audit_outfit_quality()
