# -*- coding: utf-8 -*-
"""Specialized logger for session-based prompt auditing and LLM interactions."""

import os
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional
from utils.logger import logger

class AuditLogger:
    """Manages session-based logging for batch generation and AI audits."""

    def __init__(self, session_name: Optional[str] = None):
        """Initialize a new audit session.
        
        Args:
            session_name: Optional custom prefix for the session folder.
        """
        self.base_dir = Path(__file__).parent.parent.parent / "output" / "logs"
        self.timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # Create a unique session directory
        prefix = f"{session_name}_" if session_name else ""
        self.session_id = f"{prefix}{self.timestamp}"
        self.session_dir = self.base_dir / "sessions" / self.session_id
        
        self.chat_dir = self.session_dir / "chats"
        self.report_dir = self.session_dir / "reports"
        
        self._initialized = False

    def _ensure_init(self):
        """Lazy creation of directories."""
        if not self._initialized:
            self.chat_dir.mkdir(parents=True, exist_ok=True)
            self.report_dir.mkdir(parents=True, exist_ok=True)
            self._initialized = True
            logger.info(f"Audit Session started: {self.session_id}")

    def log_chat(self, label: str, system: str, prompt: str, response: str):
        """Save a full LLM interaction to a text file.
        
        Args:
            label: Descriptive name (e.g., 'critic_audit', 'enhance')
            system: The system prompt used
            prompt: The user prompt sent
            response: The AI response received
        """
        self._ensure_init()
        
        # Use a high-precision timestamp for filenames to avoid collisions
        sub_ts = int(time.time() * 1000) % 100000
        filename = f"{label}_{sub_ts}.txt"
        path = self.chat_dir / filename
        
        content = (
            f"=== SYSTEM ===\n{system}\n\n"
            f"=== PROMPT ===\n{prompt}\n\n"
            f"=== RESPONSE ===\n{response}\n"
        )
        
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Failed to log chat to {path}: {e}")

    def log_json(self, filename: str, data: Any):
        """Save structured data to a JSON file in the reports directory.
        
        Args:
            filename: Base filename (e.g., 'batch_results')
            data: Any JSON-serializable object
        """
        self._ensure_init()
        
        if not filename.endswith(".json"):
            filename += ".json"
            
        path = self.report_dir / filename
        
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            logger.debug(f"Audit report saved: {path.name}")
        except Exception as e:
            logger.error(f"Failed to save JSON report to {path}: {e}")

    def log_event(self, message: str, level: str = "info"):
        """Log a generic event to both console and a session-specific log file."""
        self._ensure_init()
        
        # Log to the main app logger
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(message)
        
        # Also append to a session.log file
        log_path = self.session_dir / "session.log"
        ts = time.strftime("%H:%M:%S")
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{ts}] {level.upper()}: {message}\n")
        except Exception:
            pass

# Create a singleton-like instance for global use if needed, 
# though AutomationController should ideally manage its own sessions.
default_audit_logger = AuditLogger(session_name="global")
