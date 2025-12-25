"""
Google Sheets client for storing call results.
"""
import json
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials

from app.config import settings
from app.core.models import CallSession
from app.utils.logging import logger
from app.utils.time import format_timestamp


class GoogleSheetsClient:
    """Client for writing call results to Google Sheets."""

    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    HEADERS = [
        "timestamp",
        "call_id",
        "phone",
        "status",
        "final_disposition",
        "duration_sec",
        "short_summary",
        "transcript"
    ]

    def __init__(
        self,
        spreadsheet_id: Optional[str] = None,
        credentials_json: Optional[str] = None,
        credentials_file: Optional[str] = None
    ):
        """
        Initialize Google Sheets client.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            credentials_json: Service account credentials as JSON string
            credentials_file: Path to service account credentials JSON file
        """
        self.spreadsheet_id = spreadsheet_id or settings.GOOGLE_SHEETS_SPREADSHEET_ID
        self.credentials_json = credentials_json or settings.GOOGLE_CREDENTIALS_JSON
        self.credentials_file = credentials_file or settings.GOOGLE_CREDENTIALS_FILE

        self.client: Optional[gspread.Client] = None
        self.worksheet: Optional[gspread.Worksheet] = None

        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize gspread client and connect to worksheet."""
        try:
            # Load credentials
            if self.credentials_json:
                # Parse JSON string
                creds_dict = json.loads(self.credentials_json)
                credentials = Credentials.from_service_account_info(
                    creds_dict,
                    scopes=self.SCOPES
                )
            elif self.credentials_file:
                # Load from file
                credentials = Credentials.from_service_account_file(
                    self.credentials_file,
                    scopes=self.SCOPES
                )
            else:
                raise ValueError(
                    "Either GOOGLE_CREDENTIALS_JSON or GOOGLE_CREDENTIALS_FILE must be provided"
                )

            # Authorize and open spreadsheet
            self.client = gspread.authorize(credentials)
            spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            self.worksheet = spreadsheet.sheet1  # Use first sheet

            # Initialize headers if sheet is empty
            self._ensure_headers()

            logger.info(f"Connected to Google Sheets: {self.spreadsheet_id}")

        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets client: {e}")
            raise

    def _ensure_headers(self) -> None:
        """Ensure the first row contains headers."""
        try:
            # Check if first row is empty or doesn't match headers
            first_row = self.worksheet.row_values(1)

            if not first_row or first_row != self.HEADERS:
                # Set headers
                self.worksheet.update('A1:H1', [self.HEADERS])
                logger.info("Initialized headers in Google Sheets")

        except Exception as e:
            logger.warning(f"Failed to ensure headers: {e}")

    def write_call_result(self, call_session: CallSession) -> None:
        """
        Write call result to Google Sheets.

        Args:
            call_session: Completed call session

        Raises:
            Exception: If writing fails after retries
        """
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                # Prepare row data
                timestamp = format_timestamp(call_session.ended_at) if call_session.ended_at else ""
                call_id = str(call_session.id)
                phone = call_session.phone
                status = call_session.status.value
                disposition = call_session.final_disposition.value if call_session.final_disposition else ""
                duration = call_session.duration_sec if call_session.duration_sec is not None else 0
                summary = call_session.short_summary or ""
                transcript = call_session.get_transcript_text()

                row = [
                    timestamp,
                    call_id,
                    phone,
                    status,
                    disposition,
                    duration,
                    summary,
                    transcript
                ]

                # Append row
                self.worksheet.append_row(row, value_input_option='RAW')

                logger.info(
                    f"Wrote call result to Google Sheets | "
                    f"call_id={call_id} | "
                    f"status={status} | "
                    f"disposition={disposition}"
                )
                return

            except Exception as e:
                retry_count += 1
                logger.error(
                    f"Failed to write to Google Sheets (attempt {retry_count}/{max_retries}): {e}"
                )

                if retry_count >= max_retries:
                    logger.error(f"Max retries reached, failed to write call result for {call_session.id}")
                    # Optionally: save to local file as fallback
                    self._save_to_fallback_file(call_session)
                    raise

                # Wait before retry (simple exponential backoff)
                import time
                time.sleep(2 ** retry_count)

    def _save_to_fallback_file(self, call_session: CallSession) -> None:
        """
        Save call result to local JSON file as fallback.

        Args:
            call_session: Call session to save
        """
        try:
            import os
            from datetime import datetime

            fallback_dir = "fallback_results"
            os.makedirs(fallback_dir, exist_ok=True)

            filename = f"{fallback_dir}/call_{call_session.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(call_session.model_dump(mode='json'), f, ensure_ascii=False, indent=2)

            logger.info(f"Saved call result to fallback file: {filename}")

        except Exception as e:
            logger.error(f"Failed to save to fallback file: {e}")
