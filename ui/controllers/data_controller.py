# -*- coding: utf-8 -*-
"""Controller for data lifecycle and synchronization."""

from typing import Callable
from utils import logger


class DataController:
    """Handles data loading, reloading, and synchronization."""

    def __init__(self, ctx):
        """Initialize DataController.

        Args:
            ctx: AppContext instance
        """
        self.ctx = ctx
        self.data_loader = ctx.data_loader

    def load_initial_data(self, on_success: Callable, on_error: Callable):
        """Start async initial data load."""
        self.ctx.load_data_async(on_success, on_error)

    def sync_character_tags(self) -> int:
        """Sync tags from character files to tags.md."""
        try:
            return self.data_loader.sync_tags()
        except Exception:
            logger.exception("DataController: failed to sync tags")
            return 0

    def reload_all_data(self, on_success: Callable, on_error: Callable):
        """Force a fresh reload of all data from disk."""
        try:
            self.data_loader.clear_cache()
            self.ctx.load_data_async(on_success, on_error)
        except Exception as e:
            on_error(e)

    def get_editable_files(self) -> list:
        """Get list of files that can be edited in the app."""
        return self.data_loader.get_editable_files()
