"""Custom exceptions for the application."""

class AppError(Exception):
    """Base class for application exceptions."""
    pass

class DataLoadError(AppError):
    """Raised when data loading fails."""
    pass

class ParseError(AppError):
    """Raised when parsing fails."""
    pass
