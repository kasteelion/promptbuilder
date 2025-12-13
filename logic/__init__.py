"""Logic package public API.

This module exposes the primary classes and functions from submodules but
avoids importing them at package import time to prevent circular import
problems (for example when UI modules import the `logic` package during
their own initialization).

Consumers can still do `from logic import DataLoader` — the attribute
access will import the corresponding submodule lazily.
"""

from importlib import import_module
from typing import Any, List

__all__ = ['MarkdownParser', 'DataLoader', 'validate_prompt_config', 'PromptRandomizer']


def _load(name: str) -> Any:
	mapping = {
		'MarkdownParser': ('.parsers', 'MarkdownParser'),
		'DataLoader': ('.data_loader', 'DataLoader'),
		'PromptRandomizer': ('.randomizer', 'PromptRandomizer'),
		'validate_prompt_config': ('.validator', 'validate_prompt_config'),
	}
	mod_name, attr = mapping[name]
	module = import_module(mod_name, __package__)
	return getattr(module, attr)


def __getattr__(name: str) -> Any:  # module-level lazy attribute loader (PEP 562)
	if name in __all__:
		value = _load(name)
		globals()[name] = value
		return value
	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> List[str]:
	return sorted(list(globals().keys()) + __all__)

