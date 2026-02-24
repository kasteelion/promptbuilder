"""Automation controller for managing background image generation.

Encapsulates the logic for generating prompts and/or images using
the AI Studio automation client while providing progress updates
compatible with the Flet UI.
"""

import asyncio
import os
import threading
import queue
from typing import List, Callable, Dict, Any

from utils.ai_client import AIStudioClient


class AutomationController:
    """Manages background automation tasks."""

    def __init__(self, ctx, app_state=None):
        self.ctx = ctx
        self.app_state = app_state  # AppState has .builder
        self.stop_requested = False
        self._thread = None
        self._loop = None
        self._queue = queue.Queue()

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
        forced_scenario: str = None
    ):
        """Start the generation process in a background thread."""
        self.stop_requested = False
        self._thread = threading.Thread(
            target=self._run_thread,
            args=(count, match_outfits_prob, prompts_only, on_progress, on_complete, on_error, 
                  fixed_prompt, num_characters, include_scene, include_notes, candidates, forced_characters, forced_scenario),
            daemon=True
        )
        self._thread.start()

    def stop(self):
        """Request the background thread to stop."""
        self.stop_requested = True

    def _run_thread(self, count, match_outfits_prob, prompts_only, on_progress, on_complete, on_error, 
                    fixed_prompt, num_characters, include_scene, include_notes, candidates, forced_characters, forced_scenario):
        """Worker thread entry point."""
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            
            results = self._loop.run_until_complete(
                self._generate_task(count, match_outfits_prob, prompts_only, on_progress, 
                                    fixed_prompt, num_characters, include_scene, include_notes, candidates, forced_characters, forced_scenario)
            )
            
            if not self.stop_requested:
                on_complete(results)
                
        except Exception as e:
            on_error(e)
        finally:
            if self._loop:
                self._loop.close()

    async def _generate_task(
        self, 
        count: int, 
        match_outfits_prob: float, 
        prompts_only: bool,
        on_progress: Callable[[int, int, str], None],
        fixed_prompt: str = None,
        num_characters: int = None,
        include_scene: bool = True,
        include_notes: bool = True,
        candidates: int = 3,
        forced_characters: List[str] = None,
        forced_scenario: str = None
    ) -> List[Dict[str, Any]]:
        """Internal task that handles the logic."""
        prompts_with_meta = []
        if fixed_prompt:
             prompts_with_meta.append({
                "prompt": fixed_prompt,
                "config": {},
                "score": 100
            })
        else:
            on_progress(0, count, "Randomizing prompts...")

            # Reuse already-loaded data from the application context
            builder = self.app_state.builder if self.app_state else None
            randomizer = self.ctx.randomizer

            if not builder or not randomizer:
                raise RuntimeError("Builder or Randomizer not initialized. Load data first.")
            
            # Ensure all available characters are loaded for randomization variety (Lazy Loading support)
            all_names = list(self.ctx.characters_metadata.keys())
            if len(self.ctx.characters) < len(all_names):
                on_progress(0, count, f"Preparing character pool ({len(all_names)} characters)...")
                for name in all_names:
                    if self.stop_requested: break
                    if self.app_state:
                        self.app_state.ensure_character_loaded(name)
            
            for i in range(count):
                if self.stop_requested:
                    break
                
                on_progress(i, count, f"Randomizing prompt {i+1}/{count}...")
                config = randomizer.randomize(
                    num_characters=num_characters,
                    include_scene=include_scene,
                    include_notes=include_notes,
                    match_outfits_prob=match_outfits_prob,
                    candidates=candidates,
                    forced_characters=forced_characters,
                    forced_scenario=forced_scenario
                )
                prompt_text = builder.generate(config)
                prompts_with_meta.append({
                    "prompt": prompt_text,
                    "config": config,
                    "score": config.get("metadata", {}).get("score", 0)
                })

        if self.stop_requested or not prompts_with_meta:
            return prompts_with_meta

        if prompts_only:
            return prompts_with_meta

        # 2. Browser Automation (Slow)
        def client_progress_shim(current, total, message):
            if not self.stop_requested:
                on_progress(current, total, message)

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        output_dir = os.path.join(base_dir, "output", "images", "generated_images")
        user_data_dir = os.path.join(base_dir, ".config", "chrome_profile")
        
        client = AIStudioClient(
            output_dir=output_dir,
            user_data_dir=user_data_dir,
            headless=False
        )
        
        batch_prompts = [f"Generate an image of: {p['prompt']}" for p in prompts_with_meta]
        
        results = await client.generate_images(batch_prompts, progress_callback=client_progress_shim)
        
        # Merge results
        final_results = []
        for i, (prompt, img_path) in enumerate(results):
            res = prompts_with_meta[i].copy()
            res["image_path"] = img_path
            final_results.append(res)
            
        return final_results
