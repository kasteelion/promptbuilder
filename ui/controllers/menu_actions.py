"""Menu actions controller: centralize menu callbacks for `PromptBuilderApp`.

This adapter keeps `main_window` smaller and makes menu-related logic
easier to test and evolve.
"""

from typing import Any


class MenuActions:
    """Adapter exposing menu callbacks used by `MenuManager`.

    Each method delegates to the corresponding `PromptBuilderApp` method
    to preserve existing behavior while keeping `main_window` focused on UI layout.
    """

    def __init__(self, app: Any):
        self.app = app

    def save_preset(self):
        return self.app._save_preset()

    def load_preset(self):
        return self.app._load_preset()

    def export_config(self):
        return self.app._export_config()

    def import_config(self):
        return self.app._import_config()

    def export_for_llm(self):
        """Export condensed app data for LLM knowledge injection."""
        return self.app.dialog_manager.show_llm_export(self.app.ctx)

    def export_for_llm_creation(self):
        """Show guide for LLM content creation."""
        return self.app.dialog_manager.show_llm_content_creation(self.app.ctx)

    def import_from_text(self):
        """Show text import dialog or apply current summary box."""
        # If user is currently editing the summary box, just apply it
        # Check the panel directly instead of a stale app flag
        if hasattr(self.app, "summary_panel") and self.app.summary_panel.is_modified:
            return self.app._import_from_summary_box()
            
        available_chars = list(self.app.characters.keys())
        
        def on_success(config):
            self.app._save_state_for_undo()
            self.app._restore_state(config)
            self.app._update_status("Imported configuration from text")
            
        return self.app.dialog_manager.show_text_import(available_chars, on_success)

    def bulk_prompt_generator(self):
        """Open the bulk prompt generator tool."""
        # We need to construct a PromptBuilder instance for the tool
        # Re-using the app's loaded data
        from core.builder import PromptBuilder
        
        builder = PromptBuilder(
            self.app.characters,
            self.app.base_prompts,
            self.app.poses,
            self.app.color_schemes,
            self.app.modifiers
        )
        
        return self.app.dialog_manager.show_bulk_generator(
            self.app.data_loader,
            self.app.poses,
            builder
        )

    def undo(self):
        return self.app._undo()

    def redo(self):
        return self.app._redo()

    def clear_all_characters(self):
        return self.app._clear_all_characters()

    def reset_all_outfits(self):
        return self.app._reset_all_outfits()

    def apply_same_pose_to_all(self):
        return self.app._apply_same_pose_to_all()

    def toggle_character_gallery(self):
        # Toggle the flag then delegate to main_window logic which now uses GalleryController
        self.app._toggle_character_gallery()

    def increase_font(self):
        return self.app._increase_font()

    def decrease_font(self):
        return self.app._decrease_font()

    def reset_font(self):
        return self.app._reset_font()

    def randomize_all(self):
        return self.app.randomize_all()

    def change_theme(self, theme_name: str):
        return self.app._change_theme(theme_name)

    def toggle_auto_theme(self):
        return self.app._toggle_auto_theme()

    def show_characters_summary(self):
        return self.app.dialog_manager.show_characters_summary(
            data_loader=self.app.data_controller.data_loader,
            theme_manager=self.app.theme_manager
        )

    def show_dashboard(self):
        return self.app.dialog_manager.show_dashboard(
            data_loader=self.app.data_controller.data_loader,
            theme_manager=self.app.theme_manager
        )

    def show_outfits_summary(self):
        return self.app.dialog_manager.show_outfits_summary(
            data_loader=self.app.data_controller.data_loader,
            on_reload=self.app.reload_data
        )

    def show_color_schemes_summary(self):
        return self.app.dialog_manager.show_color_schemes_summary()

    def show_tag_summary(self):
        return self.app.dialog_manager.show_tag_summary(
            data_loader=self.app.data_controller.data_loader,
            theme_manager=self.app.theme_manager
        )

    def show_health_check(self):
        """Open the health check tab in Dashboard."""
        return self.app.dialog_manager.show_health_check(
            data_loader=self.app.data_controller.data_loader,
            theme_manager=self.app.theme_manager
        )

    def show_auditing_suite(self):
        """Open the Auditing Suite tab in Dashboard."""
        return self.app.dialog_manager.show_auditing_suite(
            data_loader=self.app.data_controller.data_loader,
            theme_manager=self.app.theme_manager
        )

    def show_automation_dialog(self, prompt: str = None):
        """Open the AI Automation tool."""
        return self.app.dialog_manager.show_automation_dialog(
            self.app.ctx,
            self.app.theme_manager,
            prompt=prompt
        )

    def generate_current_image(self):
        """Extract prompt from preview and start automation directly."""
        if not hasattr(self.app, "preview_panel") or not self.app.preview_panel.get_prompt_callback:
            return
            
        prompt = self.app.preview_panel.get_prompt_callback()
        if not prompt or prompt.startswith("--- VALIDATION ERROR ---"):
             if hasattr(self.app, "toasts"):
                 self.app.toasts.notify("Please generate a valid prompt first", "warning")
             return

        controller = self.app.ctx.automation_controller
        if not controller:
            from logic.automation_controller import AutomationController
            controller = AutomationController(self.app.ctx)
            self.app.ctx.automation_controller = controller

        if controller._thread and controller._thread.is_alive():
            if hasattr(self.app, "toasts"):
                self.app.toasts.notify("An automation task is already running", "warning")
            return

        def on_progress(current, total, message):
            self.app.root.after(0, lambda: self.app._update_status(f"🤖 {message}"))
            
        def on_complete(results):
            def _done():
                self.app._update_status("Generation complete!")
                if results and "image_path" in results[0]:
                    path = results[0]["image_path"]
                    self.app.toasts.notify(f"Image saved: {path}", "success", duration=5000)
                else:
                    self.app.toasts.notify("Image generation completed", "success")
            self.app.root.after(0, _done)

        def on_error(e):
            def _err():
                self.app._update_status(f"Error: {str(e)}")
                self.app.toasts.notify(f"Automation Error: {str(e)}", "error")
            self.app.root.after(0, _err)

        self.app.toasts.notify("Launching AI Studio...", "info")
        controller.start_generation(
            count=1,
            match_outfits_prob=0.3,
            prompts_only=False,
            on_progress=on_progress,
            on_complete=on_complete,
            on_error=on_error,
            fixed_prompt=prompt
        )

    def open_data_folder(self):
        """Open local data folder."""
        return self.app.dialog_manager.open_data_folder(self.app.data_loader)

    def show_welcome(self):
        return self.app.dialog_manager.show_welcome()

    def show_shortcuts(self):
        return self.app.dialog_manager.show_shortcuts()

    def show_about(self):
        return self.app.dialog_manager.show_about()

    def on_closing(self):
        return self.app._on_closing()

    def get_theme(self):
        try:
            return self.app.menu_manager.get_theme()
        except Exception:
            return None

    def get_auto_theme(self):
        try:
            return self.app.menu_manager.get_auto_theme()
        except Exception:
            return False

    def set_gallery_visible(self, visible: bool):
        try:
            if hasattr(self.app, "menu_manager"):
                self.app.menu_manager.set_gallery_visible(visible)
        except Exception:
            pass
