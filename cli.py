"""Command-line parsing utilities for Prompt Builder.

This module centralizes CLI parsing so `main.py` avoids import-time side
effects and becomes easier to test and reuse.
"""
from __future__ import annotations

import argparse
from typing import Iterable, Optional


def parse_cli(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments and return namespace.

    Keeps only the flags we previously supported so behavior remains
    unchanged while making future extensions easier.
    """
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--check-compat", action="store_true", help=argparse.SUPPRESS)
    p.add_argument("--version", "-v", action="store_true", help=argparse.SUPPRESS)
    p.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)
    return p.parse_args(argv)
