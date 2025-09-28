#!/usr/bin/env python3
"""
Test script for ansari-backend WhatsApp API endpoints.

This script tests all the WhatsApp API endpoints in the ansari-backend service
that the ansari-whatsapp microservice depends on.

Usage:
    python tests/test_whatsapp_api_endpoints.py

Requirements:
    - ansari-backend server running on http://localhost:8000
    - requests library: pip install requests
"""

import json
import logging
import requests
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('tests/test_results_api_endpoints.log', encoding='utf-8')
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
BACKEND_URL = "http://localhost:8000"
TEST_PHONE_NUM = "1234567890"
TEST_LANGUAGE = "en"
TEST_LATITUDE = 40.7128
TEST_LONGITUDE = -74.0060
TEST_THREAD_TITLE = "Test Thread for API Testing"

class WhatsAppAPITester:
    """Test class for WhatsApp API endpoints."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.thread_id: Optional[str] = None

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

    def test_user_registration(self) -> bool:
        """Test POST /api/v2/whatsapp/users/register endpoint."""
        test_name = "User Registration"
        url = f"{self.base_url}/api/v2/whatsapp/users/register"

        payload = {
            "phone_num": TEST_PHONE_NUM,
            "preferred_language": TEST_LANGUAGE
        }

        try:
            logger.info(f"[TEST] Testing {test_name}...")
            logger.info(f"   URL: {url}")
            logger.info(f"   Payload: {json.dumps(payload, indent=2)}")

            response = self.session.post(url, json=payload)
            response_data = response.json()

            if response.status_code == 200 and response_data.get("status") == "success":
                self.log_test_result(test_name, True, f"User registered successfully with ID: {response_data.get('user_id')}", response_data)
                return True
            else:
                self.log_test_result(test_name, False, f"Registration failed: HTTP {response.status_code}", response_data)
                return False

        except Exception as e:
            self.log_test_result(test_name, False, f"Exception occurred: {str(e)}")
            return False

    def test_user_exists(self) -> bool:
        """Test GET /api/v2/whatsapp/users/exists endpoint."""
        test_name = "User Existence Check"
        url = f"{self.base_url}/api/v2/whatsapp/users/exists"

        params = {"phone_num": TEST_PHONE_NUM}

        try:
            logger.info(f"[TEST] Testing {test_name}...")
            logger.info(f"   URL: {url}")
            logger.info(f"   Params: {params}")

            response = self.session.get(url, params=params)
            response_data = response.json()

            if response.status_code == 200:
                exists = response_data.get("exists", False)
                self.log_test_result(test_name, True, f"User existence check successful: exists = {exists}", response_data)
                return True
            else:
                self.log_test_result(test_name, False, f"User existence check failed: HTTP {response.status_code}", response_data)
                return False

        except Exception as e:
            self.log_test_result(test_name, False, f"Exception occurred: {str(e)}")
            return False

    def test_location_update(self) -> bool:
        """Test PUT /api/v2/whatsapp/users/location endpoint."""
        test_name = "Location Update"
        url = f"{self.base_url}/api/v2/whatsapp/users/location"

        payload = {
            "phone_num": TEST_PHONE_NUM,
            "latitude": TEST_LATITUDE,
            "longitude": TEST_LONGITUDE
        }

        try:
            logger.info(f"[TEST] Testing {test_name}...")
            logger.info(f"   URL: {url}")
            logger.info(f"   Payload: {json.dumps(payload, indent=2)}")

            response = self.session.put(url, json=payload)
            response_data = response.json()

            if response.status_code == 200:
                self.log_test_result(test_name, True, "Location updated successfully", response_data)
                return True
            else:
                self.log_test_result(test_name, False, f"Location update failed: HTTP {response.status_code}", response_data)
                return False

        except Exception as e:
            self.log_test_result(test_name, False, f"Exception occurred: {str(e)}")
            return False

    def test_thread_creation(self) -> bool:
        """Test POST /api/v2/whatsapp/threads endpoint."""
        test_name = "Thread Creation"
        url = f"{self.base_url}/api/v2/whatsapp/threads"

        payload = {
            "phone_num": TEST_PHONE_NUM,
            "title": TEST_THREAD_TITLE
        }

        try:
            logger.info(f"[TEST] Testing {test_name}...")
            logger.info(f"   URL: {url}")
            logger.info(f"   Payload: {json.dumps(payload, indent=2)}")

            response = self.session.post(url, json=payload)
            response_data = response.json()

            if response.status_code == 200 and "thread_id" in response_data:
                self.thread_id = response_data["thread_id"]
                self.log_test_result(test_name, True, f"Thread created successfully with ID: {self.thread_id}", response_data)
                return True
            else:
                self.log_test_result(test_name, False, f"Thread creation failed: HTTP {response.status_code}", response_data)
                return False

        except Exception as e:
            self.log_test_result(test_name, False, f"Exception occurred: {str(e)}")
            return False

    def test_last_thread_info(self) -> bool:
        """Test GET /api/v2/whatsapp/threads/last endpoint."""
        test_name = "Last Thread Info"
        url = f"{self.base_url}/api/v2/whatsapp/threads/last"

        params = {"phone_num": TEST_PHONE_NUM}

        try:
            logger.info(f"[TEST] Testing {test_name}...")
            logger.info(f"   URL: {url}")
            logger.info(f"   Params: {params}")

            response = self.session.get(url, params=params)
            response_data = response.json()

            if response.status_code == 200:
                thread_id = response_data.get("thread_id")
                last_message_time = response_data.get("last_message_time")
                self.log_test_result(test_name, True, f"Last thread info retrieved: thread_id={thread_id}, last_message_time={last_message_time}", response_data)
                return True
            else:
                self.log_test_result(test_name, False, f"Last thread info failed: HTTP {response.status_code}", response_data)
                return False

        except Exception as e:
            self.log_test_result(test_name, False, f"Exception occurred: {str(e)}")
            return False

    def test_thread_history(self) -> bool:
        """Test GET /api/v2/whatsapp/threads/{thread_id}/history endpoint."""
        test_name = "Thread History"

        if not self.thread_id:
            self.log_test_result(test_name, False, "No thread_id available from previous test")
            return False

        url = f"{self.base_url}/api/v2/whatsapp/threads/{self.thread_id}/history"
        params = {"phone_num": TEST_PHONE_NUM}

        try:
            logger.info(f"[TEST] Testing {test_name}...")
            logger.info(f"   URL: {url}")
            logger.info(f"   Params: {params}")

            response = self.session.get(url, params=params)
            response_data = response.json()

            if response.status_code == 200:
                messages_count = len(response_data.get("messages", []))
                self.log_test_result(test_name, True, f"Thread history retrieved successfully with {messages_count} messages", {"messages_count": messages_count, "thread_id": self.thread_id})
                return True
            else:
                self.log_test_result(test_name, False, f"Thread history failed: HTTP {response.status_code}", response_data)
                return False

        except Exception as e:
            self.log_test_result(test_name, False, f"Exception occurred: {str(e)}")
            return False

    def test_message_processing(self) -> bool:
        """Test POST /api/v2/whatsapp/messages/process endpoint (streaming)."""
        test_name = "Message Processing (Streaming)"

        if not self.thread_id:
            self.log_test_result(test_name, False, "No thread_id available from previous test")
            return False

        url = f"{self.base_url}/api/v2/whatsapp/messages/process"

        payload = {
            "phone_num": TEST_PHONE_NUM,
            "thread_id": self.thread_id,
            "message": "Hello, this is a test message from the API test suite."
        }

        try:
            logger.info(f"[TEST] Testing {test_name}...")
            logger.info(f"   URL: {url}")
            logger.info(f"   Payload: {json.dumps(payload, indent=2)}")
            logger.info("   Note: This is a streaming endpoint, will read first chunk only")

            response = self.session.post(url, json=payload, stream=True, timeout=30)

            if response.status_code == 200:
                # Read first chunk of streaming response
                first_chunk = None
                for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
                    if chunk:
                        first_chunk = chunk
                        break

                self.log_test_result(test_name, True, f"Message processing started successfully. First chunk: {first_chunk[:100]}..." if first_chunk else "Message processing started (no immediate content)", {"status_code": response.status_code})
                return True
            else:
                response_data = None
                try:
                    response_data = response.json()
                except:
                    response_data = response.text
                self.log_test_result(test_name, False, f"Message processing failed: HTTP {response.status_code}", response_data)
                return False

        except Exception as e:
            self.log_test_result(test_name, False, f"Exception occurred: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all WhatsApp API endpoint tests."""
        logger.info("[START] Starting WhatsApp API Endpoints Test Suite")
        logger.info("=" * 60)

        # Test server connectivity first
        try:
            health_response = self.session.get(f"{self.base_url}/")
            if health_response.status_code != 200:
                logger.error(f"[FAIL] Backend server not responding at {self.base_url}")
                return
        except Exception as e:
            logger.error(f"[FAIL] Cannot connect to backend server: {str(e)}")
            return

        logger.info(f"[PASS] Backend server is responding at {self.base_url}")

        # Run all tests
        tests = [
            self.test_user_registration,
            self.test_user_exists,
            self.test_location_update,
            self.test_thread_creation,
            self.test_last_thread_info,
            self.test_thread_history,
            self.test_message_processing
        ]

        passed = 0
        total = len(tests)

        for test_func in tests:
            logger.info("-" * 40)
            if test_func():
                passed += 1

        # Summary
        logger.info("=" * 60)
        logger.info(f"[SUMMARY] TEST SUMMARY")
        logger.info(f"   Total tests: {total}")
        logger.info(f"   Passed: {passed}")
        logger.info(f"   Failed: {total - passed}")
        logger.info(f"   Success rate: {(passed/total*100):.1f}%")

        if passed == total:
            logger.info("[SUCCESS] All tests passed!")
        else:
            logger.warning(f"[WARNING] {total - passed} test(s) failed")

        # Save detailed results
        results_file = "tests/detailed_test_results_api_endpoints.json"
        with open(results_file, "w") as f:
            json.dump({
                "test_run": {
                    "timestamp": datetime.now().isoformat(),
                    "backend_url": self.base_url,
                    "total_tests": total,
                    "passed_tests": passed,
                    "failed_tests": total - passed,
                    "success_rate": f"{(passed/total*100):.1f}%"
                },
                "test_results": self.test_results
            }, f, indent=2)

        logger.info(f"[INFO] Detailed results saved to: {results_file}")


def main():
    """Main function to run the tests."""
    tester = WhatsAppAPITester(BACKEND_URL)
    tester.run_all_tests()


if __name__ == "__main__":
    main()