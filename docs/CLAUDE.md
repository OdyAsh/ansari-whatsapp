# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is `ansari-whatsapp`, a Python FastAPI microservice that handles WhatsApp Business API integration for the Ansari AI assistant. The service receives webhook events from WhatsApp, processes messages, communicates with the main Ansari backend API, and sends responses back to WhatsApp users.

## Development Commands

### Setup and Installation
- **Initial setup**: `./setup.sh` (Linux/Mac) or `setup.bat` (Windows) - Creates virtual environment, installs dependencies, and sets up .env file
- **Manual setup**: `python -m venv .venv && source .venv/bin/activate && uv sync`

### Running the Application
- **Development mode**:
  1. Use ansari-whatsapp's OWN venv python: `D:\CS\projects\ansari\ansari-whatsapp\.venv\Scripts\python.exe src/ansari_whatsapp/app/main.py` - Starts server on port 8001 with auto-reload
  - Alternative: `python -m src.ansari_whatsapp.app.main`

  **IMPORTANT**: Use ansari-whatsapp's own .venv, NOT ansari-backend's .venv!

  **Note**: Direct venv python path is used because `source .venv/Scripts/activate` may not properly activate the virtual environment in bash.

  **Testing changes**: ansari-whatsapp boots up quickly, so auto-reload works reliably. You can test immediately after making changes.
- **Docker**: `docker build -t ansari-whatsapp . && docker run -p 8001:8001 --env-file .env ansari-whatsapp`
- **WhatsApp Webhook Proxy** (for local testing with Meta):
  1. In separate terminal, activate environment and cd to ansari-whatsapp root
  2. Run: `zrok reserve public localhost:8001 -n ZROK_SHARE_TOKEN` (using ZROK_SHARE_TOKEN from .env)
  3. This creates a public URL that Meta can reach to send webhook requests to your local server

### Package Management
- **Install dependencies**: `uv sync` - Installs all dependencies from pyproject.toml and uv.lock
- **Add new package**: `uv add <package>` - Adds package to dependencies and updates lock file
- **Add development dependency**: `uv add --dev <package>` - Adds package to dev dependencies
- **Remove package**: `uv remove <package>` - Removes package from dependencies
- **Create virtual environment**: `uv venv` - Creates .venv directory (if not exists)
- **Update dependencies**: `uv lock` - Updates uv.lock file with latest compatible versions

### Code Quality
- **Linting**: `ruff check .` - Uses Ruff with line length 127, targeting Python 3.10+
- **Formatting**: `ruff format .` - Auto-formats code with double quotes and 4-space indentation
- **Fix issues**: `ruff check --fix .` - Auto-fixes linting issues

### Utilities
- **Clean logs**: `./clean_logs.sh [minutes]` - Removes log entries older than specified minutes (0 = all)

## Architecture

### Directory Structure
```
src/ansari_whatsapp/
├── app/                    # FastAPI application and endpoints
│   └── main.py            # Main FastAPI app with webhook endpoints
├── presenters/            # WhatsApp interaction handlers
│   └── whatsapp_presenter.py  # Core message processing logic
└── utils/                 # Utility modules
    ├── config.py          # Pydantic settings and configuration
    ├── ansari_client.py   # HTTP client for Ansari backend API
    ├── whatsapp_logger.py # Custom logging with Rich/Loguru
    └── general_helpers.py # CORS middleware and utilities
```

### Key Components

**FastAPI Application** (`app/main.py:89-261`):
- Health check endpoint: `GET /`
- Webhook verification: `GET /whatsapp/v1`
- Message processing: `POST /whatsapp/v1`
- Uses BackgroundTasks for async message processing to prevent WhatsApp timeouts

**WhatsApp Presenter** (`presenters/whatsapp_presenter.py`):
- Handles user registration, message processing, and response generation
- Manages typing indicators and chat retention (3 hours default)
- Supports text messages, location sharing, and media type detection

**Configuration** (`utils/config.py:10-141`):
- Pydantic Settings with environment variable support
- Validates deployment type (local/staging/production)
- Auto-configures CORS origins based on deployment environment
- Manages WhatsApp API credentials and backend URL

**Ansari Client** (`utils/ansari_client.py`):
- HTTP client for communicating with the main Ansari backend
- Handles user registration, existence checks, and message processing
- Uses httpx for async requests with proper error handling

### Integration Points

The service acts as a bridge between WhatsApp Business API and the Ansari backend:
1. Receives webhooks from WhatsApp at `/whatsapp/v1`
2. Validates and processes incoming messages
3. Makes API calls to Ansari backend endpoints:
   - `/api/v2/whatsapp/users/register` - User registration
   - `/api/v2/whatsapp/messages/process` - Message processing
4. Sends responses back to WhatsApp users via Graph API

### Environment Configuration

Key environment variables (see `.env.example`):
- `BACKEND_SERVER_URL` - URL of the Ansari backend API
- `META_BUSINESS_PHONE_NUMBER_ID` - WhatsApp Business phone number ID
- `META_ACCESS_TOKEN_FROM_SYS_USER` - WhatsApp API access token
- `META_WEBHOOK_VERIFY_TOKEN` - Webhook verification token
- `DEPLOYMENT_TYPE` - Environment type (local/staging/production)
- `WHATSAPP_CHAT_RETENTION_HOURS` - Chat history retention (default: 3)

### Development Notes

- Uses Python 3.10+ with modern async/await patterns
- Implements proper error handling with Loguru decorators
- CORS middleware automatically includes backend URL and deployment-specific origins
- Local development uses zrok for webhook tunneling
- Logging configured with Rich formatting and file rotation
- No test suite currently exists - tests would need to be added