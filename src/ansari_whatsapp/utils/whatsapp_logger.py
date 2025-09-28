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


# TODO soon: Remove this function in an upcoming commit
# NOTE: It will get removed, as loguru doesn't support the following corner case:
#   * You log a message which contains a dict-like string (e.g., "this -> {'hi':1}")
#   * So it will raise (KeyError: "'hi'")
# # Define a formatter function that handles the file path formatting
def _formatter(record):
    """Format a log record with custom styling and layout.

    Example of a loguru record:
    {
        'elapsed': datetime.timedelta(microseconds=127166),
        'exception': None,
        'extra': {'name': 'module_name'},
        'file': {'name': 'file.py', 'path': 'path/to/file.py'},
        'function': '<module>' if module-level code, else 'function name',
        'level': {'name': 'DEBUG', 'no': 10, 'icon': '🐞'},
        'line': 42,
        'message': 'Example log message',
        'module': 'file',
        'name': 'module_name',
        'process': {'id': 12345, 'name': 'MainProcess'},
        'thread': {'id': 67890, 'name': 'MainThread'},
        'time': datetime(2025, 4, 29, 8, 7, 42, 126258, tzinfo=timezone)
    }
    """
    r_time = record["time"]
    r_level = record["level"]
    r_name = record["name"]
    r_file = record["file"]
    r_line = record["line"]
    r_function = record["function"]
    r_message = record["message"]

    # Format the time with green color
    time_str = f"<green>{r_time.strftime('%Y-%m-%d %H:%M:%S')}</green>"

    # Format the level with its own color
    level_str = f"<level>{r_level.name: <4}</level>"

    # Format the module/file name
    if get_settings().DEPLOYMENT_TYPE == "local":
        # file_details = r_file.path if r_level.no >= 40 else r_file.name  # 40 == ERROR
        file_details = r_file.name
        location_str = f"<cyan>{file_details}</cyan>:<cyan>{r_line}</cyan>"
    else:
        # Format like: ansari_whatsapp.presenters.whatsapp_presenter:156
        location_str = f"<cyan>{r_name}</cyan>:<cyan>{r_line}</cyan>"

    # Format the function name with blue color
    if r_function == "<module>":
        # Escape angle brackets for module-level code
        function_str = "<blue>[\\<module-code>]</blue>"
    else:
        function_str = f"<blue>[{r_function}()]</blue>"

    # Format the message with level color
    r_message = repr(r_message)
    # VVV THIS WILL RAISE KeyError IF IT CONTAINS A DICT-LIKE STRING VVV
    message_str = f"<level>{r_message}</level>"

    # Return the complete formatted string
    return f"{time_str} | {level_str} | {location_str} {function_str} | {message_str}\n"


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
        if isinstance(default_return, dict) and "error" not in default_return:
            result = default_return.copy()
            result["error"] = str(exception)
            return result
        else:
            return default_return

    return error_handler
