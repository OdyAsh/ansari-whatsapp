# Claude Code Instructions for ansari-whatsapp

## Project Context
This is the `ansari-whatsapp` microservice that handles WhatsApp webhook requests and communicates with the `ansari-backend` service.

## Important Project-Specific Instructions

### Package Management
**CRITICAL: This project uses `uv` for package management, NOT `pip`!**

- ✅ **Correct:** `uv add package-name`
- ✅ **Correct:** `uv remove package-name`
- ✅ **Correct:** `uv sync`
- ❌ **Wrong:** `pip install package-name`
- ❌ **Wrong:** `pip uninstall package-name`

### Dependencies Installation
- **Add new dependencies:** `uv add pytest` (not `pip install pytest`)
- **Add dev dependencies:** `uv add --dev pytest`
- **Sync dependencies:** `uv sync`

### Virtual Environment
- The project uses `.venv` created by `uv`
- Activation: `.venv/Scripts/python.exe` (Windows) or `.venv/bin/python` (Unix)

### Test Framework
- **Framework:** pytest (not unittest)
- **Pattern:** Follow backend test patterns (pytest + TestClient + fixtures)
- **Installation:** `uv add pytest`
- **Run tests:** `pytest tests/ -v`

### Security Requirements
- **Environment Variables:** Load sensitive data from `.env` file using `get_env_var()`
- **Logging:** Always mask sensitive content using `mask_sensitive_data()`
- **No Hardcoded Secrets:** Never put tokens, keys, or phone numbers directly in code

### Test Structure
- `tests/test_whatsapp_service.py` - WhatsApp service webhook tests (no external dependencies)
- `tests/test_utils.py` - Secure logging utilities
- `pytest.ini` - pytest configuration

**NOTE:** WhatsApp API endpoint tests have been moved to `ansari-backend/tests/unit/test_whatsapp_api_endpoints.py` since they test backend endpoints, not WhatsApp webhook endpoints. This allows them to use TestClient without external server dependencies.

### Streaming Endpoint Testing
The `/api/v2/whatsapp/messages/process` endpoint streams responses. Tests should:
- Collect the **complete** streaming response (not just first chunk)
- Validate streaming performance, timing, and content
- Test timeout scenarios and error handling

### Environment Variables Required
```env
META_WEBHOOK_VERIFY_TOKEN=your_verify_token
META_BUSINESS_PHONE_NUMBER_ID=your_phone_id
```

### Services Dependencies
- **ansari-backend:** Must be running on `http://localhost:8000`
- **ansari-whatsapp:** Must be running on `http://localhost:8001`

## Common Commands
```bash
# Install dependencies
uv add package-name

# Run WhatsApp service tests (this repo)
pytest tests/ -v
pytest tests/test_whatsapp_service.py -v
pytest tests/ -m integration -v

# Run WhatsApp API tests (ansari-backend repo)
cd ../ansari-backend
pytest tests/unit/test_whatsapp_api_endpoints.py -v
pytest tests/unit/test_whatsapp_api_endpoints.py -m streaming -v

# Run servers
.venv/Scripts/python.exe src/ansari_whatsapp/app/main.py
```

## Recent Changes
- Refactored all tests to use pytest + TestClient pattern
- Added comprehensive streaming endpoint testing
- Implemented secure logging with sensitive data masking
- Added proper environment variable handling
- All security issues resolved (no hardcoded secrets)

**Remember: Always use `uv` for package management in this project!**