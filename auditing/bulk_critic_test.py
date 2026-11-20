import sys
import os
import asyncio
import time
import traceback

# Setup paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))
os.chdir(PROJECT_ROOT)

try:
    # Test imports
    from core.app_state import AppState
    from logic.automation_controller import AutomationController
except ImportError as e:
    print(f"Error: Could not import project modules: {e}")
    print(f"DEBUG: SCRIPT_DIR={SCRIPT_DIR}")
    print(f"DEBUG: PROJECT_ROOT={PROJECT_ROOT}")
    print(f"DEBUG: sys.path[0]={sys.path[0]}")
    sys.exit(1)

async def run_audit():
    print("--- Bulk Critic Audit Tool ---")
    print("Initializing App State (Loading Characters, Outfits, Scenarios)...")
    
    # AppState requires a Flet page object, but since we are running headless
    # for the audit, we pass None. load_data() handles this gracefully.
    state = AppState(None)
    
    try:
        state.load_data()
    except Exception as e:
        print(f"Failed to load data: {e}")
        return

    print(f"Data loaded. Characters: {len(state.ctx.characters_metadata)}")
    
    # Ensure Gemma is detected
    if state.ctx.gemma_client:
        print(f"Gemma Client initialized. Local model: {state.ctx.gemma_client.ollama_model}")
    else:
        print("Warning: Gemma Client not found in context. Audit will likely fail or skip.")

    controller = AutomationController(state.ctx, app_state=state)
    
    def on_progress(current, total, msg):
        # Clean progress printing
        sys.stdout.write(f"\r[{current}/{total}] {msg:<60}")
        sys.stdout.flush()

    print("\nStarting generation of 10 prompts with AI Critic active...")
    print("Settings: Include Scene=True, Include Interaction=True, Candidates=3")
    
    start_time = time.time()
    try:
        results = await controller._generate_task(
            count=10,
            match_outfits_prob=0.4,
            prompts_only=True,
            on_progress=on_progress,
            include_scene=True,
            include_notes=True,
            use_gemma=False,  # Set to True if you also want Gemma enhancement
            use_critic=True,
            candidates=3
        )
        
        duration = time.time() - start_time
        print(f"\n\nDone! Generated {len(results)} prompts in {duration:.1f}s")
        
        # Display a quick summary
        print("\n--- Summary ---")
        for i, res in enumerate(results):
            score = res.get("critic_score")
            if score is None:
                # Fallback to normalized internal score if critic was skipped
                score = (res.get("score", 0) / 1000.0) * 10.0 if res.get("score", 0) > 10 else res.get("score", 0)
            
            status = "PASSED" if score >= 7.5 else ("FIXED" if score >= 5.0 else "REJECTED")
            print(f"Prompt {i+1}: Critic Score {score:.1f}/10 [{status}]")
        
        print("\nFull audit logs and rejected compositions saved to: output/logs/")
        print("Detailed prompt text can be found in the latest 'critic_audit_*.json' file.")

    except Exception as e:
        print(f"\n\nCritical Error during generation: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(run_audit())
    except KeyboardInterrupt:
        print("\nAudit cancelled by user.")
