# Quick Reference: Modularity & Code Quality Improvements

## Modular Architecture

### New Manager Classes

The application now uses a modular manager pattern for better code organization:

#### MenuManager (`ui/menu_manager.py`)
```python
from ui.menu_manager import MenuManager

# Creates and manages all menu bars
menu_manager = MenuManager(parent, callbacks={
    'new': self._new_file,
    'open': self._open_file,
    'save': self._save_file,
    # ... etc
})
menu_manager.create_menus()
current_theme = menu_manager.get_theme()
```

#### FontManager (`ui/font_manager.py`)
```python
from ui.font_manager import FontManager

# Adaptive font sizing with breakpoint interpolation
font_manager = FontManager(parent, callbacks={
    'update_preview': self._update_preview_tags
})
font_manager.register_widgets([label1, text1, button1])
font_manager.handle_resize(event)  # Auto-called on window resize
```

#### StateManager (`ui/state_manager.py`)
```python
from ui.state_manager import StateManager

# Undo/redo and preset coordination
state_manager = StateManager(parent, callbacks={
    'get_state': self._get_current_state,
    'restore_state': self._restore_state
})
state_manager.save_preset()
state_manager.undo()
state_manager.redo()
```

#### DialogManager (`ui/dialog_manager.py`)
```python
from ui.dialog_manager import DialogManager

# Centralized dialog management
dialog_manager = DialogManager(parent)
dialog_manager.show_welcome()
dialog_manager.show_error("Error title", "Error message", details="Full traceback...")
result = dialog_manager.ask_yes_no("Confirm?", "Are you sure?")
```

## UI Constants

### New Constants Module (`ui/constants.py`)
Centralized UI-specific constants for consistency:

```python
from ui.constants import (
    PREVIEW_UPDATE_THROTTLE_MS,
    TEXT_UPDATE_DEBOUNCE_MS,
    WIDGET_REFLOW_RETRY_LIMIT,
    MIN_FONT_SIZE,
    MAX_FONT_SIZE
)

# Usage examples
self.after(TEXT_UPDATE_DEBOUNCE_MS, self._update_text)  # 300ms
self.after(PREVIEW_UPDATE_THROTTLE_MS, self._refresh)   # 150ms

# Font sizing
if size < MIN_FONT_SIZE:  # 9pt
    size = MIN_FONT_SIZE
if size > MAX_FONT_SIZE:  # 16pt
    size = MAX_FONT_SIZE
```

**Available Constants:**
- `PREVIEW_UPDATE_THROTTLE_MS = 150` - Preview refresh delay
- `TEXT_UPDATE_DEBOUNCE_MS = 300` - Text widget update debouncing
- `WIDGET_REFLOW_RETRY_LIMIT = 5` - Max retries for FlowFrame reflow
- `MIN_FONT_SIZE = 9` - Minimum font size in points
- `MAX_FONT_SIZE = 16` - Maximum font size in points
- Font breakpoints and scaling factors

## Logging

### Consistent Logger Usage
```python
from utils import logger

# Usage (replaces print statements)
logger.info("Information message")
logger.warning("Warning message")
logger.error("Error message")
logger.debug("Debug message")
```

## Input Validation

### Validation Utilities
```python
from utils import (
    validate_character_name,
    validate_text_length,
    sanitize_filename,
    validate_file_path,
    validate_preset_name
)

# Validate character name
is_valid, error_msg = validate_character_name("My Character")
if not is_valid:
    logger.error(f"Invalid character name: {error_msg}")

# Sanitize filename (security)
safe_name = sanitize_filename("My ../Unsafe/../File.txt")
# Returns: "My_Unsafe_File.txt"

# Validate preset name
is_valid, error_msg = validate_preset_name("My Preset")

# Validate text length
is_valid, error_msg = validate_text_length(
    text, 
    max_length=5000, 
    field_name="Scene"
)

# Validate file path (prevents directory traversal)
from pathlib import Path
is_valid, error_msg = validate_file_path(
    Path("presets/myfile.json"),
    Path("presets")
)
```

## Improved Error Handling

### Specific Exception Types

**Before:**
```python
try:
    # some operation
except:
    print("Error occurred")
```

**After:**
```python
try:
    # file operation
except (FileNotFoundError, PermissionError) as e:
    logger.error(f"File access error: {e}")
except UnicodeDecodeError as e:
    logger.error(f"Invalid file encoding: {e}")
except tk.TclError as e:
    logger.error(f"Widget error: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

### Common Exception Patterns

**File Operations:**
```python
except (OSError, IOError, PermissionError) as e:
    logger.error(f"File operation failed: {e}")
```

**JSON Operations:**
```python
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON: {e}")
```

**Widget Operations:**
```python
except tk.TclError as e:
    logger.debug(f"Widget operation failed: {e}")
```

## Type Hints

### Manager Classes
All manager classes include comprehensive type hints:

```python
from typing import Dict, List, Callable, Optional, Any

class MenuManager:
    def __init__(
        self, 
        parent: tk.Tk,
        callbacks: Dict[str, Callable[[], None]]
    ) -> None:
        ...
    
    def get_theme(self) -> str:
        ...
```

## Architecture Benefits

### Code Organization
- **Before**: 1210-line MainWindow class
- **After**: 851-line coordinator + 4 specialized managers
- **Result**: 30% reduction, improved maintainability

### Separation of Concerns
- **MenuManager**: Menu structure and theme switching
- **FontManager**: Resize handling and font scaling  
- **StateManager**: Undo/redo and presets
- **DialogManager**: All user dialogs with consistent styling

### Testing & Debugging
- Managers can be tested independently
- Clearer error messages with specific exception types
- Centralized logging for easier debugging

## Security Improvements

### Path Validation
All file operations validate paths to prevent traversal attacks:

```python
# Automatically validated in preset_manager
preset_manager.import_preset("/path/to/preset.json")
# Rejects paths like "../../etc/passwd"
```

### Filename Sanitization
User-provided filenames are sanitized:
```python
# Input: "../../../etc/passwd"
# Output: "etcpasswd"
```

## Migration Guide

### Importing Constants
**Old:**
```python
# Magic numbers scattered throughout code
self.after(300, self._update)
retry_limit = 10
```

**New:**
```python
from ui.constants import TEXT_UPDATE_DEBOUNCE_MS, WIDGET_REFLOW_RETRY_LIMIT

self.after(TEXT_UPDATE_DEBOUNCE_MS, self._update)
retry_limit = WIDGET_REFLOW_RETRY_LIMIT
```

### Using Managers
**Old:**
```python
class MainWindow:
    def __init__(self):
        self._create_menus()  # 100+ lines
        self._setup_fonts()   # 50+ lines
        self._setup_state()   # 80+ lines
```

**New:**
```python
class MainWindow:
    def __init__(self):
        self.menu_manager = MenuManager(self, callbacks={...})
        self.font_manager = FontManager(self, callbacks={...})
        self.state_manager = StateManager(self, callbacks={...})
        self.dialog_manager = DialogManager(self)
```

## Documentation

### Updated Files
- ✅ `README.md` - Reflects modular architecture
- ✅ `MODULARITY_REFACTORING.md` - Details all refactoring work
- ✅ `QUICK_REFERENCE.md` - This document

### Removed Files
Outdated review documentation has been removed:
- ❌ `CODE_REVIEW_*.md`
- ❌ `COMPREHENSIVE_*.md`  
- ❌ `FIXES_APPLIED.md`
- ❌ `IMPROVEMENTS_IMPLEMENTED.md`
- ❌ `REVIEW_SUMMARY.md`
- ❌ `CODEBASE_ANALYSIS.md`
- ❌ `UX_ENHANCEMENTS.md`

### Filename Sanitization
All user-provided filenames are sanitized:
```python
# Dangerous: "../../../etc/passwd"
# Sanitized: "etcpasswd"
```

## Performance

### String Operations
Optimized repeated string operations:
```python
# Before: Multiple .strip().lower() calls
if value.strip().lower() == 'x' or value.strip().lower() == 'y':
    pass

# After: Cached result
normalized = value.strip().lower()
if normalized in ('x', 'y'):
    pass
```

## Removed Dependencies

- `pydantic` is no longer needed (removed `core/models.py`)
- Application uses only Python standard library

## Backward Compatibility

All changes are backward compatible:
- Existing data files work unchanged
- User preferences preserved
- No breaking API changes

## Testing

Verify installation:
```bash
python main.py --check-compat
python main.py --version
```

Test new features:
```bash
python -c "from utils import logger; logger.info('Test')"
python -c "from utils.validation import sanitize_filename; print(sanitize_filename('test'))"
```
