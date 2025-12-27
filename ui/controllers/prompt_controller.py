# -*- coding: utf-8 -*-
"""Controller for prompt assembly and validation."""

from core.builder import PromptBuilder
from logic import validate_prompt_config


class PromptController:
    """Handles prompt generation, summary creation, and validation logic."""

    def __init__(self, ctx):
        """Initialize PromptController.

        Args:
            ctx: AppContext instance
        """
        self.ctx = ctx

    def generate_full_prompt(self, config: dict) -> str:
        """Assemble the complete prompt string.

        Args:
            config: Dictionary containing selected_characters, base_prompt, scene, notes

        Returns:
            str: Generated prompt
        """
        builder = PromptBuilder(
            self.ctx.characters,
            self.ctx.base_prompts,
            self.ctx.poses,
            self.ctx.color_schemes,
            self.ctx.modifiers
        )
        return builder.generate(config)

    def generate_summary(self, config: dict) -> str:
        """Assemble the condensed summary string.

        Args:
            config: Dictionary containing selected_characters, scene, notes

        Returns:
            str: Generated summary
        """
        builder = PromptBuilder(
            self.ctx.characters,
            self.ctx.base_prompts,
            self.ctx.poses,
            self.ctx.color_schemes,
            self.ctx.modifiers
        )
        return builder.generate_summary(config)

    def validate(self, selected_characters: list) -> str | None:
        """Validate the current character selection.

        Returns:
            str: Error message or None if valid
        """
        return validate_prompt_config(selected_characters)

    def generate_or_error(self, config: dict) -> str:
        """Generate prompt or return empty string if invalid."""
        error = self.validate(config.get("selected_characters", []))
        if error:
            return ""
        return self.generate_full_prompt(config)
