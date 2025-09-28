# Main WhatsApp API application
"""
FastAPI application for handling WhatsApp webhook requests.

This application serves as a wrapper around the Ansari backend API,
handling incoming webhook requests from the WhatsApp Business API
and forwarding them to the Ansari backend for processing.

NOTE: the `BackgroundTasks` logic is inspired by this issue and chat (respectively):
https://stackoverflow.com/questions/72894209/whatsapp-cloud-api-sending-old-message-inbound-notification-multiple-time-on-my
https://www.perplexity.ai/search/explain-fastapi-s-backgroundta-rnpU7D19QpSxp2ZOBzNUyg
"""

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, Response

from ansari_whatsapp.presenters.whatsapp_presenter import WhatsAppPresenter, extract_relevant_whatsapp_message_details
from ansari_whatsapp.utils.whatsapp_logger import get_logger
from ansari_whatsapp.utils.config import get_settings
from ansari_whatsapp.utils.general_helpers import CORSMiddlewareWithLogging

logger = get_logger(__name__)

# TODO NOW: test , if no httpx.readtimeout occurs, then understand async def process_message(request: MessageProcessing)
#   and check other TODO NOWs


# TODO NOW OLD: see why ansari prod. responds when sending msg to ansari test (i think bec. we no add !d ?)
#   Done: We need to apply is_target_business_number in prod environment. Otherwise, sending any message in local/staging/prod
#   will also send it to rest of platforms
# TODO NOW OLD: see why ansari-backend (local) responds, but msg isn't recevied by ansari-whatsapp local
#   (i gues bec. ansari-backend is not in origins list?)
# e.g of error:
r"""
Traceback (most recent call last):

  File "D:\CS\projects\ansari\ansari-whatsapp\src\ansari_whatsapp\utils\ansari_client.py", line 164, in process_message
    response = await client.post(
                     │      └ <function AsyncClient.post at 0x000001602D0EF740>
                     └ <httpx.AsyncClient object at 0x000001602E912B10>

  File "D:\CS\projects\ansari\ansari-whatsapp\.venv\Lib\site-packages\httpx\_client.py", line 1859, in post
    return await self.request(
                 │    └ <function AsyncClient.request at 0x000001602D0EF100>
                 └ <httpx.AsyncClient object at 0x000001602E912B10>
  File "D:\CS\projects\ansari\ansari-whatsapp\.venv\Lib\site-packages\httpx\_client.py", line 1540, in request
    return await self.send(request, auth=auth, follow_redirects=follow_redirects)
                 │    │    │             │                      └ <httpx._client.UseClientDefault object at 0x000001602D0697F0>
                 │    │    │             └ <httpx._client.UseClientDefault object at 0x000001602D0697F0>
                 │    │    └ <Request('POST', 'http://localhost:8000/api/v2/whatsapp/messages/process')>
                 │    └ <function AsyncClient.send at 0x000001602D0EF2E0>
                 └ <httpx.AsyncClient object at 0x000001602E912B10>
  File "D:\CS\projects\ansari\ansari-whatsapp\.venv\Lib\site-packages\httpx\_client.py", line 1629, in send
    response = await self._send_handling_auth(
                     │    └ <function AsyncClient._send_handling_auth at 0x000001602D0EF380>
                     └ <httpx.AsyncClient object at 0x000001602E912B10>
  File "D:\CS\projects\ansari\ansari-whatsapp\.venv\Lib\site-packages\httpx\_client.py", line 1657, in _send_handling_auth
    response = await self._send_handling_redirects(
                     │    └ <function AsyncClient._send_handling_redirects at 0x000001602D0EF420>
                     └ <httpx.AsyncClient object at 0x000001602E912B10>
  File "D:\CS\projects\ansari\ansari-whatsapp\.venv\Lib\site-packages\httpx\_client.py", line 1694, in _send_handling_redirects
    response = await self._send_single_request(request)
                     │    │                    └ <Request('POST', 'http://localhost:8000/api/v2/whatsapp/messages/process')>
                     │    └ <function AsyncClient._send_single_request at 0x000001602D0EF4C0>
                     └ <httpx.AsyncClient object at 0x000001602E912B10>
  File "D:\CS\projects\ansari\ansari-whatsapp\.venv\Lib\site-packages\httpx\_client.py", line 1730, in _send_single_request
    response = await transport.handle_async_request(request)
                     │         │                    └ <Request('POST', 'http://localhost:8000/api/v2/whatsapp/messages/process')>
                     │         └ <function AsyncHTTPTransport.handle_async_request at 0x000001602D0EC040>
                     └ <httpx.AsyncHTTPTransport object at 0x000001602E913820>
  File "D:\CS\projects\ansari\ansari-whatsapp\.venv\Lib\site-packages\httpx\_transports\default.py", line 393, in handle_async_request
    with map_httpcore_exceptions():
         └ <function map_httpcore_exceptions at 0x000001602D0DB600>
  File "C:\Users\ashra\AppData\Roaming\uv\python\cpython-3.13.2-windows-x86_64-none\Lib\contextlib.py", line 162, in __exit__
    self.gen.throw(value)
    │    │   │     └ ReadTimeout(TimeoutError())
    │    │   └ <method 'throw' of 'generator' objects>
    │    └ <generator object map_httpcore_exceptions at 0x000001602E9B4540>
    └ <contextlib._GeneratorContextManager object at 0x000001602E9A56A0>
  File "D:\CS\projects\ansari\ansari-whatsapp\.venv\Lib\site-packages\httpx\_transports\default.py", line 118, in map_httpcore_exceptions
    raise mapped_exc(message) from exc
          │          └ ''
          └ <class 'httpx.ReadTimeout'>

httpx.ReadTimeout
"""

# Create FastAPI application
app = FastAPI(
    title="Ansari WhatsApp API",
    description="API for handling WhatsApp webhook requests for the Ansari service",
    version="1.0.0",
)

# Add CORS middleware with logging
app.add_middleware(
    CORSMiddlewareWithLogging,
    allow_origins=get_settings().ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint for health checks."""
    return {"status": "ok", "message": "Ansari WhatsApp service is running"}


@app.get("/whatsapp/v1")
async def verification_webhook(request: Request) -> str | None:
    """
    Handles the WhatsApp webhook verification request.

    Args:
        request (Request): The incoming HTTP request.

    Returns:
        Optional[str]: The challenge string if verification is successful, otherwise raises an HTTPException.
    """
    mode = request.query_params.get("hub.mode")
    verify_token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    logger.debug(f"Verification webhook received: {mode=}, {verify_token=}, {challenge=}")

    if mode and verify_token:
        if mode == "subscribe" and verify_token == get_settings().META_WEBHOOK_VERIFY_TOKEN.get_secret_value():
            logger.info("WHATSAPP WEBHOOK VERIFIED SUCCESSFULLY!")
            # Note: Challenge must be wrapped in an HTMLResponse for Meta to accept and verify the callback
            return HTMLResponse(challenge)
        logger.error("Verification failed: Invalid token or mode")
        raise HTTPException(status_code=403, detail="Forbidden")
    raise HTTPException(status_code=400, detail="Bad Request")


@app.post("/whatsapp/v1")
async def main_webhook(request: Request, background_tasks: BackgroundTasks) -> Response:
    """
    Handles the incoming WhatsApp webhook message.

    Args:
        request (Request): The incoming HTTP request.
        background_tasks (BackgroundTasks): The background tasks to be executed.

    Returns:
        Response: HTTP response with status code 200.
    """
    # Wait for the incoming webhook message to be received as JSON
    data = await request.json()

    # Extract message details from the webhook payload using the standalone function
    try:
        (
            is_status,
            is_target_business_number,
            from_whatsapp_number,
            incoming_msg_type,
            incoming_msg_body,
            message_id,
            message_unix_time,
        ) = await extract_relevant_whatsapp_message_details(data)

        # Check if this webhook is intended for our WhatsApp business phone number
        if not is_target_business_number:
            logger.debug("Ignoring webhook not intended for our WhatsApp business number")
            return Response(status_code=200)

        # Terminate if the incoming message is a status message (e.g., "delivered")
        if is_status:
            logger.debug("Ignoring status update message (e.g., delivered, read)")
            # This is a status message, not a user message, so doesn't need processing
            return Response(status_code=200)

        logger.debug(f"Incoming whatsapp webhook message from {from_whatsapp_number}")
    except Exception as e:
        logger.error(f"Error extracting message details: {e}")
        return Response(status_code=200)

    # Create a user-specific presenter instance for this request
    user_presenter = WhatsAppPresenter(
        user_phone_num=from_whatsapp_number,
        incoming_msg_type=incoming_msg_type,
        incoming_msg_body=incoming_msg_body,
        message_id=message_id,
        message_unix_time=message_unix_time,
    )

    # Check if the WhatsApp service is enabled
    if get_settings().WHATSAPP_UNDER_MAINTENANCE:
        # Inform the user that the service is down for maintenance
        background_tasks.add_task(
            user_presenter.send_whatsapp_message,
            "Ansari for WhatsApp is down for maintenance, please try again later or visit our website at https://ansari.chat.",
        )
        return Response(status_code=200)

    # Temporarycorner case while locally developing:
    #   Since the staging server is always running,
    #   and since we currently have the same testing number for both staging and local testing,
    #   therefore we need an indicator that a message is meant for a dev who's testing locally now
    #   and not for the staging server.
    #   This is done by prefixing the message with "!d " (e.g., "!d what is ansari?")
    # NOTE: Obviously, this temp. solution will be removed when we get a dedicated testing number for staging testing.
    if get_settings().DEPLOYMENT_TYPE == "staging" and incoming_msg_body.get("body", "").startswith("!d "):
        logger.debug("Incoming message is meant for a dev who's testing locally now, so will not process it in staging...")
        return Response(status_code=200)

    # Start the typing indicator loop that will continue until message is processed
    background_tasks.add_task(
        user_presenter.send_typing_indicator_then_start_loop,
    )

    # Check if there are more than xx hours have passed from the user's message to the current time
    # If so, send a message to the user and return
    if user_presenter.is_message_too_old():
        return Response(status_code=200)  # TODO: Remove
        response_msg = "Sorry, your message "
        user_msg_start = " ".join(incoming_msg_body.get("body", "").split(" ")[:5])
        if user_msg_start:
            response_msg_cont = ' "' + user_msg_start + '" '
        else:
            response_msg_cont = " "
        response_msg = f"Sorry, your message{response_msg_cont}is too old. Please send a new message."
        background_tasks.add_task(
            user_presenter.send_whatsapp_message,
            response_msg,
        )
        return Response(status_code=200)

    # Check if the user's phone number is stored and register if not
    # Returns false if user's not found and their registration fails
    user_found: bool = await user_presenter.check_and_register_user()
    if not user_found:
        background_tasks.add_task(
            user_presenter.send_whatsapp_message, "Sorry, we couldn't register you to our database. Please try again later."
        )
        return Response(status_code=200)

    # Check if the incoming message is a location
    if incoming_msg_type == "location":
        background_tasks.add_task(
            user_presenter.handle_location_message,
        )
        return Response(status_code=200)

    # Check if the incoming message is a media type other than text
    if incoming_msg_type != "text":
        background_tasks.add_task(
            user_presenter.handle_unsupported_message,
        )
        return Response(status_code=200)

    # Process text messages sent by the WhatsApp user
    background_tasks.add_task(
        user_presenter.handle_text_message,
    )

    return Response(status_code=200)


if __name__ == "__main__":
    # This block is executed when the script is run directly
    # To run with auto-reload on .env file changes, use:
    # uvicorn src.ansari_whatsapp.app.main:app --reload --reload-include .env
    import uvicorn
    import os

    settings = get_settings()

    # Determine module path for uvicorn dynamically
    #   (E.g.: ansari_whatsapp.app.main:app)
    file_path = os.path.abspath(__file__)
    module_path = os.path.relpath(file_path, os.getcwd())
    module_name = module_path.replace(os.sep, ".").replace(".py", "").replace("src.", "", 1) + ":app"
    logger.debug(f"Running FastAPI app with module name: {module_name}")

    # Run the FastAPI app with uvicorn
    uvicorn.run(
        module_name,  # Dynamically constructed module path
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        reload_includes=[".env"],  # Watch .env file for changes
        log_level=get_settings().LOGGING_LEVEL.lower(),
    )
