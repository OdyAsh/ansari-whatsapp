# Ansari WhatsApp Service

This service handles WhatsApp integration for the Ansari backend, providing a dedicated service for processing WhatsApp messages and communicating with the main Ansari backend.

## Overview

The Ansari WhatsApp service is designed as a separate microservice that:

1. Receives webhook events from the WhatsApp Business API
2. Processes incoming messages
3. Communicates with the main Ansari backend API
4. Sends responses back to WhatsApp users

By separating the WhatsApp functionality into its own service, we can:
- Scale the WhatsApp service independently
- Simplify the main Ansari backend codebase
- Make deployments and updates easier
- Improve testing and maintenance

## Setup

### Prerequisites

- Python 3.8 or higher
- Access to the WhatsApp Business API
- A running instance of the Ansari backend API

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd ansari-whatsapp
   ```

2. Run the setup script:
   - On Linux/Mac:
     ```
     ./setup.sh
     ```
   - On Windows:
     ```
     setup.bat
     ```

3. Edit the `.env` file with your configuration settings:
   ```
   # Update these with your values
   META_BUSINESS_PHONE_NUMBER_ID=your_phone_number_id
   META_ACCESS_TOKEN_FROM_SYS_USER=your_access_token
   META_WEBHOOK_VERIFY_TOKEN=your_verify_token
   BACKEND_SERVER_URL=http://your-ansari-backend:8000
   ```

## Running the Service

### Development Mode

```
python -m src.ansari_whatsapp.app.main
```

This will start the service on port 8001 (or the port specified in your .env file).

### Using Docker

To build and run the Docker container:

```
docker build -t ansari-whatsapp .
docker run -p 8001:8001 --env-file .env ansari-whatsapp
```

## API Endpoints

The service exposes the following endpoints:

- `GET /`: Health check endpoint
- `GET /whatsapp/v1`: Webhook verification endpoint for WhatsApp
- `POST /whatsapp/v1`: Main webhook endpoint for receiving WhatsApp messages

## Architecture

The service follows a clean architecture pattern:

- `app/`: Contains the FastAPI application and endpoints
- `presenters/`: Contains the WhatsApp presenter for handling WhatsApp interactions
- `utils/`: Contains utility modules for logging, configuration, and API client

## Integration with Ansari Backend

The WhatsApp service acts as a client to the Ansari backend, making API calls for:

1. User registration and verification
2. Creating and managing chat threads
3. Processing messages and generating responses
4. Storing user information such as location

The Ansari backend should expose endpoints specifically for WhatsApp integration, which are called by this service.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| HOST | Host to bind the server to | 0.0.0.0 |
| PORT | Port to run the server on | 8001 |
| BACKEND_SERVER_URL | URL of the Ansari backend API | http://localhost:8000 |
| META_API_VERSION | WhatsApp API version | v21.0 |
| META_BUSINESS_PHONE_NUMBER_ID | Your WhatsApp business phone number ID | (required) |
| META_ACCESS_TOKEN_FROM_SYS_USER | Access token for WhatsApp API | (required) |
| META_WEBHOOK_VERIFY_TOKEN | Verify token for WhatsApp webhook | (required) |
| WHATSAPP_CHAT_RETENTION_HOURS | Hours to retain chat history | 3 |
| DEV_MODE | Enable development mode | false |

## Troubleshooting

Logs are stored in the `logs/` directory. Check these logs for any errors or issues.

Common issues:
- WhatsApp API connection problems
- Missing or invalid environment variables
- Connection issues with the Ansari backend