"""Entrypoint shim for Prompt Builder.

Keep this file minimal: delegate runtime behavior to `Runner` in
`runner.py` so the startup sequence is easier to test and maintain.
"""

import sys

from runner import Runner


def main(argv=None) -> int:
    """Run the application via the Runner class.

    Accepts an optional `argv` list for testing; returns an exit code.
    """
    return Runner().run(argv)


if __name__ == "__main__":
    sys.exit(main())
