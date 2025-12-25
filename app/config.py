"""
Application configuration using Pydantic Settings.
"""
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenAI Configuration
    OPENAI_API_KEY: str
    GPT_MODEL: str = "gpt-4o"
    TTS_VOICE: str = "alloy"

    # Google Sheets Configuration
    GOOGLE_SHEETS_SPREADSHEET_ID: str
    GOOGLE_CREDENTIALS_JSON: Optional[str] = None
    GOOGLE_CREDENTIALS_FILE: Optional[str] = None

    # Telephony Provider Configuration
    TELEPHONY_API_KEY: Optional[str] = None
    TELEPHONY_CONFIG: Optional[str] = None

    # Voximplant Configuration
    VOXIMPLANT_ACCOUNT_ID: Optional[str] = None
    VOXIMPLANT_API_KEY: Optional[str] = None
    VOXIMPLANT_APPLICATION_ID: Optional[str] = None
    VOXIMPLANT_RULE_ID: Optional[str] = None
    VOXIMPLANT_CALLER_ID: str = "+74951234567"  # Default caller ID

    # Backend URL for webhooks (must be publicly accessible)
    BACKEND_URL: Optional[str] = None

    # Use Voximplant or Stub adapter
    USE_VOXIMPLANT: bool = False

    # API Security
    API_AUTH_KEY: str

    # Call Configuration
    MAX_CALL_DURATION_SEC: int = 120
    MAX_DIALOG_TURNS: int = 12

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Logging
    LOG_LEVEL: str = "INFO"

    # Testing/Development
    USE_MOCK_SHEETS: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Singleton instance
settings = Settings()
