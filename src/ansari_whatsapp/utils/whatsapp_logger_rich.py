# WhatsApp Logger for ansari-whatsapp
"""Logging configuration for the WhatsApp service using Python's standard logging with Rich handler integration."""

import functools
import logging
import os
import re
import sys
import time
import traceback
from typing import Any, Callable, Dict, Optional, TypeVar, cast

from rich.console import Console
from rich.logging import RichHandler
from rich.style import Style
from rich.theme import Theme
from rich.text import Text
from rich.traceback import install as install_rich_traceback

from ansari_whatsapp.utils.config import get_settings

# Type variable for generic function types
F = TypeVar("F", bound=Callable[..., Any])

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Install rich traceback handler globally
install_rich_traceback(
    show_locals=True,
    max_frames=10,
    suppress=[],
    width=None,
    word_wrap=True,
)

# Define log level colors
LOG_LEVEL_COLORS = {
    "DEBUG": "cyan",
    "INFO": "white",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold red",
}


class ColoredRichHandler(RichHandler):
    """Custom Rich handler that colors the message text based on log level."""

    def render_message(self, record: logging.LogRecord, message: str) -> Text:
        """Override the render_message method to color the message based on level."""
        level_name = record.levelname
        color = LOG_LEVEL_COLORS.get(level_name, "white")
        return Text.from_markup(message, style=Style(color=color))


def create_file_handler(name: str, logging_level: str) -> logging.FileHandler:
    """Creates and configures a file handler for logging.

    Args:
        name (str): The name of the module for the log file.
        logging_level (str): The logging level to set for the handler.

    Returns:
        logging.FileHandler: Configured file handler instance.
    """
    # Ensure logs directory exists
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"{name.replace('.', '_')}.log")
    file_handler = logging.FileHandler(
        filename=log_file,
        mode="a",  # Append mode
        encoding="utf-8",  # Use UTF-8 encoding to support Unicode characters
    )
    file_handler.setLevel(logging_level)

    # Custom formatter for files with forward slashes and function name in square brackets
    class VSCodePathFormatter(logging.Formatter):
        # ANSI color code regex pattern
        ANSI_ESCAPE_PATTERN = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

        def format(self, record):
            # Format path with forward slashes and function name in square brackets
            path_format = f"{record.name.replace('.','/')}:{record.lineno} [{record.funcName}()]"

            # Format time without milliseconds
            # Override the default formatTime to remove milliseconds
            created = self.converter(record.created)
            time_format = time.strftime("%Y-%m-%d %H:%M:%S", created)

            # Get the message and strip any ANSI color codes
            message = record.getMessage()
            clean_message = self.ANSI_ESCAPE_PATTERN.sub("", message)

            # Combine everything
            return f"{time_format} | {record.levelname} | {path_format} | {clean_message}"

    # Use the custom formatter for files
    file_formatter = VSCodePathFormatter()
    file_handler.setFormatter(file_formatter)
    return file_handler


class LoggerWithCatch(logging.Logger):
    """Extended Logger class that includes a catch decorator similar to loguru's."""

    def catch(
        self,
        exception=Exception,
        *,
        level="ERROR",
        reraise=False,
        message="An error occurred during execution of {function}",
        onerror=None,
        exclude=None,
    ):
        """Decorator that catches exceptions from the decorated function.

        Args:
            exception: The exception(s) to catch
            level: The logging level for caught exceptions
            reraise: Whether to reraise the exception after logging
            message: The message format to use for the log
            onerror: Optional callback to call on error
            exclude: Exception types to exclude from catching

        Returns:
            Decorated function that catches and logs exceptions
        """
        if exclude is None:
            exclude = []

        def decorator(func: F) -> F:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except exception as e:
                    if any(isinstance(e, exc) for exc in exclude):
                        raise

                    # Format the function name for the log message
                    func_name = f"{func.__module__}.{func.__name__}"
                    formatted_message = message.format(function=func_name)

                    # Log the exception with traceback
                    self.log(level=getattr(logging, level), msg=formatted_message, exc_info=True)

                    # Call the onerror callback if provided
                    if onerror is not None:
                        onerror(e)

                    # Reraise the exception if requested
                    if reraise:
                        raise

            return cast(F, wrapper)

        return decorator


# Register our custom logger class
logging.setLoggerClass(LoggerWithCatch)


def get_logger(name: str) -> LoggerWithCatch:
    """Creates and returns a logger instance for the specified module.

    Args:
        name (str): The name of the module requesting the logger (typically __name__).

    Returns:
        LoggerWithCatch: Configured logger instance with catch method.
    """
    # Default to INFO if settings are not available
    settings = get_settings()
    logging_level = settings.LOGGING_LEVEL.upper() if hasattr(settings, "LOGGING_LEVEL") else "INFO"

    # Create a Rich console for logging
    console = Console(
        highlight=True,  # Syntax highlighting
        markup=True,  # Enable Rich markup
        log_path=False,  # Don't write to a log file directly - we'll handle that separately
        log_time_format="%Y-%m-%d %H:%M:%S",
    )

    # Create a logger
    logger = logging.getLogger(name)
    # Ensure it's an instance of our custom class
    if not isinstance(logger, LoggerWithCatch):
        logger.__class__ = LoggerWithCatch

    # Clear any existing handlers to avoid duplicate logs
    if logger.handlers:
        logger.handlers.clear()

    # Set the logging level
    logger.setLevel(logging_level)

    # Use our custom ColoredRichHandler instead of the standard RichHandler
    rich_handler = ColoredRichHandler(
        console=console,
        enable_link_path=False,
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        show_time=True,
        show_level=True,
        show_path=True,
    )
    rich_handler.setLevel(logging_level)

    # Add the Rich handler to the logger
    logger.addHandler(rich_handler)

    # Add file handler
    file_handler = create_file_handler(name, logging_level)
    logger.addHandler(file_handler)

    return cast(LoggerWithCatch, logger)
