"""
Test utilities for WhatsApp microservice tests.

This module provides secure logging and common test functionality following
the backend test patterns (pytest + TestClient + fixtures).
"""

import json
import re
from typing import Any, Dict
from datetime import datetime

def mask_sensitive_data(data: Any) -> Any:
    """
    Mask sensitive data in test logs to prevent exposure.

    Recursively processes dictionaries, lists, and strings to mask sensitive information.
    """
    if isinstance(data, dict):
        masked = {}
        for key, value in data.items():
            # Check if key contains sensitive patterns
            key_lower = key.lower()
            if any(pattern in key_lower for pattern in ['token', 'verify', 'secret', 'phone_number_id']):
                if isinstance(value, str) and value:
                    masked[key] = f"<{key.upper()}>"
                else:
                    masked[key] = value
            elif key_lower == 'phone_num':
                masked[key] = "<TEST_PHONE_NUM>"
            elif key_lower == 'from' and isinstance(value, str) and value.isdigit():
                masked[key] = "<TEST_PHONE_NUM>"
            else:
                masked[key] = mask_sensitive_data(value)
        return masked

    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]

    elif isinstance(data, str):
        # Mask phone numbers (sequences of 10+ digits)
        masked = re.sub(r'\b\d{10,}\b', '<PHONE_NUMBER>', data)

        # Mask tokens (long alphanumeric strings)
        masked = re.sub(r'\b[a-f0-9]{32,}\b', '<TOKEN>', masked)

        return masked

    else:
        return data


def secure_log_result(test_name: str, success: bool, message: str, response_data: Any = None) -> Dict[str, Any]:
    """
    Create a secure test result log entry with masked sensitive data.

    Args:
        test_name: Name of the test
        success: Whether the test passed
        message: Test result message
        response_data: Response data to include (will be masked)

    Returns:
        Dictionary containing the secure log entry
    """
    result = {
        "test_name": test_name,
        "success": success,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }

    if response_data is not None:
        result["response_data"] = mask_sensitive_data(response_data)

    return result


def format_payload_for_logging(payload: Dict[str, Any]) -> str:
    """
    Format payload for logging with sensitive data masked.

    Args:
        payload: The payload dictionary

    Returns:
        JSON string with sensitive data masked
    """
    masked_payload = mask_sensitive_data(payload)
    return json.dumps(masked_payload, indent=2)


def format_params_for_logging(params: Dict[str, Any]) -> str:
    """
    Format URL parameters for logging with sensitive data masked.

    Args:
        params: The parameters dictionary

    Returns:
        JSON string with sensitive data masked
    """
    masked_params = mask_sensitive_data(params)
    return json.dumps(masked_params, indent=2)