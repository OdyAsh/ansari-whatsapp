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

Backend Availability:
- If MOCK_ANSARI_CLIENT=True: Tests use mock client (no backend needed)
- If MOCK_ANSARI_CLIENT=False: Tests check backend availability
  - If backend is available: Tests proceed with real backend
  - If backend is NOT available: Tests terminate with error instructions

Required Environment Variables:
- META_BUSINESS_PHONE_NUMBER_ID: Your Meta business phone number ID
- WHATSAPP_DEV_PHONE_NUM: A valid WhatsApp phone number for testing
- WHATSAPP_DEV_MESSAGE_ID: A valid message ID for testing
- MOCK_ANSARI_CLIENT: True for mock mode, False for real backend
- BACKEND_SERVER_URL: URL of backend service (required if MOCK_ANSARI_CLIENT=False)

Security: All sensitive data is loaded from environment variables and masked in logs.
"""

import json
import os
import pytest
import time
import httpx
from typing import Any

from fastapi.testclient import TestClient
# This `logger` will get configured when importing `ansari_whatsapp.app.main` below, 
# as `main.py` calls `configure_logger()`
from loguru import logger

from ansari_whatsapp.app.main import app
from ansari_whatsapp.utils.config import get_settings
from .test_utils import (
    log_test_result,
    format_payload_for_logging,
    format_params_for_logging
)


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

    This fixture runs before all tests and checks the MOCK_ANSARI_CLIENT setting.
    If MOCK_ANSARI_CLIENT is True, tests will use a mock client.
    If MOCK_ANSARI_CLIENT is False, tests will check backend availability.

    If backend is not available and mock mode is disabled, tests will terminate
    with clear instructions on how to fix the issue.

    The original value (if any) is restored after tests complete.
    """
    # Get settings first to check current configuration
    settings = get_settings()

    # Log the current mock mode setting
    if settings.MOCK_ANSARI_CLIENT:
        logger.info("MOCK_ANSARI_CLIENT is True - Tests will use MOCK client")
        logger.info("Backend availability check will be skipped")
    else:
        logger.info("MOCK_ANSARI_CLIENT is False - Tests will use REAL backend")
        logger.info("Checking backend availability...")

        # Check if backend is available
        backend_available = check_backend_availability()

        if not backend_available:
            error_message = f"""
{'=' * 80}
BACKEND IS NOT AVAILABLE
{'=' * 80}

The backend server is not reachable, but MOCK_ANSARI_CLIENT is set to False.

To fix this issue, you have the following options:

Option 1: Enable mock mode
  Set MOCK_ANSARI_CLIENT=True (e.g., in your .env file, GitHub Actions, etc.)
  This will run tests with a mock client (no backend needed)

Option 2: Fix the backend URL
  Current BACKEND_SERVER_URL: {settings.BACKEND_SERVER_URL}
  Ensure the BACKEND_SERVER_URL is correct

Option 3: Start the backend server
  If BACKEND_SERVER_URL is correct, ensure the ansari-backend
  service is running on {settings.BACKEND_SERVER_URL}

{'=' * 80}
"""
            logger.error(error_message)
            pytest.exit("Backend not available and MOCK_ANSARI_CLIENT=False. See error message above for solutions.", returncode=1)

    # Log the effective configuration
    logger.info(f"Test configuration: MOCK_ANSARI_CLIENT = {settings.MOCK_ANSARI_CLIENT}")
    logger.info(f"Backend URL: {settings.BACKEND_SERVER_URL}")

    yield

    # No teardown actions needed for this fixture

@pytest.fixture(scope="module")
def settings():
    return get_settings()

# Create TestClient
client = TestClient(app)

# Test results storage
test_results = []


def log_test_result_to_list(test_name: str, success: bool, message: str, response_data: Any = None):
    """Log test results."""
    result = log_test_result(test_name, success, message, response_data)
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
        log_test_result_to_list(test_name, True, "WhatsApp service is healthy", response_data)
        assert True
    else:
        log_test_result_to_list(test_name, False, f"Health check failed: HTTP {response.status_code}", response_data)
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
    logger.debug("   URL: /whatsapp/v2")
    logger.debug(f"   Params: {format_params_for_logging(params)}")

    response = client.get("/whatsapp/v2", params=params)

    if response.status_code == 200 and "test_challenge_12345" in response.text:
        log_test_result_to_list(test_name, True, "Webhook verification successful", {"response": response.text})
        assert True
    else:
        log_test_result_to_list(test_name, False, f"Webhook verification failed: HTTP {response.status_code}", 
                        {"response": response.text})
        assert False


@pytest.mark.integration
def test_webhook_message_basic(settings):
    """Test basic WhatsApp webhook message processing using TestClient.

    With mock client enabled, this test should always succeed with 200 status.

    This test requires proper environment variables to be set that simulate
    a real WhatsApp message. If you encounter errors, verify:
    - META_BUSINESS_PHONE_NUMBER_ID is set
    - WHATSAPP_DEV_PHONE_NUM is set
    - WHATSAPP_DEV_MESSAGE_ID is set

    See .env.example for details on required environment variables.
    """
    test_name = "Basic Webhook Message"

    try:
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
        logger.debug("   URL: /whatsapp/v2")
        logger.debug(f"   Payload: {format_payload_for_logging(payload)}")
        logger.debug(f"   Mock mode: {settings.MOCK_ANSARI_CLIENT}")

        response = client.post("/whatsapp/v2", json=payload)

        # With mock client, we should always get 200
        if response.status_code == 200:
            try:
                response_data = response.json()
                success = response_data.get("success", False)
                message = response_data.get("message", "")

                if success and "processed successfully" in message.lower():
                    log_test_result_to_list(test_name, True, "Webhook message processed successfully", response_data)
                    logger.debug("   [PASS] Message processed successfully")
                else:
                    log_test_result_to_list(test_name, True, "Webhook message accepted", response_data)
                    logger.debug("   [PASS] Message accepted")

                assert True
            except json.JSONDecodeError:
                log_test_result_to_list(test_name, True, "Webhook message accepted", {"status_code": response.status_code})
                assert True
        else:
            # Non-200 status codes are now considered failures since mock client should handle everything
            response_data = None
            try:
                response_data = response.json()
            except Exception:
                response_data = response.text
            log_test_result_to_list(test_name, False, f"Expected 200, got {response.status_code}.", response_data)
            assert False, f"Expected HTTP 200 with mock client, got {response.status_code}"

    except (AttributeError, KeyError, TypeError) as e:
        error_message = f"""
{'=' * 80}
ERROR CREATING TEST PAYLOAD
{'=' * 80}

Failed to create test payload: {str(e)}

This usually means required environment variables are not set.
These variables must simulate a real WhatsApp message.

Required environment variables:
  - META_BUSINESS_PHONE_NUMBER_ID: Your Meta business phone number ID
  - WHATSAPP_DEV_PHONE_NUM: A valid WhatsApp phone number for testing
  - WHATSAPP_DEV_MESSAGE_ID: A valid message ID for testing

Please check your .env file and ensure all required variables are set.
See .env.example for the complete list of required environment variables
and examples of valid values.

{'=' * 80}
"""
        logger.error(error_message)
        log_test_result_to_list(test_name, False, f"Environment variables not properly configured: {str(e)}", None)
        pytest.fail(f"Test setup failed due to missing environment variables. See error message above. Error: {str(e)}")


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
