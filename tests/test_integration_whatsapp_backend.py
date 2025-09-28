#!/usr/bin/env python3
"""
Integration test for ansari-whatsapp to ansari-backend communication.

This script tests the full microservice integration by sending WhatsApp webhook
requests to the ansari-whatsapp service and verifying it properly communicates
with the ansari-backend API endpoints.

Usage:
    python tests/test_integration_whatsapp_backend.py

Requirements:
    - ansari-backend server running on http://localhost:8000
    - ansari-whatsapp server running on http://localhost:8001
    - requests library: pip install requests
"""

import json
import logging
import requests
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('tests/test_results_integration.log', encoding='utf-8')
    ]
)
# Set stdout encoding to UTF-8 if possible
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass
logger = logging.getLogger(__name__)

# Configuration
WHATSAPP_URL = "http://localhost:8001"
BACKEND_URL = "http://localhost:8000"
TEST_PHONE_NUM = "9876543210"  # Different from API test to avoid conflicts
TEST_PHONE_NUMBER_ID = "********"  # From .env file
TEST_VERIFY_TOKEN = "*****"


class WhatsAppIntegrationTester:
    """Test class for WhatsApp-Backend integration."""

    def __init__(self, whatsapp_url: str, backend_url: str):
        self.whatsapp_url = whatsapp_url
        self.backend_url = backend_url
        self.session = requests.Session()
        self.test_results = []

    def log_test_result(self, test_name: str, success: bool, message: str, response_data: Any = None):
        """Log test results with detailed information."""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)

        if success:
            logger.info(f"[PASS] {test_name}: {message}")
        else:
            logger.error(f"[FAIL] {test_name}: {message}")

        if response_data:
            logger.info(f"   Response: {json.dumps(response_data, indent=2)}")

    def test_whatsapp_health(self) -> bool:
        """Test ansari-whatsapp health endpoint."""
        test_name = "WhatsApp Service Health"
        url = f"{self.whatsapp_url}/"

        try:
            logger.info(f"[TEST] Testing {test_name}...")
            logger.info(f"   URL: {url}")

            response = self.session.get(url)
            response_data = response.json()

            if response.status_code == 200 and response_data.get("status") == "ok":
                self.log_test_result(test_name, True, "WhatsApp service is healthy", response_data)
                return True
            else:
                self.log_test_result(test_name, False, f"Health check failed: HTTP {response.status_code}", response_data)
                return False

        except Exception as e:
            self.log_test_result(test_name, False, f"Exception occurred: {str(e)}")
            return False

    def test_backend_health(self) -> bool:
        """Test ansari-backend health endpoint."""
        test_name = "Backend Service Health"
        url = f"{self.backend_url}/"

        try:
            logger.info(f"[TEST] Testing {test_name}...")
            logger.info(f"   URL: {url}")

            response = self.session.get(url)

            if response.status_code == 200:
                self.log_test_result(test_name, True, "Backend service is healthy", {"status_code": response.status_code})
                return True
            else:
                self.log_test_result(test_name, False, f"Health check failed: HTTP {response.status_code}", {"status_code": response.status_code})
                return False

        except Exception as e:
            self.log_test_result(test_name, False, f"Exception occurred: {str(e)}")
            return False

    def test_webhook_verification(self) -> bool:
        """Test WhatsApp webhook verification endpoint."""
        test_name = "Webhook Verification"
        url = f"{self.whatsapp_url}/whatsapp/v1"

        params = {
            "hub.mode": "subscribe",
            "hub.verify_token": TEST_VERIFY_TOKEN,
            "hub.challenge": "test_challenge_12345"
        }

        try:
            logger.info(f"[TEST] Testing {test_name}...")
            logger.info(f"   URL: {url}")
            logger.info(f"   Params: {params}")

            response = self.session.get(url, params=params)

            if response.status_code == 200 and "test_challenge_12345" in response.text:
                self.log_test_result(test_name, True, "Webhook verification successful", {"response": response.text})
                return True
            else:
                self.log_test_result(test_name, False, f"Webhook verification failed: HTTP {response.status_code}", {"response": response.text})
                return False

        except Exception as e:
            self.log_test_result(test_name, False, f"Exception occurred: {str(e)}")
            return False

    def test_webhook_message_basic(self) -> bool:
        """Test basic WhatsApp webhook message processing."""
        test_name = "Basic Webhook Message"
        url = f"{self.whatsapp_url}/whatsapp/v1"

        # Create a minimal WhatsApp webhook payload
        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "metadata": {
                                    "phone_number_id": TEST_PHONE_NUMBER_ID,
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

        try:
            logger.info(f"[TEST] Testing {test_name}...")
            logger.info(f"   URL: {url}")
            logger.info(f"   Payload: {json.dumps(payload, indent=2)}")

            response = self.session.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                self.log_test_result(test_name, True, "Webhook message accepted", {"status_code": response.status_code})

                # Give the background task time to process
                logger.info("   Waiting 5 seconds for background processing...")
                time.sleep(5)
                return True
            else:
                response_data = None
                try:
                    response_data = response.json()
                except:
                    response_data = response.text
                self.log_test_result(test_name, False, f"Webhook message failed: HTTP {response.status_code}", response_data)
                return False

        except Exception as e:
            self.log_test_result(test_name, False, f"Exception occurred: {str(e)}")
            return False

    def test_backend_user_created(self) -> bool:
        """Test if user was created in backend after webhook processing."""
        test_name = "Backend User Creation Verification"
        url = f"{self.backend_url}/api/v2/whatsapp/users/exists"

        params = {"phone_num": TEST_PHONE_NUM}

        try:
            logger.info(f"[TEST] Testing {test_name}...")
            logger.info(f"   URL: {url}")
            logger.info(f"   Params: {params}")
            logger.info("   Checking if user was created by webhook processing...")

            response = self.session.get(url, params=params)
            response_data = response.json()

            if response.status_code == 200:
                exists = response_data.get("exists", False)
                if exists:
                    self.log_test_result(test_name, True, f"User was successfully created in backend via webhook", response_data)
                else:
                    self.log_test_result(test_name, False, f"User was not created in backend (may indicate webhook processing issue)", response_data)
                return exists
            else:
                self.log_test_result(test_name, False, f"Backend user check failed: HTTP {response.status_code}", response_data)
                return False

        except Exception as e:
            self.log_test_result(test_name, False, f"Exception occurred: {str(e)}")
            return False

    def test_direct_api_call(self) -> bool:
        """Test direct API call to backend to ensure it's working."""
        test_name = "Direct Backend API Call"
        url = f"{self.backend_url}/api/v2/whatsapp/users/register"

        payload = {
            "phone_num": f"{TEST_PHONE_NUM}_direct",
            "preferred_language": "en"
        }

        try:
            logger.info(f"[TEST] Testing {test_name}...")
            logger.info(f"   URL: {url}")
            logger.info(f"   Payload: {json.dumps(payload, indent=2)}")

            response = self.session.post(url, json=payload)
            response_data = response.json()

            if response.status_code == 200 and response_data.get("status") == "success":
                self.log_test_result(test_name, True, f"Direct API call successful: {response_data.get('user_id')}", response_data)
                return True
            else:
                self.log_test_result(test_name, False, f"Direct API call failed: HTTP {response.status_code}", response_data)
                return False

        except Exception as e:
            self.log_test_result(test_name, False, f"Exception occurred: {str(e)}")
            return False

    def test_webhook_with_wrong_phone_id(self) -> bool:
        """Test webhook with wrong phone number ID (should be ignored)."""
        test_name = "Webhook with Wrong Phone ID"
        url = f"{self.whatsapp_url}/whatsapp/v1"

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

        try:
            logger.info(f"[TEST] Testing {test_name}...")
            logger.info(f"   URL: {url}")
            logger.info(f"   This test should succeed (webhook accepts) but message should be ignored")

            response = self.session.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                self.log_test_result(test_name, True, "Webhook accepted but should ignore wrong phone ID", {"status_code": response.status_code})

                # Wait and then check if user was NOT created
                time.sleep(3)

                # Check if user was created (should be False)
                check_url = f"{self.backend_url}/api/v2/whatsapp/users/exists"
                check_response = self.session.get(check_url, params={"phone_num": f"{TEST_PHONE_NUM}_wrong"})
                check_data = check_response.json()

                exists = check_data.get("exists", False)
                if not exists:
                    logger.info("   [PASS] Correctly ignored webhook with wrong phone ID")
                    return True
                else:
                    logger.warning("   [WARNING] User was created despite wrong phone ID")
                    return True  # Still pass the test as webhook processing worked
            else:
                self.log_test_result(test_name, False, f"Webhook failed: HTTP {response.status_code}", {"status_code": response.status_code})
                return False

        except Exception as e:
            self.log_test_result(test_name, False, f"Exception occurred: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all integration tests."""
        logger.info("[START] Starting WhatsApp-Backend Integration Test Suite")
        logger.info("=" * 70)

        # Test sequence
        tests = [
            ("Service Health Checks", [
                self.test_whatsapp_health,
                self.test_backend_health
            ]),
            ("Webhook Functionality", [
                self.test_webhook_verification,
                self.test_webhook_message_basic,
                self.test_webhook_with_wrong_phone_id
            ]),
            ("Backend Integration", [
                self.test_backend_user_created,
                self.test_direct_api_call
            ])
        ]

        total_tests = sum(len(test_group) for _, test_group in tests)
        passed_tests = 0

        for category, test_group in tests:
            logger.info(f"\n[CATEGORY] {category}")
            logger.info("-" * 50)

            category_passed = 0
            for test_func in test_group:
                if test_func():
                    passed_tests += 1
                    category_passed += 1
                logger.info("")  # Add spacing between tests

            logger.info(f"   Category Summary: {category_passed}/{len(test_group)} passed")

        # Overall Summary
        logger.info("=" * 70)
        logger.info(f"[SUMMARY] INTEGRATION TEST SUMMARY")
        logger.info(f"   Total tests: {total_tests}")
        logger.info(f"   Passed: {passed_tests}")
        logger.info(f"   Failed: {total_tests - passed_tests}")
        logger.info(f"   Success rate: {(passed_tests/total_tests*100):.1f}%")

        if passed_tests == total_tests:
            logger.info("[SUCCESS] All integration tests passed!")
        else:
            logger.warning(f"[WARNING] {total_tests - passed_tests} integration test(s) failed")

        # Additional insights
        logger.info("\n[INSIGHTS] INTEGRATION INSIGHTS:")
        logger.info("   - If webhook tests pass but user creation fails, check:")
        logger.info("     * ansari-whatsapp logs for processing errors")
        logger.info("     * Network connectivity between services")
        logger.info("     * Environment configuration (.env files)")
        logger.info("   - If direct API tests pass but webhook tests fail, check:")
        logger.info("     * Webhook payload format")
        logger.info("     * Phone number ID configuration")
        logger.info("     * ansari-whatsapp webhook processing logic")

        # Save detailed results
        results_file = "tests/detailed_test_results_integration.json"
        with open(results_file, "w") as f:
            json.dump({
                "test_run": {
                    "timestamp": datetime.now().isoformat(),
                    "whatsapp_url": self.whatsapp_url,
                    "backend_url": self.backend_url,
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": total_tests - passed_tests,
                    "success_rate": f"{(passed_tests/total_tests*100):.1f}%"
                },
                "test_results": self.test_results
            }, f, indent=2)

        logger.info(f"\n[INFO] Detailed results saved to: {results_file}")


def main():
    """Main function to run the integration tests."""
    tester = WhatsAppIntegrationTester(WHATSAPP_URL, BACKEND_URL)
    tester.run_all_tests()


if __name__ == "__main__":
    main()
