"""Handles background generation of local assets (e.g. missing character portraits)."""

import asyncio
import os
import re
import threading
from typing import Callable

from utils.ai_client import AIStudioClient

class AssetAutomationManager:
    """Manages generation and caching of application assets."""
    
    def __init__(self, ctx, app_state):
        self.ctx = ctx
        self.app_state = app_state
        self._portrait_lock = threading.Lock()
        self._active_portrait_tasks = set()

    def generate_character_portrait(self, character_name: str, on_complete: Callable = None):
        """Generate a character portrait in a background thread."""
        with self._portrait_lock:
            if character_name in self._active_portrait_tasks:
                return
            self._active_portrait_tasks.add(character_name)
            
        threading.Thread(
            target=self._run_portrait_thread,
            args=(character_name, on_complete),
            daemon=True
        ).start()

    def _run_portrait_thread(self, character_name: str, on_complete: Callable = None):
        with self._portrait_lock:
            loop = None
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._generate_portrait_async(character_name))
                if on_complete:
                    on_complete()
            except Exception as e:
                try:
                    from utils import logger
                    logger.error(f"Error generating portrait for {character_name}: {e}")
                except ImportError:
                    print(f"Error generating portrait for {character_name}: {e}")
            finally:
                if loop and loop.is_running():
                    loop.stop()
                try:
                    if loop:
                        loop.close()
                except RuntimeError:
                    pass
                with self._portrait_lock:
                    if character_name in self._active_portrait_tasks:
                        self._active_portrait_tasks.remove(character_name)

    async def _generate_portrait_async(self, character_name: str):
        # 1. Look up character details
        details = self.ctx.characters.get(character_name)
        if not details:
            if self.app_state:
                self.app_state.ensure_character_loaded(character_name)
                details = self.ctx.characters.get(character_name)
        
        if not details:
            print(f"Could not load character {character_name}")
            return
            
        # 2. Construct prompt using PromptBuilder
        prompt = ""
        if hasattr(self, "app_state") and self.app_state and hasattr(self.app_state, "builder"):
            from core.models import PromptConfig, SelectedCharacterConfig
            try:
                scene_text = "A professional photography studio with a high-key setup. C-stands, softboxes, and reflectors are positioned around a seamless grey backdrop. The space is clinical and optimized for commercial imaging.\n\n- **Lighting:** Multi-point strobe setup; crisp and shadowless.\n- **Atmosphere:** Professional, technical, smell of fresh electronics.\n- **Key Elements:** Umbrella reflectors, camera tripod, cooling fans, tethering cables."
                config = PromptConfig(
                    base_prompt="Studio Photorealism",
                    scene=scene_text,
                    selected_characters=[
                        SelectedCharacterConfig(
                            name=character_name,
                            outfit="Base"
                        )
                    ]
                )
                built_prompt = self.app_state.builder.generate(config)
                prompt = f"Generate an image of:\n{built_prompt}"
            except Exception as e:
                import traceback
                print(f"Error using PromptBuilder: {e}")
                traceback.print_exc()
                
        if not prompt:
            # Fallback logic if PromptBuilder is unavailable
            appearance = str(details.appearance) if hasattr(details, "appearance") else ""
            base_outfit = str(details.outfits.get("Base", "")) if hasattr(details, "outfits") and isinstance(details.outfits, dict) else ""
            prompt = f"Waist-up portrait, plain white background. Character: {character_name}. Appearance: {appearance}. Wearing: {base_outfit}. Style: studio photorealism"
        
        # 4. Generate
        import pathlib
        import shutil
        client = AIStudioClient(
            output_dir=os.path.join(os.getcwd(), "output", "images", "generated_images"),
            headless=False
        )
        
        print(f"Generating portrait for {character_name}...")
        results = await client.generate_images([prompt])
        
        # 5. Move image
        if results and results[0][1]:
            image_path = results[0][1]
            
            filename = character_name.lower().replace(" ", "_")
            filename = re.sub(r'[^a-z0-9_]', '', filename) + "_photo.png"
            dest = pathlib.Path("assets/data/characters") / filename
            
            shutil.move(image_path, dest)
            print(f"Generated portrait saved to {dest}")
            
            if self.app_state:
                # Dispatch an event to reload assets and refresh the roster safely
                if hasattr(self.app_state.page, "run_task"):
                    async def _refresh_ui(*args):
                        self.app_state.page.window_prevent_close = True # Dummy op to ensure thread safety
                        self.app_state.refresh_data()
                    self.app_state.page.run_task(_refresh_ui)
