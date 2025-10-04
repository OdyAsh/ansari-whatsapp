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

Security: All sensitive data is loaded from environment variables and masked in logs.
"""

import json
import os
import pytest
import time
from typing import Any
from fastapi.testclient import TestClient

from ansari_whatsapp.app.main import app
from ansari_whatsapp.utils.whatsapp_logger import get_logger
from ansari_whatsapp.utils.config import get_settings
from .test_utils import (
    secure_log_result,
    format_payload_for_logging,
    format_params_for_logging
)

# Initialize logger
logger = get_logger(__name__)

# Configuration (non-sensitive)
TEST_PHONE_NUM = "9876543210"  # Test phone number for webhook messages


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
    """Test basic WhatsApp webhook message processing using TestClient."""
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
                                    "from": TEST_PHONE_NUM,
                                    "id": f"test_message_{int(time.time())}",
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

    response = client.post("/whatsapp/v1", json=payload)

    if response.status_code == 200:
        # Validate response structure in test environment
        try:
            response_data = response.json()
            success = response_data.get("success", False)
            message = response_data.get("message", "")

            if success and "processed successfully" in message.lower():
                log_test_result(test_name, True, "Webhook message accepted with proper structure", response_data)
                logger.debug("   [PASS] Message processed successfully with structured response")
            else:
                log_test_result(test_name, True, "Webhook message accepted", response_data)
                logger.debug("   [PASS] Message accepted (may be partial processing)")

            assert True
        except json.JSONDecodeError:
            # Fallback for non-JSON responses
            log_test_result(test_name, True, "Webhook message accepted", {"status_code": response.status_code})
            assert True
    elif response.status_code == 500:
        # In test environment, expect 500 for user registration failures (backend not available)
        try:
            response_data = response.json()
            error_code = response_data.get("error_code")

            if error_code == "USER_REGISTRATION_FAILED":
                log_test_result(test_name, True, "Expected test failure: Backend service not available", response_data)
                logger.debug("   [PASS] Correctly returned 500 for registration failure (expected in test environment)")
                assert True
            else:
                log_test_result(test_name, False, f"Unexpected 500 error: {response_data.get('message')}", response_data)
                assert False
        except json.JSONDecodeError:
            log_test_result(test_name, False, f"Invalid JSON in 500 response: {response.text}")
            assert False
    else:
        response_data = None
        try:
            response_data = response.json()
        except Exception:
            response_data = response.text
        log_test_result(test_name, False, f"Webhook message failed: HTTP {response.status_code}", response_data)
        assert False


@pytest.mark.integration
def test_webhook_with_wrong_phone_id():
    """Test webhook with wrong phone number ID (should be ignored) using TestClient."""
    test_name = "Webhook with Wrong Phone ID"

    # Create payload with wrong phone number ID
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {
                                "phone_number_id": "999999999999999",  # Wrong ID
                                "display_phone_number": "+1234567890"
                            },
                            "messages": [
                                {
                                    "from": f"{TEST_PHONE_NUM}_wrong",
                                    "id": f"test_message_wrong_{int(time.time())}",
                                    "timestamp": str(int(time.time())),
                                    "type": "text",
                                    "text": {
                                        "body": "This should be ignored due to wrong phone ID"
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
    logger.debug("   This test should succeed (webhook accepts) but message should be ignored")

    response = client.post("/whatsapp/v1", json=payload)

    # In test environment, wrong phone ID should return 422 with structured error response
    if response.status_code == 422:
        try:
            response_data = response.json()
            success = response_data.get("success", True)
            error_code = response_data.get("error_code")

            if not success and error_code == "WRONG_PHONE_NUMBER":
                log_test_result(test_name, True, "Correctly rejected wrong phone ID with 422 status", response_data)
                logger.debug("   [PASS] Correctly returned 422 for wrong phone ID")
                assert True
            else:
                log_test_result(test_name, False, "Wrong response structure for error case", response_data)
                assert False
        except json.JSONDecodeError:
            log_test_result(test_name, False, f"Invalid JSON response: {response.text}")
            assert False
    else:
        response_data = None
        try:
            response_data = response.json()
        except:
            response_data = response.text
        log_test_result(test_name, False, f"Expected 422 status code, got {response.status_code}", response_data)
        assert False


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
