"""Facade for automation controllers."""

import asyncio
import threading
from typing import List, Callable, Dict, Any, Optional

from logic.automation.gemma_pipeline import GemmaPipelineRunner
from logic.automation.asset_automation import AssetAutomationManager

class AutomationOrchestrator:
    """Manages background automation tasks and routes them to specific managers."""

    def __init__(self, ctx, app_state=None):
        self.ctx = ctx
        self.app_state = app_state
        
        self.gemma_runner = GemmaPipelineRunner(ctx, app_state)
        self.asset_manager = AssetAutomationManager(ctx, app_state)
        
        self.stop_requested = False
        self._thread = None
        self._loop = None

    def is_running(self) -> bool:
        """Check if a generation thread is currently running."""
        return self._thread is not None and self._thread.is_alive()

    def start_generation(
        self,
        count: int,
        match_outfits_prob: float,
        prompts_only: bool,
        on_progress: Callable[[int, int, str], None],
        on_complete: Callable[[List[Dict[str, Any]]], None],
        on_error: Callable[[Exception], None],
        fixed_prompt: str = None,
        num_characters: int = None,
        include_scene: bool = True,
        include_notes: bool = True,
        candidates: int = 3,
        forced_characters: List[str] = None,
        forced_scenario: str = None,
        use_gemma: bool = False,
        use_critic: bool = False,
        pure_gemma: bool = False,
        character_pool: List[str] = None,
        format_type: str = "markdown"
    ):
        """Start the generation process in a background thread."""
        if self.is_running():
            on_error(RuntimeError("Generation pipeline is already running."))
            return

        self.stop_requested = False
        self.gemma_runner.stop_requested = False
        
        self._thread = threading.Thread(
            target=self._run_thread,
            args=(count, match_outfits_prob, prompts_only, on_progress, on_complete, on_error, 
                  fixed_prompt, num_characters, include_scene, include_notes, candidates, 
                  forced_characters, forced_scenario, use_gemma, use_critic, pure_gemma, character_pool,
                  format_type),
            daemon=True
        )
        self._thread.start()

    def stop(self):
        """Request the background thread to stop."""
        self.stop_requested = True
        self.gemma_runner.stop()

    def _run_thread(self, count, match_outfits_prob, prompts_only, on_progress, on_complete, on_error, 
                    fixed_prompt, num_characters, include_scene, include_notes, candidates, 
                    forced_characters, forced_scenario, use_gemma, use_critic, pure_gemma, character_pool,
                    format_type="markdown"):
        """Worker thread entry point."""
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            
            results = self._loop.run_until_complete(
                self.gemma_runner.run_batch(
                    count, match_outfits_prob, prompts_only, on_progress, 
                    fixed_prompt, num_characters, include_scene, include_notes, candidates, 
                    forced_characters, forced_scenario, use_gemma, use_critic, pure_gemma, character_pool,
                    format_type=format_type
                )
            )
            
            if not self.stop_requested:
                on_complete(results)
                
        except Exception as e:
            on_error(e)
        finally:
            if self._loop:
                if self._loop.is_running():
                    self._loop.stop()
                try:
                    self._loop.close()
                except RuntimeError:
                    pass # Already closed or running
            self._thread = None

    def generate_character_portrait(self, character_name: str, on_complete: Callable = None):
        """Delegates portrait generation to the Asset Manager."""
        self.asset_manager.generate_character_portrait(character_name, on_complete)
