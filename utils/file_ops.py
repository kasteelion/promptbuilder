"""File operation utilities with atomic writes and backups.

Safe helpers for atomic file writing, size-checked reads, and creating
numbered backups. This module keeps implementations simple and
robust so the rest of the project can rely on predictable behavior.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional


def atomic_write(
    filepath: Path, content: str, encoding: str = "utf-8", create_backup: bool = True
) -> bool:
    """Write file atomically to prevent corruption.

    Writes to a temporary file in the same directory and then replaces the
    target path. If requested, a simple .bak backup copy is created first.

    Returns True on success, False on error (exceptions are logged).
    """
    try:
        filepath = Path(filepath)

        # Create backup if file exists and backup is requested
        if create_backup and filepath.exists():
            backup_path = filepath.with_suffix(filepath.suffix + ".bak")
            try:
                shutil.copy2(filepath, backup_path)
            except (IOError, OSError) as e:
                from utils import logger

                logger.debug(f"Backup failed for {filepath}: {e}")

        # Create a temp file in the same directory to allow atomic replace
        temp_fd, temp_path = tempfile.mkstemp(
            dir=str(filepath.parent), prefix=f".{filepath.name}.", suffix=".tmp"
        )
        try:
            # Use os.fdopen to write using the returned file descriptor
            with os.fdopen(temp_fd, "w", encoding=encoding) as f:
                f.write(content)

            # Replace target atomically
            Path(temp_path).replace(filepath)
            return True
        except Exception:
            from utils import logger

            logger.exception("Auto-captured exception")
            # Clean up temp file on error
            try:
                Path(temp_path).unlink(missing_ok=True)
            except Exception as unlink_err:
                from utils import logger

                logger.debug(f"Could not delete temp file {temp_path}: {unlink_err}")
            raise
    except Exception:
        from utils import logger

        logger.exception(f"Atomic write failed for {filepath}")
        return False


def safe_read(filepath: Path, encoding: str = "utf-8", max_size_mb: int = 10) -> Optional[str]:
    """Safely read a file with size limit validation.

    Returns the file content or None if the file is too large or an error
    occurred (exceptions are logged).
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
    except Exception:
        from utils import logger

        logger.exception(f"Safe read failed for {filepath}")
        return None


def create_backup(filepath: Path, max_backups: int = 5) -> Optional[Path]:
    """Create numbered backup of file.

    Backups are stored in a `.backups` directory next to the file and are
    named `{stem}.{nnn}.bak`. Older backups are removed when exceeding
    `max_backups`.
    """
    try:
        filepath = Path(filepath)

        if not filepath.exists():
            return None

        # Find next backup number
        backup_dir = filepath.parent / ".backups"
        backup_dir.mkdir(exist_ok=True)

        existing = list(backup_dir.glob(f"{filepath.stem}.*.bak"))

        next_num = 1
        if existing:
            numbers = []
            for backup in existing:
                try:
                    num = int(backup.stem.split(".")[-1])
                    numbers.append(num)
                except (ValueError, IndexError):
                    pass
            if numbers:
                next_num = max(numbers) + 1

        backup_path = backup_dir / f"{filepath.stem}.{next_num:03d}.bak"
        shutil.copy2(filepath, backup_path)

        # Prune old backups
        existing = sorted(
            backup_dir.glob(f"{filepath.stem}.*.bak"), key=lambda p: p.stat().st_mtime
        )
        while len(existing) > max_backups:
            oldest = existing.pop(0)
            try:
                oldest.unlink()
            except (OSError, PermissionError) as e:
                from utils import logger

                logger.debug(f"Could not delete old backup {oldest}: {e}")

        return backup_path
    except Exception:
        from utils import logger

        logger.exception(f"Backup creation failed for {filepath}")
        return None
