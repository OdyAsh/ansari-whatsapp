#!/usr/bin/env python3
"""
Test runner for all WhatsApp microservice tests.

This script runs both the API endpoint tests and integration tests,
providing a comprehensive test suite for the WhatsApp microservice.

Usage:
    python tests/run_all_tests.py [--api-only] [--integration-only]

Requirements:
    - ansari-backend server running on http://localhost:8000
    - ansari-whatsapp server running on http://localhost:8001
    - requests library: pip install requests
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('tests/test_runner.log', encoding='utf-8')
    ]
)
# Set stdout encoding to UTF-8 if possible
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass
logger = logging.getLogger(__name__)


def run_test_script(script_path: str, test_name: str) -> tuple[bool, str]:
    """Run a test script and return success status and output."""
    try:
        logger.info(f"[RUNNING] Running {test_name}...")

        result = subprocess.run(
            [sys.executable, script_path],
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        success = result.returncode == 0
        output = result.stdout + result.stderr

        if success:
            logger.info(f"[PASS] {test_name} completed successfully")
        else:
            logger.error(f"[FAIL] {test_name} failed with return code {result.returncode}")

        return success, output

    except subprocess.TimeoutExpired:
        logger.error(f"[FAIL] {test_name} timed out after 5 minutes")
        return False, "Test timed out"
    except Exception as e:
        logger.error(f"[FAIL] {test_name} failed with exception: {str(e)}")
        return False, str(e)


def check_services() -> tuple[bool, bool]:
    """Check if both services are running."""
    import requests

    backend_running = False
    whatsapp_running = False

    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        # logger.debug(f"Backend service response: {response.status_code}")
        backend_running = response.status_code == 200
    except:
        pass

    try:
        response = requests.get("http://localhost:8001/", timeout=5)
        whatsapp_running = response.status_code == 200
    except:
        pass

    return backend_running, whatsapp_running


def main():
    """Main function to run all tests."""
    parser = argparse.ArgumentParser(description="Run WhatsApp microservice tests")
    parser.add_argument("--api-only", action="store_true", help="Run only API endpoint tests")
    parser.add_argument("--integration-only", action="store_true", help="Run only integration tests")
    args = parser.parse_args()

    logger.info("[TEST] WhatsApp Microservice Test Runner")
    logger.info("=" * 60)
    logger.info(f"Started at: {datetime.now().isoformat()}")

    # Check service availability
    logger.info("\n[CHECK] Checking service availability...")
    backend_running, whatsapp_running = check_services()

    logger.info(f"   Backend (localhost:8000): {'[PASS] Running' if backend_running else '[FAIL] Not responding'}")
    logger.info(f"   WhatsApp (localhost:8001): {'[PASS] Running' if whatsapp_running else '[FAIL] Not responding'}")

    if not backend_running:
        logger.error("[FAIL] ansari-backend service is not running. Please start it first:")
        logger.error("   cd ansari-backend && .venv/Scripts/python.exe src/ansari/app/main_api.py")
        return False

    if not whatsapp_running:
        logger.error("[FAIL] ansari-whatsapp service is not running. Please start it first:")
        logger.error("   cd ansari-whatsapp && .venv/Scripts/python.exe src/ansari_whatsapp/app/main.py")
        return False

    logger.info("[PASS] All services are running!")

    # Determine which tests to run
    run_api = not args.integration_only
    run_integration = not args.api_only

    test_results = []

    # Run API endpoint tests
    if run_api:
        logger.info("\n" + "=" * 60)
        logger.info("[API] API ENDPOINT TESTS")
        logger.info("=" * 60)

        success, output = run_test_script("tests/test_whatsapp_api_endpoints.py", "API Endpoint Tests")
        test_results.append({
            "test_suite": "API Endpoints",
            "success": success,
            "output": output
        })

    # Run integration tests
    if run_integration:
        logger.info("\n" + "=" * 60)
        logger.info("[INTEGRATION] INTEGRATION TESTS")
        logger.info("=" * 60)

        success, output = run_test_script("tests/test_integration_whatsapp_backend.py", "Integration Tests")
        test_results.append({
            "test_suite": "Integration",
            "success": success,
            "output": output
        })

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("[SUMMARY] FINAL TEST SUMMARY")
    logger.info("=" * 60)

    total_suites = len(test_results)
    passed_suites = sum(1 for result in test_results if result["success"])

    for result in test_results:
        status = "[PASS] PASSED" if result["success"] else "[FAIL] FAILED"
        logger.info(f"   {result['test_suite']} Tests: {status}")

    logger.info(f"\n   Test Suites: {passed_suites}/{total_suites} passed")

    if passed_suites == total_suites:
        logger.info("[SUCCESS] ALL TEST SUITES PASSED!")
        success_overall = True
    else:
        logger.error(f"[WARNING] {total_suites - passed_suites} test suite(s) failed")
        success_overall = False

    # Save combined results
    combined_results = {
        "test_run": {
            "timestamp": datetime.now().isoformat(),
            "total_suites": total_suites,
            "passed_suites": passed_suites,
            "failed_suites": total_suites - passed_suites,
            "overall_success": success_overall
        },
        "suite_results": test_results
    }

    results_file = "tests/combined_test_results.json"
    with open(results_file, "w") as f:
        json.dump(combined_results, f, indent=2)

    logger.info(f"\n[INFO] Combined results saved to: {results_file}")

    # File locations
    logger.info("\n[FILES] Generated Files:")
    logger.info("   tests/test_results_api_endpoints.log - API test logs")
    logger.info("   tests/detailed_test_results_api_endpoints.json - API test details")
    logger.info("   tests/test_results_integration.log - Integration test logs")
    logger.info("   tests/detailed_test_results_integration.json - Integration test details")
    logger.info("   tests/test_runner.log - Test runner logs")
    logger.info("   tests/combined_test_results.json - Combined results")

    return success_overall


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)