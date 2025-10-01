# WhatsApp Logger for ansari-whatsapp
"""Logging configuration for the WhatsApp service using Loguru."""

import os
import sys
from typing import Any, Callable

from loguru import logger

from ansari_whatsapp.utils.config import get_settings

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Flag to track whether logger has been configured
_LOGGER_CONFIGURED = False


def configure_logger():
    """Configure global loguru logger settings. This should be called only once."""
    global _LOGGER_CONFIGURED

    # Only configure if not already done
    if _LOGGER_CONFIGURED:
        return

    # Clear any existing handlers
    logger.remove()

    # Get settings
    settings = get_settings()
    logging_level = settings.LOGGING_LEVEL.upper() if hasattr(settings, "LOGGING_LEVEL") else "INFO"

    # Use file name only for local deployment, as it can be ctrl+clicked by VSCode
    #   E.g.: whatsapp_presenter:56
    if settings.DEPLOYMENT_TYPE == "local":
        name_format = "{file}"
    else:
        # Use full module name for non-local deployments
        #   E.g.: ansari_whatsapp.utils.whatsapp_logger:56
        name_format = "{name}"

    # Add console handler with custom format
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <4}</level> | "
            f"<cyan>{name_format}</cyan>:<cyan>{{line}}</cyan> "
            "<blue>[{function}()]</blue> | "
            "<level>{message}</level>"
        ),
        level=logging_level,
        colorize=True,
        backtrace=False,
        diagnose=True,
    )

    _LOGGER_CONFIGURED = True


# Initialize the logger configuration at import time
configure_logger()


def get_logger(name: str):
    """Creates and returns a module-specific logger instance.

    Args:
        name (str): The name of the module requesting the logger (typically __name__).

    Returns:
        A bound loguru logger instance configured for the specific module.
    """
    # Ensure logger is configured (will only happen once)
    configure_logger()

    # Get settings
    settings = get_settings()

    # Define log file path for this specific module
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    module_log_file = os.path.join(log_dir, f"{name.replace('.', '_')}.log")

    if not settings.DEPLOYMENT_TYPE == "local":
        logger.bind(name=name)
        return logger

    logger.add(
        module_log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}/{module}:{line} [{function}()] | {message}",
        level=settings.LOGGING_LEVEL.upper(),
        enqueue=True,
        backtrace=True,
        diagnose=True,
        catch=False,
    )

    # Return a logger bound to the module name
    return logger.bind(name=name)


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
