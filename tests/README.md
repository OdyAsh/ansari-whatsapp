# WhatsApp Microservice Test Suite

This directory contains comprehensive tests for the WhatsApp microservice implementation, including API endpoint tests and full integration tests between `ansari-whatsapp` and `ansari-backend` services.

## 📋 Test Overview

### 1. API Endpoint Tests (`test_whatsapp_api_endpoints.py`)
Tests all WhatsApp API endpoints in the `ansari-backend` service:
- ✅ `POST /api/v2/whatsapp/users/register` - User registration
- ✅ `GET /api/v2/whatsapp/users/exists` - User existence check
- ✅ `PUT /api/v2/whatsapp/users/location` - Location updates
- ✅ `POST /api/v2/whatsapp/threads` - Thread creation
- ✅ `GET /api/v2/whatsapp/threads/last` - Last thread info
- ✅ `GET /api/v2/whatsapp/threads/{thread_id}/history` - Thread history
- ✅ `POST /api/v2/whatsapp/messages/process` - Message processing (streaming)

### 2. Integration Tests (`test_integration_whatsapp_backend.py`)
Tests full microservice communication:
- 🏥 Service health checks (both services)
- 🔐 Webhook verification endpoint
- 📨 WhatsApp webhook message processing
- 🚫 Wrong phone ID handling (should be ignored)
- 👤 Backend user creation verification
- 🔗 Direct API communication verification

### 3. Test Runner (`run_all_tests.py`)
Orchestrates all tests with comprehensive logging and reporting.

## 🚀 Quick Start

### Prerequisites
1. **Start both services:**
   ```bash
   # Terminal 1: Start ansari-backend
   cd ansari-backend
   .venv/Scripts/python.exe src/ansari/app/main_api.py

   # Terminal 2: Start ansari-whatsapp
   cd ansari-whatsapp
   .venv/Scripts/python.exe src/ansari_whatsapp/app/main.py
   ```

2. **Install required dependencies:**
   ```bash
   cd ansari-whatsapp
   .venv/Scripts/python.exe -m pip install requests
   ```

### Running Tests

#### Option 1: Run All Tests (Recommended)
```bash
cd ansari-whatsapp
.venv/Scripts/python.exe tests/run_all_tests.py
```

#### Option 2: Run Specific Test Suites
```bash
# API endpoint tests only
.venv/Scripts/python.exe tests/run_all_tests.py --api-only

# Integration tests only
.venv/Scripts/python.exe tests/run_all_tests.py --integration-only
```

#### Option 3: Run Individual Tests
```bash
# API endpoint tests
.venv/Scripts/python.exe tests/test_whatsapp_api_endpoints.py

# Integration tests
.venv/Scripts/python.exe tests/test_integration_whatsapp_backend.py
```

## 📊 Understanding Test Results

### Console Output
Tests provide real-time colored output:
- ✅ **Green checkmarks**: Successful tests
- ❌ **Red X marks**: Failed tests
- 🧪 **Test tube**: Currently running test
- 📊 **Chart**: Summary statistics
- 🎉 **Party**: All tests passed

### Log Files
Each test run generates detailed log files:

| File | Description |
|------|-------------|
| `test_results_api_endpoints.log` | Detailed API endpoint test logs |
| `test_results_integration.log` | Detailed integration test logs |
| `test_runner.log` | Test runner execution logs |

### JSON Reports
Structured test results for programmatic analysis:

| File | Description |
|------|-------------|
| `detailed_test_results_api_endpoints.json` | Complete API test results with timestamps |
| `detailed_test_results_integration.json` | Complete integration test results |
| `combined_test_results.json` | Overall test suite summary |

## 🔍 Test Details

### API Endpoint Tests
- **User Registration**: Creates a new WhatsApp user (`1234567890`)
- **User Existence**: Verifies user was created successfully
- **Location Update**: Updates user's GPS coordinates
- **Thread Management**: Creates and retrieves thread information
- **Message Processing**: Tests streaming AI response endpoint

### Integration Tests
- **Health Checks**: Verifies both services are responding
- **Webhook Verification**: Tests Meta's webhook verification flow
- **Message Processing**: Sends simulated WhatsApp webhook with different scenarios:
  - Valid message (should process and create user)
  - Wrong phone ID (should be ignored)
- **Backend Verification**: Confirms webhook processing created users in backend

## 🛠 Troubleshooting

### Common Issues

#### Services Not Running
```
❌ ansari-backend service is not running
```
**Solution**: Start the backend service:
```bash
cd ansari-backend && .venv/Scripts/python.exe src/ansari/app/main_api.py
```

#### Import Errors
```
ModuleNotFoundError: No module named 'requests'
```
**Solution**: Install requests in the correct virtual environment:
```bash
cd ansari-whatsapp && .venv/Scripts/python.exe -m pip install requests
```

#### Webhook Processing Issues
If integration tests pass but webhook messages aren't processed:
1. Check `ansari-whatsapp` logs for processing errors
2. Verify phone number ID in `.env` matches test configuration
3. Check network connectivity between services
4. Verify CORS configuration allows cross-service communication

#### Test Timeouts
If tests timeout:
1. Check if services are overloaded
2. Verify database connectivity
3. Increase timeout values in test scripts if needed

### Debug Mode
For verbose debugging, modify the test scripts to set:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Expected Results

### Full Test Suite Success
```
📊 FINAL TEST SUMMARY
============================================================
   API Endpoints Tests: ✅ PASSED
   Integration Tests: ✅ PASSED

   Test Suites: 2/2 passed
🎉 ALL TEST SUITES PASSED!
```

### Individual Test Success Rates
- **API Endpoint Tests**: Should achieve 100% (7/7 tests)
- **Integration Tests**: Should achieve 100% (6/6 tests)

## 🔧 Configuration

### Test Configuration
Edit the configuration constants in test files:

```python
# test_whatsapp_api_endpoints.py
BACKEND_URL = "http://localhost:8000"
TEST_PHONE_NUM = "1234567890"

# test_integration_whatsapp_backend.py
WHATSAPP_URL = "http://localhost:8001"
BACKEND_URL = "http://localhost:8000"
TEST_PHONE_NUM = "9876543210"
TEST_PHONE_NUMBER_ID = "397822203424751"  # From .env file
```

### Environment Variables
Tests read from the same `.env` file as the services:
- `META_BUSINESS_PHONE_NUMBER_ID`: Used for webhook validation
- `META_WEBHOOK_VERIFY_TOKEN`: Used for webhook verification tests

## 📝 Adding New Tests

### API Endpoint Tests
Add new test methods to `WhatsAppAPITester` class:
```python
def test_new_endpoint(self) -> bool:
    """Test new API endpoint."""
    test_name = "New Endpoint Test"
    # ... test implementation
    self.log_test_result(test_name, success, message, response_data)
    return success
```

### Integration Tests
Add new test methods to `WhatsAppIntegrationTester` class:
```python
def test_new_integration(self) -> bool:
    """Test new integration scenario."""
    # ... test implementation
    return success
```

Don't forget to add new tests to the `run_all_tests` method!

## 📞 Support

If you encounter issues:
1. Check the log files for detailed error messages
2. Verify both services are running and healthy
3. Confirm environment configuration matches test expectations
4. Review the troubleshooting section above

The test suite is designed to provide comprehensive validation of the WhatsApp microservice implementation and should help identify integration issues early in the development process.