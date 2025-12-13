"""Background preview executor to run expensive preview generation off the UI thread.

Provides a simple wrapper around ThreadPoolExecutor that schedules callbacks
back on the Tk mainloop using the provided `root.after`.
"""
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Any


class PreviewExecutor:
    def __init__(self, root, max_workers: int = 1):
        self.root = root
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    def submit(self, func: Callable[[], Any], on_done: Callable[[Any], None] | None = None):
        """Submit `func` to run in background. When finished, `on_done(result)`
        will be scheduled on the Tk mainloop via `root.after(0, ...)`.
        """
        future = self._executor.submit(func)

        if on_done:
            def _callback(f):
                try:
                    result = f.result()
                except Exception as exc:  # capture background exception
                    # Schedule raising/logging on main thread by passing the exception
                    self.root.after(0, lambda: on_done(exc))
                    return
                self.root.after(0, lambda: on_done(result))

            future.add_done_callback(_callback)

        return future

    def shutdown(self, wait: bool = False):
        try:
            self._executor.shutdown(wait=wait)
        except Exception:
            pass
