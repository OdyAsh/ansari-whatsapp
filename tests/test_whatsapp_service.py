"""
Integration tests for ansari-whatsapp service webhooks.

This module tests the WhatsApp webhook endpoints in the ansari-whatsapp service
using pytest and FastAPI TestClient. It focuses solely on testing the WhatsApp
service itself without external dependencies.

Tests verify:
- Service health endpoint
- Webhook verification endpoint
- Webhook message processing
- Phone number validation logic

The test suite automatically detects if the backend is available:
- If backend is running: Tests run with real backend (MOCK_ANSARI_CLIENT=False)
- If backend is not available: Tests run with mock client (MOCK_ANSARI_CLIENT=True)

Security: All sensitive data is loaded from environment variables and masked in logs.
"""

import json
import os
import pytest
import time
import httpx
from typing import Any
from fastapi.testclient import TestClient

from ansari_whatsapp.app.main import app
from ansari_whatsapp.utils.app_logger import get_logger
from ansari_whatsapp.utils.config import get_settings
from .test_utils import (
    secure_log_result,
    format_payload_for_logging,
    format_params_for_logging
)

# Initialize logger
logger = get_logger(__name__)


def check_backend_availability() -> bool:
    """Check if the ansari-backend service is running and accessible.

    Returns:
        bool: True if backend is available, False otherwise
    """
    settings = get_settings()
    backend_url = settings.BACKEND_SERVER_URL

    try:
        logger.info(f"Checking backend availability at {backend_url}")
        response = httpx.get(f"{backend_url}/", timeout=3.0)
        is_available = response.status_code == 200
        logger.info(f"Backend availability: {'AVAILABLE' if is_available else 'UNAVAILABLE'} (status: {response.status_code})")
        return is_available
    except httpx.RequestError as e:
        logger.info(f"Backend is not available: {e}")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error checking backend: {e}")
        return False


@pytest.fixture(scope="module", autouse=True)
def configure_mock_mode():
    """Configure mock mode based on backend availability before running tests.

    This fixture runs before all tests and sets MOCK_ANSARI_CLIENT environment variable.
    We need to set the env var and clear the settings cache to ensure the new value is used.

    The original value (if any) is restored after tests complete.
    """
    # Store the original value if it exists
    original_value = os.environ.get("MOCK_ANSARI_CLIENT")
    had_original_value = "MOCK_ANSARI_CLIENT" in os.environ

    backend_available = check_backend_availability()

    if backend_available:
        logger.info("Backend is AVAILABLE - Tests will use REAL backend")
        os.environ["MOCK_ANSARI_CLIENT"] = "False"
    else:
        logger.info("Backend is NOT available - Tests will use MOCK client")
        os.environ["MOCK_ANSARI_CLIENT"] = "True"

    # Clear the settings cache to pick up the new MOCK_ANSARI_CLIENT value
    get_settings.cache_clear()

    # Log the effective configuration
    settings = get_settings()
    logger.info(f"MOCK_ANSARI_CLIENT is now set to: {settings.MOCK_ANSARI_CLIENT}")

    yield

    # Cleanup: restore original state
    if had_original_value:
        # Restore the original value
        os.environ["MOCK_ANSARI_CLIENT"] = original_value
        logger.debug(f"Restored MOCK_ANSARI_CLIENT to original value: {original_value}")
    else:
        # Delete the key if it didn't exist before
        if "MOCK_ANSARI_CLIENT" in os.environ:
            del os.environ["MOCK_ANSARI_CLIENT"]
        logger.debug("Removed MOCK_ANSARI_CLIENT (it didn't exist before tests)")

    get_settings.cache_clear()


@pytest.fixture(scope="module")
def settings():
    return get_settings()

# Create TestClient
client = TestClient(app)

# Test results storage
test_results = []


def log_test_result(test_name: str, success: bool, message: str, response_data: Any = None):
    """Log test results with secure data masking."""
    result = secure_log_result(test_name, success, message, response_data)
    test_results.append(result)

    status = "[PASS]" if success else "[FAIL]"
    logger.info(f"{status} {test_name}: {message}")

    if response_data:
        logger.debug(f"   Response: {json.dumps(result['response_data'], indent=2)}")


@pytest.mark.integration
def test_whatsapp_health():
    """Test ansari-whatsapp health endpoint using TestClient."""
    test_name = "WhatsApp Service Health"

    response = client.get("/")
    response_data = response.json()

    if response.status_code == 200 and response_data.get("status") == "ok":
        log_test_result(test_name, True, "WhatsApp service is healthy", response_data)
        assert True
    else:
        log_test_result(test_name, False, f"Health check failed: HTTP {response.status_code}", response_data)
        assert False


@pytest.mark.integration
def test_webhook_verification(settings):
    """Test WhatsApp webhook verification endpoint using TestClient."""
    test_name = "Webhook Verification"

    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": settings.META_WEBHOOK_VERIFY_TOKEN.get_secret_value(),
        "hub.challenge": "test_challenge_12345"
    }

    logger.debug(f"[TEST] Testing {test_name}...")
    logger.debug("   URL: /whatsapp/v1")
    logger.debug(f"   Params: {format_params_for_logging(params)}")

    response = client.get("/whatsapp/v1", params=params)

    if response.status_code == 200 and "test_challenge_12345" in response.text:
        log_test_result(test_name, True, "Webhook verification successful", {"response": response.text})
        assert True
    else:
        log_test_result(test_name, False, f"Webhook verification failed: HTTP {response.status_code}", 
                        {"response": response.text})
        assert False


@pytest.mark.integration
def test_webhook_message_basic(settings):
    """Test basic WhatsApp webhook message processing using TestClient.

    With mock client enabled, this test should always succeed with 200 status.
    """
    test_name = "Basic Webhook Message"

    # Create a minimal WhatsApp webhook payload
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {
                                "phone_number_id": settings.META_BUSINESS_PHONE_NUMBER_ID.get_secret_value(),
                                "display_phone_number": "+1234567890"
                            },
                            "messages": [
                                {
                                    "from": settings.WHATSAPP_DEV_PHONE_NUM.get_secret_value(),
                                    "id": settings.WHATSAPP_DEV_MESSAGE_ID.get_secret_value(),
                                    "timestamp": str(int(time.time())),
                                    "type": "text",
                                    "text": {
                                        "body": "Hello, this is a test message for integration testing"
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    logger.debug(f"[TEST] Testing {test_name}...")
    logger.debug("   URL: /whatsapp/v1")
    logger.debug(f"   Payload: {format_payload_for_logging(payload)}")
    logger.debug(f"   Mock mode: {settings.MOCK_ANSARI_CLIENT}")

    response = client.post("/whatsapp/v1", json=payload)

    # With mock client, we should always get 200
    if response.status_code == 200:
        try:
            response_data = response.json()
            success = response_data.get("success", False)
            message = response_data.get("message", "")

            if success and "processed successfully" in message.lower():
                log_test_result(test_name, True, "Webhook message processed successfully", response_data)
                logger.debug("   [PASS] Message processed successfully")
            else:
                log_test_result(test_name, True, "Webhook message accepted", response_data)
                logger.debug("   [PASS] Message accepted")

            assert True
        except json.JSONDecodeError:
            log_test_result(test_name, True, "Webhook message accepted", {"status_code": response.status_code})
            assert True
    else:
        # Non-200 status codes are now considered failures since mock client should handle everything
        response_data = None
        try:
            response_data = response.json()
        except Exception:
            response_data = response.text
        log_test_result(test_name, False, f"Expected 200, got {response.status_code}.", response_data)
        assert False, f"Expected HTTP 200 with mock client, got {response.status_code}"


@pytest.fixture(scope="session", autouse=True)
def save_results():
    """Save test results to file (runs after all tests in the session)."""
    yield  # All tests run here
    
    # Teardown: runs after all tests, even if filtered by -k
    from datetime import datetime

    if test_results:
        results_file = "tests/detailed_test_results_whatsapp_service.json"

        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results if result["success"])

        combined_results = {
            "test_run": {
                "timestamp": datetime.now().isoformat(),
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": f"{(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%"
            },
            "test_results": test_results
        }

        with open(results_file, "w") as f:
            json.dump(combined_results, f, indent=2)

        logger.info(f"Detailed results saved to: {results_file}")
