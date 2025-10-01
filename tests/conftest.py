"""
Pytest configuration for ansari-whatsapp tests.

This module configures test fixtures and logging behavior using loguru.
"""

import sys
import pytest
from loguru import logger


def pytest_addoption(parser):
    """Add custom command-line options for test logging control."""
    parser.addoption(
        "--log-mode",
        action="store",
        default="full",
        choices=["full", "test-only", "minimal"],
        help=(
            "Control test logging verbosity:\n"
            "  full      - Show all logs including FastAPI/TestClient (default)\n"
            "  test-only - Show only test and ansari_whatsapp logs\n"
            "  minimal   - Show only INFO level and above"
        )
    )


@pytest.fixture(scope="session", autouse=True)
def configure_test_logging(request):
    """
    Configure loguru for test runs based on --log-mode option.

    This fixture automatically configures logging for all tests and provides
    easy toggling between different log verbosity levels.

    Usage:
        pytest tests/ -v -s                           # full logs (default)
        pytest tests/ -v -s --log-mode=test-only      # test file, not FastAPI logs
        pytest tests/ -v -s --log-mode=minimal        # minimal logs
    """
    log_mode = request.config.getoption("--log-mode")

    # Remove default loguru handler to prevent duplicate logs
    logger.remove()

    if log_mode == "full":
        # Show all logs including FastAPI, uvicorn, httpx, etc.
        logger.add(
            sys.stderr,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <4}</level> | "
                "<cyan>{name}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            ),
            level="DEBUG",
            colorize=True,
        )

    elif log_mode == "test-only":
        # Show only test files and ansari_whatsapp logs
        # Filter out FastAPI/TestClient noise
        def test_filter(record):
            """Filter to show only test-related and application logs."""
            excluded_modules = [
                # User-defined modules to exclude
                "ansari_whatsapp.app",
                "ansari_whatsapp.presenters",
                "ansari_whatsapp.utils",

                "uvicorn",      # Web server logs
                "fastapi",      # FastAPI framework logs
                "httpx",        # HTTP client logs (used by TestClient)
                "httpcore",     # Low-level HTTP logs
                "starlette",    # ASGI framework logs
                "anyio",        # Async I/O logs
            ]

            # Allow logs from test files and ansari_whatsapp modules
            return not any(excluded in record["name"] for excluded in excluded_modules)

        logger.add(
            sys.stderr,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <4}</level> | "
                "<cyan>{file}</cyan>:<cyan>{line}</cyan> "
                "<blue>[{function}()]</blue> | "
                "<level>{message}</level>"
            ),
            level="DEBUG",
            filter=test_filter,
            colorize=True,
        )

    yield

    # Cleanup after all tests complete
    logger.remove()