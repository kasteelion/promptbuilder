"""Debug logging utility for crash diagnostics."""
import os
import sys
from datetime import datetime

_log_file = "promptbuilder_debug.log"
_log_handle = None

def init_debug_log():
    """Initialize debug logging. Deletes old log and creates new one."""
    global _log_handle
    
    # Delete old log if exists
    if os.path.exists(_log_file):
        try:
            os.remove(_log_file)
        except (OSError, PermissionError) as e:
            # Log deletion failure is non-critical; file will be overwritten
            print(f"Warning: Could not delete old debug log: {e}")
    
    # Create new log
    try:
        _log_handle = open(_log_file, 'w', encoding='utf-8')
        log(f"=== Debug Log Started: {datetime.now()} ===")
        log(f"Python: {sys.version}")
        log(f"Platform: {sys.platform}")
        log("=" * 60)
    except Exception as e:
        print(f"Warning: Could not create debug log: {e}")

def log(message):
    """Write a log message to the debug file and console."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    log_line = f"[{timestamp}] {message}"
    
    # Write to console
    print(log_line, flush=True)
    
    # Write to file
    if _log_handle:
        try:
            _log_handle.write(log_line + "\n")
            _log_handle.flush()
        except (OSError, ValueError) as e:
            # File handle may be closed or invalid; continue to console output
            print(f"Warning: Could not write to debug log: {e}")

def close_debug_log():
    """Close debug log file."""
    global _log_handle
    if _log_handle:
        try:
            log("=== Debug Log Ended ===")
            _log_handle.close()
        except (OSError, ValueError) as e:
            # Log close failure is non-critical at shutdown
            print(f"Warning: Could not close debug log cleanly: {e}")
        _log_handle = None
