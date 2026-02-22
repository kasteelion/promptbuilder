import threading

class Debouncer:
    """Helper for delaying function execution until a pause in updates.
    
    Useful for:
    - Search bars (wait for typing to stop)
    - Resize events
    - High-frequency UI updates
    """
    
    def __init__(self, delay_ms: float):
        self.delay = delay_ms / 1000.0
        self.timer = None
        self._lock = threading.Lock()

    def debounce(self, func, *args, **kwargs):
        """Reset timer and schedule function call."""
        with self._lock:
            if self.timer:
                self.timer.cancel()
            
            self.timer = threading.Timer(self.delay, func, args=args, kwargs=kwargs)
            self.timer.start()

    def cancel(self):
        """Cancel any pending execution."""
        with self._lock:
            if self.timer:
                self.timer.cancel()
                self.timer = None
