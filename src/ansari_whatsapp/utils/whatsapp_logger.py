# WhatsApp Logger for ansari-whatsapp
"""Logging configuration for the WhatsApp service using Loguru."""

import os
import sys
from typing import Any, Callable

from loguru import logger

from ansari_whatsapp.utils.config import get_settings

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Track which modules have already been configured to avoid duplicate handlers
_configured_modules = set()


def get_logger(name: str):
    """Creates and returns a module-specific logger instance.

    Args:
        name (str): The name of the module requesting the logger (typically __name__).

    Returns:
        A bound loguru logger instance configured for the specific module.
    """
    # Only configure handlers once per module
    if name in _configured_modules:
        return logger.bind(name=name)

    _configured_modules.add(name)

    # Create a module-specific logger by binding the name
    module_logger = logger.bind(name=name)

    # Get settings
    settings = get_settings()

    # Use file name only for local deployment, as it can be ctrl+clicked by VSCode
    #   E.g.: whatsapp_presenter:56
    if settings.DEPLOYMENT_TYPE == "local":
        name_format = "{file}"
    else:
        # Use full module name for non-local deployments
        #   E.g.: ansari_whatsapp.utils.whatsapp_logger:56
        name_format = "{name}"

    # Combined filter for all handlers
    def log_filter(record):
        """
        Filter logs based on module specificity and test file settings.

        Args:
            record: The log record being processed.
        """
        # Filter 1: Module-specific filtering (so that each handler only logs its own module's messages to terminal/file)
        #   I.e., if the current logger's `name` is not the same as the record's `name`, filter it out
        filter_1 = record.get("extra", {}).get("name", "") != name

        # Filter 2: Test files only (when LOG_TEST_FILES_ONLY is True)
        #  I.e., if LOG_TEST_FILES_ONLY is True, only allow logs from files in "tests" folder or files starting with "test_"
        filter_2 = settings.LOG_TEST_FILES_ONLY and not (
            "tests" in record["file"].path or "test_" in record["file"].name
        )

        if filter_1 or filter_2:
            return False

        return True

    # Add console handler for terminal output
    module_logger.add(
        sys.stderr,
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
        filter=log_filter,
        catch=False,
    )

    # Add file logging for test files (when enabled)
    if settings.DEPLOYMENT_TYPE == "local":
        # Define log file path for this specific module
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        module_log_file = os.path.join(log_dir, f"{name.replace('.', '_')}.log")
        module_logger.add(
            module_log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {file}:{line} [{function}()] | {message}",
            level=settings.LOGGING_LEVEL.upper(),
            backtrace=False,
            diagnose=False,
            filter=log_filter,
            rotation="10 MB",
            catch=False,
        )

        # Make it log to `all_logs.log` as well
        all_logs_file = os.path.join(log_dir, "all_logs.log")
        module_logger.add(
            all_logs_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {file}:{line} [{function}()] | {message}",
            level=settings.LOGGING_LEVEL.upper(),
            enqueue=True,
            backtrace=False,
            diagnose=False,
            filter=log_filter,
            rotation="10 MB",
            catch=False,
        )


    return module_logger

# Error handler factory that creates context-specific error handlers
# NOTE: This function is deprecated in favor of explicit try-except blocks with custom exceptions.
# It remains here for backward compatibility with any remaining @logger.catch decorators.
def make_error_handler(context: str) -> Callable:
    """Create a context-specific error handler (DEPRECATED).

    This function is deprecated. Use explicit try-except blocks with custom exceptions instead.

    Args:
        context (str): Description of the operation that failed (e.g., "Error registering user")

    Returns:
        callable: An error handler function that can be used with logger.catch
    """

    def error_handler(exception):
        exception_msg = str(exception)
        # NOTE: Loguru's exception method automatically includes the stack trace after the message
        logger.exception(f"{context}: {exception_msg}")
        return

    return error_handler
