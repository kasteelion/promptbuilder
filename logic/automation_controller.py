"""Automation controller for managing background image generation.

Encapsulates the logic for generating prompts and/or images using
the AI Studio automation client while providing progress updates
compatible with a Tkinter UI.
"""

import asyncio
import os
import threading
import queue
from typing import List, Callable, Dict, Any

from automation.ai_studio_client import AIStudioClient
from logic.data_loader import DataLoader
from logic.randomizer import PromptRandomizer
from core.builder import PromptBuilder

class AutomationController:
    """Manages background automation tasks."""

    def __init__(self, ctx):
        self.ctx = ctx
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
        fixed_prompt: str = None
    ):
        """Start the generation process in a background thread."""
        self.stop_requested = False
        self._thread = threading.Thread(
            target=self._run_thread,
            args=(count, match_outfits_prob, prompts_only, on_progress, on_complete, on_error, fixed_prompt),
            daemon=True
        )
        self._thread.start()

    def stop(self):
        """Request the background thread to stop."""
        self.stop_requested = True

    def _run_thread(self, count, match_outfits_prob, prompts_only, on_progress, on_complete, on_error, fixed_prompt):
        """Worker thread entry point."""
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            
            results = self._loop.run_until_complete(
                self._generate_task(count, match_outfits_prob, prompts_only, on_progress, fixed_prompt)
            )
            
            # Use after() or queue to call on_complete back on main thread if needed,
            # but for now we'll assume the caller handles thread safety.
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
        fixed_prompt: str = None
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
            on_progress(0, count, "Loading data and randomizing prompts...")
            loader = DataLoader()
            chars = loader.load_characters()
            base_prompts = loader.load_base_prompts()
            poses = loader.load_presets("poses.md")
            scenes = loader.load_presets("scenes.md")
            schemes = loader.load_color_schemes()
            modifiers = loader.load_modifiers()
            interactions = loader.load_interactions()
            framing = loader.load_framing()
            
            builder = PromptBuilder(chars, base_prompts, poses, schemes, modifiers, framing)
            randomizer = PromptRandomizer(chars, base_prompts, poses, scenes, interactions, schemes, modifiers, framing)
            
            for i in range(count):
                if self.stop_requested:
                    break
                
                on_progress(i, count, f"Randomizing prompt {i+1}/{count}...")
                config = randomizer.randomize(
                    num_characters=None,
                    include_scene=True,
                    include_notes=True,
                    match_outfits_prob=match_outfits_prob
                )
                prompt_text = builder.generate(config)
                prompts_with_meta.append({
                    "prompt": prompt_text,
                    "config": config,
                    "score": config.get("metadata", {}).get("score", 0)
                })

        if self.stop_requested or prompts_only:
            # If prompts-only, we should still save them if requested, 
            # but let's see how integrate with ai_studio_client.
            # Actually, automate_generation.py has save_local_generation logic.
            # Let's keep it simple here and just return objects.
            return prompts_with_meta

        # 2. Browser Automation (Slow)
        # We need a progress wrapper to pass to AIStudioClient
        def client_progress_shim(current, total, message):
            if not self.stop_requested:
                on_progress(current, total, message)

        # Setup paths (similar to automate_generation.py)
        # We use parent dir logic
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(base_dir, "output", "images", "generated_images")
        user_data_dir = os.path.join(base_dir, ".config", "chrome_profile")
        
        client = AIStudioClient(
            output_dir=output_dir,
            user_data_dir=user_data_dir,
            headless=False
        )
        
        batch_prompts = [f"Generate an image of: {p['prompt']}" for p in prompts_with_meta]
        
        # This will run in the background thread's loop
        results = await client.generate_images(batch_prompts, progress_callback=client_progress_shim)
        
        # Merge results
        final_results = []
        for i, (prompt, img_path) in enumerate(results):
            res = prompts_with_meta[i].copy()
            res["image_path"] = img_path
            final_results.append(res)
            
        return final_results
