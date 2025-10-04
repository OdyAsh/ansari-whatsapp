# WhatsApp Microservice Test Suite

This directory contains integration tests for the WhatsApp microservice, focusing on WhatsApp webhook endpoints.

## 🚨 IMPORTANT CHANGE: Test Location Update

**WhatsApp API endpoint tests have been moved to `ansari-backend/tests/unit/test_whatsapp_api_endpoints.py`**

### Reason for Move:
- The WhatsApp API endpoints (like `/api/v2/whatsapp/users/register`) are **implemented in ansari-backend**
- Tests should live with the code they test
- Moving them allows use of **TestClient** instead of external HTTP calls
- **No external server dependencies** needed for CI/CD
- **Faster test execution** with in-memory testing

## Current Test Files (This Repo)

### 1. WhatsApp Service Tests (`test_whatsapp_service.py`)
Tests WhatsApp service webhook endpoints (no external dependencies):
- ✅ WhatsApp service health check
- ✅ Webhook verification endpoint
- ✅ Basic webhook message processing
- ✅ Wrong phone ID handling (should be ignored)

### 2. Test Utilities (`test_utils.py`)
Secure logging and testing utilities:
- 🔒 Sensitive data masking for logs
- 🌍 Environment variable loading with validation
- 📝 Secure test result logging


## 🚀 Quick Start

### Prerequisites
1. **Environment Variables** (in `.env`):
   ```env
   META_WEBHOOK_VERIFY_TOKEN=your_verify_token
   META_BUSINESS_PHONE_NUMBER_ID=your_phone_number_id
   ALWAYS_RETURN_OK_TO_META=True  # Set to False for CI/CD
   LOG_TEST_FILES_ONLY=False      # Set to True to filter test logs
   ```

2. **Install Dependencies**:
   ```bash
   cd ansari-whatsapp
   uv add pytest
   ```

### Running Tests

#### WhatsApp Service Tests (This Repo)
```bash
# All WhatsApp service tests (local development)
pytest tests/test_whatsapp_service.py -v

# With test-only logging (filters out non-test logs)
LOG_TEST_FILES_ONLY=True pytest tests/test_whatsapp_service.py -v -s

# For CI/CD (proper HTTP status codes)
ALWAYS_RETURN_OK_TO_META=False pytest tests/test_whatsapp_service.py -v
```

#### WhatsApp API Tests (ansari-backend repo)
```bash
cd ../ansari-backend
pytest tests/unit/test_whatsapp_api_endpoints.py -v

# Streaming tests specifically
pytest tests/unit/test_whatsapp_api_endpoints.py -m streaming -v
```

## 📊 Test Categories

### WhatsApp Service Tests (ansari-whatsapp)
- **Purpose**: Test WhatsApp webhook endpoints
- **Technology**: pytest + TestClient (for WhatsApp service)
- **Dependencies**: ✅ **No external dependencies** (uses TestClient only)

### API Tests (ansari-backend)
- **Purpose**: Test WhatsApp API endpoints in backend
- **Technology**: pytest + TestClient (for backend service)
- **Dependencies**: ✅ **No external servers needed** (uses TestClient)
- **Streaming**: ✅ **Comprehensive streaming endpoint testing**

## 🔒 Security Features

- **Sensitive Data Masking**: All tokens, phone numbers, and secrets are masked in logs
- **Environment Variables**: No hardcoded secrets in code
- **Secure Logging**: `test_utils.py` provides secure logging utilities

## 🛠 GitHub Actions Ready

### ansari-whatsapp CI/CD
- ✅ **No external server dependencies** for integration tests
- ✅ **Uses TestClient** for WhatsApp service testing
- ✅ **Environment secrets** properly loaded
- ✅ **Fast execution** with in-memory testing
- ⚠️ **Important**: Set `ALWAYS_RETURN_OK_TO_META=False` in CI/CD workflows to get proper HTTP status codes for assertions

**Example GitHub Actions workflow:**
```yaml
- name: Run tests
  env:
    ALWAYS_RETURN_OK_TO_META: False
  run: pytest tests/ -v
```

### ansari-backend CI/CD
- ✅ **No external server dependencies** for API tests
- ✅ **Uses TestClient** for all endpoint testing
- ✅ **Comprehensive streaming tests** included

## 📝 Migration Summary

### What Moved:
- `test_whatsapp_api_endpoints.py` → `ansari-backend/tests/unit/test_whatsapp_api_endpoints.py`
- `whatsapp_test_utils.py` → `ansari-backend/tests/whatsapp_test_utils.py`

### What Stayed:
- `test_whatsapp_service.py` - Tests WhatsApp webhook endpoints (renamed and focused)
- `test_utils.py` - Secure logging utilities for service tests

### Benefits:
- 🚀 **Faster CI/CD** - No external server startup time
- 🔒 **Better Security** - No hardcoded secrets, secure logging
- 📍 **Proper Organization** - Tests live with the code they test
- 🧪 **Comprehensive Testing** - Full streaming endpoint coverage
- ⚡ **Easy Local Development** - TestClient for quick iteration

## 📞 Support

For GitHub Actions setup or testing issues:
1. Check that environment secrets are configured in GitHub
2. Verify `.env` file contains required variables locally
3. Review test logs for specific error details
4. Consult `CLAUDE.md` files in both repositories for detailed instructions

The test suite now provides comprehensive validation while being optimized for modern CI/CD workflows!