# Python Version Compatibility Guide

## Supported Python Versions

This application is designed to work with **Python 3.8 and higher**.

### Tested Versions
- ✅ Python 3.8
- ✅ Python 3.9
- ✅ Python 3.10
- ✅ Python 3.11
- ✅ Python 3.12
- ✅ Python 3.13
- ✅ Python 3.14

## Why Python 3.8+?

We require Python 3.8 as the minimum version because:
1. **Walrus operator (`:=`)** - Used in some code paths (introduced in 3.8)
2. **`functools.cached_property`** - Used for performance optimizations (3.8+)
3. **Security and bug fixes** - Python 3.7 reached end-of-life in June 2023
4. **Standard library improvements** - Better typing support and pathlib enhancements

## Compatibility Features

### What We Do For Maximum Compatibility

1. **UTF-8 Encoding Declarations**
   - All Python files include `# -*- coding: utf-8 -*-` headers
   - Ensures Unicode characters work across all Python versions

2. **Standard Library Only**
   - No external dependencies required
   - Only uses built-in Python modules
   - Reduces compatibility issues and installation complexity

3. **Cross-Platform File Paths**
   - Uses `pathlib.Path` for all file operations
   - Works correctly on Windows, macOS, and Linux

4. **Version Detection**
   - Application checks Python version at startup
   - Provides helpful error messages if version is too old
   - Warns about potential issues with very new versions

## Known Compatibility Issues

### Python 3.14+
- **Unicode in String Literals**: Fixed in latest version
- **Status**: Fully compatible with proper encoding declarations

### Python 3.7 and Earlier
- **Not Supported**: Application will refuse to run
- **Why**: Missing essential standard library features
- **Solution**: Upgrade to Python 3.8 or higher

## Platform-Specific Notes

### Windows
- ✅ Fully supported
- tkinter included with standard Python installation
- Tested on Windows 10 and 11

### macOS
- ✅ Fully supported
- tkinter included with standard Python installation
- Tested on macOS 11+ (Big Sur and later)

### Linux
- ✅ Fully supported with tkinter installed
- tkinter may need separate installation:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install python3-tk
  
  # Fedora/RHEL
  sudo dnf install python3-tkinter
  
  # Arch Linux
  sudo pacman -S tk
  ```

## Checking Your Python Version

```bash
python --version
# or
python3 --version
```

## Upgrading Python

### Windows
1. Download from [python.org](https://www.python.org/downloads/)
2. Run installer with "Add to PATH" checked
3. Restart terminal

### macOS
```bash
# Using Homebrew
brew install python@3.12

# Or download from python.org
```

### Linux
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3.12

# Fedora
sudo dnf install python3.12
```

## Virtual Environment Setup (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate

# Run the app
python main.py
```

## Reporting Issues

If you encounter Python version compatibility issues:

1. Check your Python version: `python --version`
2. Ensure you're using Python 3.8 or higher
3. Try running with `python3` instead of `python`
4. Check that tkinter is installed: `python -m tkinter`
5. Report the issue with:
   - Your Python version
   - Your operating system
   - The full error message
   - Steps to reproduce

## Future Compatibility

We aim to maintain compatibility with:
- **Current stable Python releases** (3.11, 3.12, 3.13)
- **Future releases** (tested with pre-release versions when available)
- **Legacy support** for Python 3.8+ as long as feasible

## Why No Type Hints Everywhere?

While Python 3.8+ supports comprehensive type hints, we've kept them minimal to:
1. Maintain readability for Python beginners
2. Reduce visual complexity in UI code
3. Avoid potential compatibility issues with future Python versions
4. Keep the codebase accessible to contributors

Type hints may be added in the future for better IDE support and type checking.
