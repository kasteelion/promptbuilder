"""File operation utilities with atomic writes and backups."""

import shutil
import tempfile
from pathlib import Path
from typing import Optional


def atomic_write(filepath: Path, content: str, encoding: str = 'utf-8', create_backup: bool = True) -> bool:
    """Write file atomically to prevent corruption.
    
    Writes to a temporary file first, then renames it to the target path.
    This ensures the target file is never left in a half-written state.
    
    Args:
        filepath: Target file path
        content: Content to write
        encoding: Text encoding to use
        create_backup: Whether to create a backup of existing file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        filepath = Path(filepath)
        
        # Create backup if file exists and backup is requested
        if create_backup and filepath.exists():
            backup_path = filepath.with_suffix(filepath.suffix + '.bak')
            try:
                shutil.copy2(filepath, backup_path)
            except (IOError, OSError) as e:
                # Backup failed, but continue with write
                from utils import logger
                logger.debug(f"Backup failed for {filepath}: {e}")
        
        # Write to temporary file in same directory
        # (ensures same filesystem for atomic rename)
        temp_fd, temp_path = tempfile.mkstemp(
            dir=filepath.parent,
            prefix=f'.{filepath.name}.',
            suffix='.tmp',
            text=True
        )
        
        try:
            # Write content to temp file
            with open(temp_fd, 'w', encoding=encoding) as f:
                f.write(content)
            
            # Atomic rename (POSIX) or replace (Windows)
            temp_path_obj = Path(temp_path)
            temp_path_obj.replace(filepath)
            
            return True
            
        except Exception as e:
            # Clean up temp file on error
            try:
                Path(temp_path).unlink(missing_ok=True)
            except (OSError, PermissionError):
                    # Could not delete temp file; log for diagnostics
                    from utils import logger
                    logger.debug(f"Could not delete temp file {temp_path}: {e}")
            raise e
            
    except Exception as e:
        from utils import logger
        logger.error(f"Atomic write failed for {filepath}: {e}")
        return False


def safe_read(filepath: Path, encoding: str = 'utf-8', max_size_mb: int = 10) -> Optional[str]:
    """Safely read a file with size limit validation.
    
    Args:
        filepath: File to read
        encoding: Text encoding
        max_size_mb: Maximum file size in MB
        
    Returns:
        File content or None if error/too large
    """
    try:
        filepath = Path(filepath)
        
        # Check file size before reading
        size_bytes = filepath.stat().st_size
        max_bytes = max_size_mb * 1024 * 1024
        
        if size_bytes > max_bytes:
            from utils import logger
            logger.warning(f"File too large: {filepath} ({size_bytes} bytes > {max_bytes} bytes)")
            return None
        
        return filepath.read_text(encoding=encoding)
        
    except Exception as e:
        from utils import logger
        logger.error(f"Safe read failed for {filepath}: {e}")
        return None


def create_backup(filepath: Path, max_backups: int = 5) -> Optional[Path]:
    """Create numbered backup of file.
    
    Args:
        filepath: File to backup
        max_backups: Maximum number of backups to keep
        
    Returns:
        Path to backup file or None if failed
    """
    try:
        filepath = Path(filepath)
        
        if not filepath.exists():
            return None
        
        # Find next backup number
        backup_dir = filepath.parent / '.backups'
        backup_dir.mkdir(exist_ok=True)
        
        # Get existing backups
        existing = list(backup_dir.glob(f'{filepath.stem}.*.bak'))
        
        # Find next number
        next_num = 1
        if existing:
            numbers = []
            for backup in existing:
                try:
                    num = int(backup.stem.split('.')[-1])
                    numbers.append(num)
                except (ValueError, IndexError):
                    pass
            if numbers:
                next_num = max(numbers) + 1
        
        # Create new backup
        backup_path = backup_dir / f'{filepath.stem}.{next_num:03d}.bak'
        shutil.copy2(filepath, backup_path)
        
        # Remove old backups if exceeding limit
        existing = sorted(backup_dir.glob(f'{filepath.stem}.*.bak'), 
                         key=lambda p: p.stat().st_mtime)
        while len(existing) > max_backups:
            oldest = existing.pop(0)
            try:
                oldest.unlink()
            except (OSError, PermissionError) as e:
                from utils import logger
                logger.debug(f"Could not delete old backup {oldest}: {e}")
        
        return backup_path
        
    except Exception as e:
        from utils import logger
        logger.error(f"Backup creation failed for {filepath}: {e}")
        return None
