# WhatsApp Logger for ansari-whatsapp
"""Logging configuration for the WhatsApp service using Loguru.

This module configures the global Loguru logger once at import time.
All other modules should simply use: from loguru import logger
"""

import os
import sys
from typing import Any, Callable

from loguru import logger

from ansari_whatsapp.utils.config import get_settings

# =============================================================================
# Module-level logger configuration (runs once when first imported)
# =============================================================================

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Remove default handler
logger.remove()

# Get settings once
settings = get_settings()

# Determine name format based on deployment type
# Use file name only for local deployment, as it can be ctrl+clicked by VSCode
#   E.g.: whatsapp_presenter:56
if settings.DEPLOYMENT_TYPE == "local":
    name_format = "{file}"
else:
    # Use full module name for non-local deployments
    #   E.g.: ansari_whatsapp.utils.whatsapp_logger:56
    name_format = "{name}"


# Filter for test files only (when LOG_TEST_FILES_ONLY is True)
def test_file_filter(record):
    """Only log from test files when LOG_TEST_FILES_ONLY is enabled."""
    if not settings.LOG_TEST_FILES_ONLY:
        return True  # Allow all logs
    # Only log from test files
    return "tests" in record["file"].path or "test_" in record["file"].name


# Add console handler for terminal output
logger.add(
    sys.stdout,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <4}</level> | "
        f"<cyan>{name_format}</cyan>:<cyan>{{line}}</cyan> "
        "<blue>[{function}()]</blue> | "
        "<level>{message}</level>"
    ),
    level=settings.LOGGING_LEVEL.upper(),
    enqueue=True,
    colorize=True,
    backtrace=True,
    diagnose=settings.DEPLOYMENT_TYPE == "local",
    filter=test_file_filter,
    catch=False,
)

# Add file logging (when local deployment)
if settings.DEPLOYMENT_TYPE == "local":
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)

    # Create a custom sink that routes logs to module-specific files
    _file_handlers = {}  # Cache file handlers

    def module_specific_sink(message):
        """Custom sink that writes to different files based on module name."""
        record = message.record
        module_name = record["name"]

        # Apply test file filter
        if not test_file_filter(record):
            return

        # Get or create file handler for this module
        if module_name not in _file_handlers:
            log_file = os.path.join(log_dir, f"{module_name}.log")
            _file_handlers[module_name] = open(log_file, "a", encoding="utf-8")

        # Format and write the log message
        file_handle = _file_handlers[module_name]
        timestamp = record["time"].strftime("%Y-%m-%d %H:%M:%S")
        level = record["level"].name.ljust(8)
        file_info = f"{record['file'].name}:{record['line']}"
        func = record["function"]
        msg = record["message"]

        log_line = f"{timestamp} | {level} | {file_info} [{func}()] | {msg}\n"
        file_handle.write(log_line)
        file_handle.flush()

        # Doesn't close the file handle; it will be reused later
        # Therefore, this is not suitable for long-running processes with many modules on production

    logger.add(
        module_specific_sink,
        level=settings.LOGGING_LEVEL.upper(),
        catch=False,
    )

# =============================================================================
# Exports
# =============================================================================

__all__ = ["logger", "make_error_handler"]

# =============================================================================
# Error handler factory
# =============================================================================

# Error handler factory that creates context-specific error handlers
def make_error_handler(context: str, default_return: dict | Any = None) -> Callable:
    """Create a context-specific error handler.

    Args:
        context (str): Description of the operation that failed (e.g., "Error registering user")
        default_return (dict | Any): Default value to return on error

    Returns:
        callable: An error handler function that can be used with logger.catch
    """

    def error_handler(exception):
        logger.exception(f"{context}: {exception}")
        # If default_return is a dict, add the error message to it
        if isinstance(default_return, dict) and "error" not in default_return:
            result = default_return.copy()
            result["error"] = str(exception)
            return result
        # Otherwise, just return the default value
        else:
            return default_return

    return error_handler
