"""Controller to manage preview scheduling and background execution.

Encapsulates debounce/throttle logic and runs prompt generation in a
background thread via `PreviewExecutor`, then applies results on the
Tk mainloop using the provided callbacks.
"""

from typing import Callable, Optional

from utils import logger

from .preview_worker import PreviewExecutor


class PreviewController:
    def __init__(
        self,
        root,
        preview_panel,
        generate_callback: Callable[[], str],
        get_selected_count: Callable[[], int],
        throttle_ms: int = 150,
    ):
        self.root = root
        self.preview_panel = preview_panel
        self.generate_callback = generate_callback
        self.get_selected_count = get_selected_count
        self.throttle_ms = throttle_ms

        self._after_id: Optional[str] = None
        self.executor = PreviewExecutor(self.root)

    def schedule_update(self, delay: Optional[int] = None):
        """Schedule a preview update with optional delay (ms)."""
        if self._after_id:
            try:
                self.root.after_cancel(self._after_id)
            except Exception:
                logger.debug("Could not cancel existing preview after id", exc_info=True)

        d = delay if delay is not None else self.throttle_ms
        self._after_id = self.root.after(d, self._submit_preview_job)
        self._update_status("Updating preview...")

    def _submit_preview_job(self):
        self._after_id = None

        def _generate():
            return self.generate_callback()

        def _on_done(result):
            if isinstance(result, Exception):
                logger.exception("Background preview generation failed")
                try:
                    self.preview_panel.update_preview("")
                    self._update_status("❌ Preview generation failed")
                except Exception:
                    logger.exception("Failed to update preview after generation error")
                return

            try:
                self.preview_panel.update_preview(result)
                num_chars = self.get_selected_count()
                self._update_status(f"Ready • {num_chars} character(s) selected")
            except Exception:
                logger.exception("Failed to apply preview result to UI")

        try:
            self.executor.submit(_generate, on_done=_on_done)
        except Exception:
            logger.exception("Failed to submit preview job; falling back to sync")
            try:
                self.preview_panel.update_preview(self.generate_callback())
            except Exception:
                logger.exception("Synchronous preview update failed after submit failure")

    def update_now(self):
        """Force immediate preview update (synchronous fallback)."""
        try:
            result = self.generate_callback()
            self.preview_panel.update_preview(result)
            num_chars = self.get_selected_count()
            self._update_status(f"Ready • {num_chars} character(s) selected")
        except Exception:
            logger.exception("Immediate preview update failed")

    def _update_status(self, message: str):
        try:
            if hasattr(self.root, "_update_status"):
                self.root._update_status(message)
        except Exception:
            logger.debug("Status update failed", exc_info=True)

    def shutdown(self):
        try:
            self.executor.shutdown(wait=False)
        except Exception:
            logger.exception("Error shutting down preview executor")
