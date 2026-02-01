"""Python version compatibility utilities."""

import sys
from typing import Tuple


def get_python_version() -> Tuple[int, int, int]:
    """Get the current Python version as a tuple.

    Returns:
        Tuple of (major, minor, micro) version numbers
    """
    return (sys.version_info.major, sys.version_info.minor, sys.version_info.micro)


def is_version_compatible(min_version: Tuple[int, int] = (3, 8)) -> bool:
    """Check if current Python version meets minimum requirement.

    Args:
        min_version: Minimum required (major, minor) version

    Returns:
        True if compatible, False otherwise
    """
    current = (sys.version_info.major, sys.version_info.minor)
    return current >= min_version


def get_version_string() -> str:
    """Get a formatted version string.

    Returns:
        Formatted string like "Python 3.12.1"
    """
    major, minor, micro = get_python_version()
    return f"Python {major}.{minor}.{micro}"


def check_tkinter_available() -> bool:
    """Check if tkinter is available.

    Returns:
        True if tkinter can be imported, False otherwise
    """
    # Use importlib to check for the presence of the tkinter module without
    # importing it directly (avoids side-effects and linter warnings).
    try:
        import importlib.util

        return importlib.util.find_spec("tkinter") is not None
    except Exception:
        from utils import logger

        logger.exception("Auto-captured exception")
        return False


def print_version_error():
    """Print detailed error message for incompatible Python version."""
    print("=" * 70)
    print("ERROR: Python Version Too Old")
    print("=" * 70)
    print(
        f"Current version: Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    print("Required version: Python 3.8 or higher")
    print()
    print("This application requires Python 3.8+ for:")
    print("  - Modern standard library features")
    print("  - Better Unicode support")
    print("  - Security fixes and performance improvements")
    print()
    print("Please upgrade your Python installation:")
    print("  Windows: https://www.python.org/downloads/")
    print("  macOS:   brew install python@3.12")
    print("  Linux:   sudo apt-get install python3.12")
    print("=" * 70)


def print_tkinter_error():
    """Print detailed error message for missing tkinter."""
    print("=" * 70)
    print("ERROR: tkinter Not Available")
    print("=" * 70)
    print("tkinter is required but not installed.")
    print()
    print("Installation instructions:")
    print("  Ubuntu/Debian:  sudo apt-get install python3-tk")
    print("  Fedora/RHEL:    sudo dnf install python3-tkinter")
    print("  Arch Linux:     sudo pacman -S tk")
    print("  macOS/Windows:  tkinter should be included with Python")
    print()
    print("If you installed Python from python.org, tkinter should be included.")
    print("If using a system Python, you may need to install it separately.")
    print("=" * 70)


def check_requirements() -> bool:
    """Check all requirements and return True if met, False otherwise.

    Prints helpful error messages if requirements are not met.

    Returns:
        True if all requirements met, False otherwise
    """
    if not is_version_compatible():
        print_version_error()
        return False

    if not check_tkinter_available():
        print_tkinter_error()
        return False

    return True


def get_compatibility_report() -> dict:
    """Generate a compatibility report.

    Returns:
        Dictionary with compatibility information
    """
    major, minor, micro = get_python_version()

    return {
        "python_version": f"{major}.{minor}.{micro}",
        "version_tuple": (major, minor, micro),
        "is_compatible": is_version_compatible(),
        "tkinter_available": check_tkinter_available(),
        "platform": sys.platform,
        "min_required_version": "3.8.0",
        "recommended_version": "3.11+",
    }


def print_compatibility_report():
    """Print a human-readable compatibility report."""
    report = get_compatibility_report()

    print("=" * 60)
    print("Prompt Builder - Compatibility Report")
    print("=" * 60)
    print(f"Python Version: {report['python_version']}")
    print(f"Platform: {report['platform']}")
    print(f"Minimum Required: {report['min_required_version']}")
    print(f"Recommended: {report['recommended_version']}")
    print()

    if report["is_compatible"]:
        print("✓ Python version is compatible")
    else:
        print("✗ Python version is TOO OLD")
        print(f"  Please upgrade to Python {report['min_required_version']} or higher")

    if report["tkinter_available"]:
        print("✓ tkinter is available")
    else:
        print("✗ tkinter is NOT available")
        print("  Please install python3-tk package for your system")

    print("=" * 60)


if __name__ == "__main__":
    # Run compatibility check when executed directly
    print_compatibility_report()
