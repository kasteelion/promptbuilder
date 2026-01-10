# -*- coding: utf-8 -*-
"""Backup utility for PromptBuilder data."""

import shutil
import datetime
from pathlib import Path
from typing import Tuple, Optional

def create_snapshot(base_dir: Path) -> Tuple[bool, str]:
    """Create a timestamped backup of the data/ directory.
    
    Args:
        base_dir: Project root directory
        
    Returns:
        (success, message)
    """
    data_dir = base_dir / "data"
    if not data_dir.exists():
        return False, f"Data directory not found at {data_dir}"
        
    backup_dir = base_dir / "backups"
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"promptbuilder_data_{timestamp}"
    archive_path = backup_dir / archive_name
    
    try:
        # Create a zip archive
        shutil.make_archive(str(archive_path), 'zip', str(data_dir))
        return True, f"Snapshot created: {archive_name}.zip"
    except Exception as e:
        return False, f"Failed to create snapshot: {e}"

def list_snapshots(base_dir: Path) -> list:
    """List available snapshots in the backups/ directory."""
    backup_dir = base_dir / "backups"
    if not backup_dir.exists():
        return []
        
    return sorted(list(backup_dir.glob("*.zip")), key=lambda x: x.stat().st_mtime, reverse=True)
