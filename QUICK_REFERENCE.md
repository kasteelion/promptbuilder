# Quick Reference: New Features & Improvements

## New Utilities

### Logging
```python
from utils import logger

# Usage
logger.info("Information message")
logger.warning("Warning message")
logger.error("Error message")
logger.debug("Debug message")
```

### Input Validation
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
    print(f"Invalid: {error_msg}")

# Sanitize filename
safe_name = sanitize_filename("My ../Unsafe/../File.txt")
# Returns: "My_Unsafe_File.txt"

# Validate preset name
is_valid, error_msg = validate_preset_name("My Preset")

# Validate text length
is_valid, error_msg = validate_text_length(text, max_length=5000, field_name="Scene")

# Validate file path (security)
from pathlib import Path
is_valid, error_msg = validate_file_path(
    Path("presets/myfile.json"),
    Path("presets")
)
```

## Improved Error Handling

### Before
```python
try:
    # some operation
except Exception as e:
    print(f"Error: {e}")
```

### After
```python
try:
    # some operation
except (FileNotFoundError, PermissionError) as e:
    logger.error(f"Error loading file: {e}")
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON format: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

## Type Hints

### PromptBuilder
```python
from typing import Dict, List, Any

builder = PromptBuilder(
    characters: Dict[str, Any],
    base_prompts: Dict[str, str],
    poses: Dict[str, Dict[str, str]]
)

prompt: str = builder.generate(config: Dict[str, Any])
```

## Configuration Constants

New constants in `config.py`:
- `FLOW_FRAME_MIN_WIDTH_THRESHOLD = 10`
- `FLOW_FRAME_REFLOW_DELAY_MS = 50`

## Security

### Path Validation
All file operations now validate paths to prevent traversal attacks:
```python
# Automatically validated in preset_manager
preset_manager.import_preset("/path/to/preset.json")
# Will reject paths like "../../etc/passwd"
```

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
