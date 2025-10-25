# Configuration for ansari-whatsapp
"""Configuration and settings for the WhatsApp service."""

from functools import lru_cache

from pydantic import SecretStr, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class WhatsAppSettings(BaseSettings):
    """
    Settings for the WhatsApp service.

    IMPORTANT NOTE: Check `.env.examples` file for an explanation of each setting.

    Notes regarding how Pydantic Settings works:

    Field value precedence in Pydantic Settings (highest to lowest priority):

    1. CLI arguments (if cli_parse_args is enabled).
    2. Arguments passed to the Settings initializer.
    3. Environment variables.
    4. Variables from a dotenv (.env) file.
    5. Variables from the secrets directory.
    6. Default field values in the WhatsAppSettings model.

    E.g., if you set the variable `META_API_VERSION` in .env file to `v22.xyz`,
    it will override the default value of `v22.0` defined in the WhatsAppSettings model.

    For more details, refer to the Pydantic documentation:
    [https://docs.pydantic.dev/latest/concepts/pydantic_settings/#field-value-priority].

    """

    ########## Pydantic Settings Config ##########

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    ########## ansari-backend's settings ##########

    BACKEND_SERVER_URL: SecretStr

    ########### Meta Business API settings ###########

    META_API_VERSION: str = "v22.0"
    META_BUSINESS_PHONE_NUMBER_ID: SecretStr
    META_ACCESS_TOKEN_FROM_SYS_USER: SecretStr
    META_WEBHOOK_VERIFY_TOKEN: SecretStr
    META_WEBHOOK_ZROK_SHARE_TOKEN: SecretStr

    @property
    def META_API_URL(self) -> str:
        """
        Returns the Meta Graph API URL for sending WhatsApp messages.

        Format: https://graph.facebook.com/{version}/{phone-number-id}/messages
        """
        return f"https://graph.facebook.com/{self.META_API_VERSION}/{self.META_BUSINESS_PHONE_NUMBER_ID.get_secret_value()}/messages"

    ########### ansari-whatsapp's settings ##########

    DEPLOYMENT_TYPE: str = Field(
        ...,
        description="Deployment environment type",
        pattern="^(local|development|staging|production)$",
    )

    # Meta webhook response behavior
    ALWAYS_RETURN_OK_TO_META: bool = True

    # Server settings
    HOST: str = "localhost"
    PORT: int = 8001

    # CORS settings
    # NOTE: We usually don't need to set this, as the add_extra_origins validator
    #   will automatically add BACKEND_SERVER_URL and other origins as needed.
    ORIGINS: str | list[str] = ""

    # Chat settings
    WHATSAPP_UNDER_MAINTENANCE: bool = False
    WHATSAPP_CHAT_RETENTION_HOURS: int
    WHATSAPP_MESSAGE_AGE_THRESHOLD_SECONDS: int

    # Test/Development settings
    WHATSAPP_DEV_PHONE_NUM: SecretStr = SecretStr("201234567899")
    WHATSAPP_DEV_MESSAGE_ID: SecretStr = SecretStr("wamid.seventy_two_char_hash")

    # Logging settings
    LOGGING_LEVEL: str = "DEBUG"
    LOG_TEST_FILES_ONLY: bool = False

    # Service Provider settings
    MOCK_ANSARI_CLIENT: bool = False
    MOCK_META_API: bool = False

    ########### Validators ###########

    @field_validator("ORIGINS", mode="before")
    def parse_origins(cls, v):
        """Parse ORIGINS from a comma-separated string or list."""
        if isinstance(v, str):
            origins = [origin.strip() for origin in v.strip('"').split(",")]
        elif isinstance(v, list):
            origins = v
        else:
            raise ValueError(
                f"Invalid ORIGINS format: {v}. Expected a comma-separated string or a list.",
            )
        return origins

    @field_validator("ORIGINS", mode="after")
    def add_extra_origins(cls, v, info):
        """Add extra origins based on environment settings.

        Adds:
        1. In local mode: adds localhost and zrok origins
        2. In all environments: adds GitHub Actions testserver origin
        """
        origins = v.copy()

        # Add BACKEND_SERVER_URL as an origin if it's not already present
        backend_url = info.data.get("BACKEND_SERVER_URL")
        if backend_url and backend_url not in origins:
            origins.append(backend_url)

        # Add local-specific origins when in local mode
        if info.data.get("DEPLOYMENT_TYPE") == "local":
            # Add zrok origin (i.e., the webhook (callback url)) that Meta will send messages to)
            zrok_token = info.data.get("META_WEBHOOK_ZROK_SHARE_TOKEN")
            token_value = zrok_token.get_secret_value()
            # NOTE: We don't add "https://" as Meta sends request in "host" header, not "origin",
            #   and so, a value in "host" header means it won't contain the "https://" prefix
            #   However, even if you don't explicitly remove the "https://" part,
            #   apparently FastAPI will still correctly recognize the host
            webhook_origin = f"{token_value}.share.zrok.io"
            if webhook_origin not in origins:
                origins.append(webhook_origin)

        # Make sure CI/CD of GitHub Actions is allowed in all environments
        if "testserver" not in origins:
            origins.append("testserver")

        return origins


@lru_cache
def get_settings() -> WhatsAppSettings:
    """Get the application settings."""
    return WhatsAppSettings()
