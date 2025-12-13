"""Background preview executor to run expensive preview generation off the UI thread.

Provides a small wrapper around ThreadPoolExecutor that schedules the
completion callback back on the Tk mainloop using ``root.after`` so UI code
remains thread-safe.

This module intentionally keeps a minimal surface area.
"""

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable


class PreviewExecutor:
    """Run callables in a background thread and forward results to the UI.

    Methods:
        submit(func, on_done): submit ``func`` to the thread pool. When the
        function completes, ``on_done(result)`` is scheduled on the Tk mainloop
        using ``root.after(0, ...)``. If the background function raised an
        exception, the exception object is passed to ``on_done`` instead so the
        caller can decide how to handle it on the main thread.
    """

    def __init__(self, root, max_workers: int = 1):
        self.root = root
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    def submit(self, func: Callable[[], Any], on_done: Callable[[Any], None] | None = None):
        """Submit ``func`` to run in background and schedule ``on_done`` with its result.

        ``on_done`` will be called on the Tk mainloop with the result or the
        exception object if ``func`` raised.
        """
        future = self._executor.submit(func)

        if on_done:

            def _callback(fut):
                try:
                    result = fut.result()
                except Exception:  # capture background exception
                    # Keep the lambda creation inside the except so the
                    # exception instance can be captured in a closure and
                    # delivered to the main thread callback.
                    # Use sys.exc_info() to fetch the exception instance.
                    import sys

                    _exc_val = sys.exc_info()[1]
                    self.root.after(0, lambda _exc=_exc_val: on_done(_exc))
                    return
                self.root.after(0, lambda: on_done(result))

            future.add_done_callback(_callback)

        return future

    def shutdown(self, wait: bool = False):
        try:
            self._executor.shutdown(wait=wait)
        except Exception:
            # Ignore shutdown errors; nothing the app can do here.
            pass
