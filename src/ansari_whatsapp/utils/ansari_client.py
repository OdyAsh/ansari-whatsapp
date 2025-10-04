# API Client for ansari-whatsapp
"""Client for interacting with the Ansari backend API."""

import httpx

from ansari_whatsapp.utils.whatsapp_logger import logger, make_error_handler
from ansari_whatsapp.utils.config import get_settings


class AnsariClient:
    """Client for the Ansari backend API."""

    def __init__(self):
        """Initialize the Ansari API client."""
        self.settings = get_settings()
        self.base_url = self.settings.BACKEND_SERVER_URL

    @logger.catch(onerror=make_error_handler("Error registering user", {"status": "failure"}))
    async def register_user(self, phone_num: str, preferred_language: str) -> dict:
        """
        Register a new WhatsApp user with the Ansari backend.

        Args:
            phone_num (str): The user's WhatsApp phone number.
            preferred_language (str): The user's preferred language.

        Returns:
            dict: The registration result.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v2/whatsapp/users/register",
                json={
                    "phone_num": phone_num,
                    "preferred_language": preferred_language,
                },
            )
            response.raise_for_status()
            return response.json()

    @logger.catch(onerror=make_error_handler("Error checking if user exists", False))
    async def check_user_exists(self, phone_num: str) -> bool:
        """
        Check if a WhatsApp user exists in the Ansari backend.

        Args:
            phone_num (str): The user's WhatsApp phone number.

        Returns:
            bool: True if the user exists, False otherwise.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v2/whatsapp/users/exists",
                params={"phone_num": phone_num},
            )
            response.raise_for_status()
            return response.json().get("exists", False)

    @logger.catch(onerror=make_error_handler("Error updating user location", {"status": "failure"}))
    async def update_user_location(self, phone_num: str, latitude: float, longitude: float) -> dict:
        """
        Update a WhatsApp user's location in the Ansari backend.

        Args:
            phone_num (str): The user's WhatsApp phone number.
            latitude (float): The latitude of the user's location.
            longitude (float): The longitude of the user's location.

        Returns:
            dict: The update result.
        """
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/api/v2/whatsapp/users/location",
                json={
                    "phone_num": phone_num,
                    "latitude": latitude,
                    "longitude": longitude,
                },
            )
            response.raise_for_status()
            return response.json()

    @logger.catch(onerror=make_error_handler("Error creating thread", {"error": ""}))
    async def create_thread(self, phone_num: str, title: str) -> dict:
        """
        Create a new thread for a WhatsApp user in the Ansari backend.

        Args:
            phone_num (str): The user's WhatsApp phone number.
            title (str): The title of the thread.

        Returns:
            dict: The creation result with thread_id.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v2/whatsapp/threads",
                json={"phone_num": phone_num, "title": title},
            )
            response.raise_for_status()
            return response.json()

    @logger.catch(onerror=make_error_handler("Error getting thread history", {"error": ""}))
    async def get_thread_history(self, phone_num: str, thread_id: str) -> dict:
        """
        Get the message history for a WhatsApp user's thread from the Ansari backend.

        Args:
            phone_num (str): The user's WhatsApp phone number.
            thread_id (str): The ID of the thread.

        Returns:
            dict: The thread history.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v2/whatsapp/threads/{thread_id}/history",
                params={"phone_num": phone_num},
            )
            response.raise_for_status()
            return response.json()

    @logger.catch(onerror=make_error_handler("Error getting last thread info", {"thread_id": None, "last_message_time": None}))
    async def get_last_thread_info(self, phone_num: str) -> dict:
        """
        Get information about the last active thread for a WhatsApp user.

        Args:
            phone_num (str): The user's WhatsApp phone number.

        Returns:
            dict: The thread info with thread_id and last_message_time.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v2/whatsapp/threads/last",
                params={"phone_num": phone_num},
            )
            response.raise_for_status()
            return response.json()

    @logger.catch(
        onerror=make_error_handler(
            "Error processing message", "An error occurred while processing your message. Please try again later."
        )
    )
    async def process_message(self, phone_num: str, thread_id: str, message: str) -> str:
        """
        Process a message from a WhatsApp user with the Ansari backend.
        This method streams the response from the backend to avoid timeout issues.

        Args:
            phone_num (str): The user's WhatsApp phone number.
            thread_id (str): The ID of the thread.
            message (str): The message to process.

        Returns:
            str: The complete response message.
        """
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/api/v2/whatsapp/messages/process"
            data = {
                "phone_num": phone_num,
                "thread_id": thread_id,
                "message": message,
            }

            # Use stream=True to receive the response as a stream
            async with client.stream("POST", url, json=data, timeout=60.0) as response:
                if response.status_code != 200:
                    error_detail = await response.aread()
                    logger.error(f"Error from backend API: {error_detail}")
                    raise httpx.HTTPStatusError(
                        f"Error processing message: {error_detail}", request=response.request, response=response
                    )

                # Accumulate the full response as we receive chunks
                full_response = ""
                async for chunk in response.aiter_text():
                    # Each chunk is a token from the streaming response
                    if chunk:
                        full_response += chunk

                if not full_response:
                    logger.error("Received empty response from backend")
                    return ""

                return full_response
