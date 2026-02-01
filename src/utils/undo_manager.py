# -*- coding: utf-8 -*-
"""Undo/Redo manager for tracking state changes.

This module avoids importing UI-specific constants at import time to
prevent circular imports. If no `max_history` is provided, a sensible
default is used.
"""


class UndoManager:
    """Manages undo/redo stacks for application state."""

    def __init__(self, max_history=None):
        """Initialize undo manager.

        Args:
            max_history: Maximum number of states to keep in history (defaults to MAX_UNDO_STACK_SIZE)
        """
        # Use provided max_history or a reasonable default to avoid importing
        # UI constants at module import time (which can create circular deps).
        self.max_history = max_history if max_history is not None else 50
        self.undo_stack = []
        self.redo_stack = []
        self._current_state = None

    def save_state(self, state):
        """Save current state to undo stack.

        Args:
            state: Dictionary containing current application state
        """
        if self._current_state is not None:
            self.undo_stack.append(self._current_state)
            # Limit stack size
            if len(self.undo_stack) > self.max_history:
                self.undo_stack.pop(0)

        self._current_state = self._deep_copy(state)
        # Clear redo stack on new action
        self.redo_stack.clear()

    def undo(self):
        """Undo last action and return previous state.

        Returns:
            Previous state dictionary or None if no undo available
        """
        if not self.undo_stack:
            return None

        # Save current state to redo stack
        if self._current_state is not None:
            self.redo_stack.append(self._current_state)

        # Pop from undo stack
        self._current_state = self.undo_stack.pop()
        return self._deep_copy(self._current_state)

    def redo(self):
        """Redo last undone action and return next state.

        Returns:
            Next state dictionary or None if no redo available
        """
        if not self.redo_stack:
            return None

        # Save current state to undo stack
        if self._current_state is not None:
            self.undo_stack.append(self._current_state)

        # Pop from redo stack
        self._current_state = self.redo_stack.pop()
        return self._deep_copy(self._current_state)

    def can_undo(self):
        """Check if undo is available."""
        return len(self.undo_stack) > 0

    def can_redo(self):
        """Check if redo is available."""
        return len(self.redo_stack) > 0

    def clear(self):
        """Clear all undo/redo history."""
        self.undo_stack.clear()
        self.redo_stack.clear()
        self._current_state = None

    def _deep_copy(self, state):
        """Create a deep copy of state dictionary.

        Args:
            state: State dictionary to copy

        Returns:
            Deep copy of state
        """
        import copy

        return copy.deepcopy(state)
