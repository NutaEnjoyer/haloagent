"""
Mock Google Sheets client for testing without real Google Sheets.
Saves call results to local JSON files instead.
"""
import json
import os
from datetime import datetime
from pathlib import Path

from app.core.models import CallSession
from app.utils.logging import logger
from app.utils.time import format_timestamp


class MockGoogleSheetsClient:
    """Mock implementation of Google Sheets client that saves to files."""

    def __init__(self, output_dir: str = "mock_sheets_data"):
        """
        Initialize mock Google Sheets client.

        Args:
            output_dir: Directory to save mock data files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Create CSV file with headers if it doesn't exist
        self.csv_file = os.path.join(output_dir, "calls.csv")
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', encoding='utf-8') as f:
                f.write("timestamp,call_id,phone,status,final_disposition,duration_sec,short_summary,transcript\n")

        logger.info(f"[MOCK] Google Sheets client initialized (saving to {output_dir}/)")

    def write_call_result(self, call_session: CallSession) -> None:
        """
        Write call result to local files (both JSON and CSV).

        Args:
            call_session: Completed call session
        """
        try:
            call_id = str(call_session.id)

            # Save as JSON (full data)
            json_file = os.path.join(self.output_dir, f"call_{call_id}.json")
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(call_session.model_dump(mode='json'), f, ensure_ascii=False, indent=2)

            # Append to CSV (for easy viewing)
            timestamp = format_timestamp(call_session.ended_at) if call_session.ended_at else ""
            phone = call_session.phone
            status = call_session.status.value
            disposition = call_session.final_disposition.value if call_session.final_disposition else ""
            duration = call_session.duration_sec if call_session.duration_sec is not None else 0
            summary = (call_session.short_summary or "").replace('"', '""')  # Escape quotes
            transcript = call_session.get_transcript_text().replace('"', '""').replace('\n', ' | ')

            csv_line = f'"{timestamp}","{call_id}","{phone}","{status}","{disposition}",{duration},"{summary}","{transcript}"\n'

            with open(self.csv_file, 'a', encoding='utf-8') as f:
                f.write(csv_line)

            logger.info(
                f"[MOCK] Saved call result to files | "
                f"call_id={call_id} | "
                f"status={status} | "
                f"disposition={disposition} | "
                f"files={json_file}, {self.csv_file}"
            )

        except Exception as e:
            logger.error(f"[MOCK] Failed to save call result: {e}", exc_info=True)
            raise
