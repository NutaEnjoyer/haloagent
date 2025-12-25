"""
Call Orchestrator - manages the lifecycle of calls.
"""
import asyncio
import re
from typing import Optional
from uuid import UUID

from app.config import settings
from app.core.dialog_manager import DialogManager
from app.core.streaming_dialog_manager import StreamingDialogManager
from app.core.models import CallSession, CallStatus, FinalDisposition
from app.integrations.google_sheets import GoogleSheetsClient
from app.integrations.openai_client import OpenAIClient
from app.integrations.telephony_base import TelephonyAdapter, TelephonyEvent
from app.utils.logging import logger, log_call_event
from app.utils.time import utcnow


class CallOrchestrator:
    """Orchestrates call creation, management, and finalization."""

    PHONE_PATTERN = re.compile(r"^(\+7|8)\d{10}$")

    def __init__(
        self,
        telephony_adapter: TelephonyAdapter,
        openai_client: OpenAIClient,
        sheets_client: GoogleSheetsClient
    ):
        """
        Initialize Call Orchestrator.

        Args:
            telephony_adapter: Adapter for telephony operations
            openai_client: OpenAI client for AI operations
            sheets_client: Google Sheets client for storing results
        """
        self.telephony = telephony_adapter
        self.openai = openai_client
        self.sheets = sheets_client

        # Dialog managers
        self.dialog_manager = DialogManager(
            openai_client=openai_client,
            telephony_adapter=telephony_adapter
        )

        # Streaming dialog manager (Phase 2)
        self.streaming_dialog_manager = StreamingDialogManager(
            voximplant_adapter=telephony_adapter,
            openai_api_key=openai_client.api_key
        )

        # In-memory storage for active calls
        self.active_calls: dict[str, CallSession] = {}
        self._lock = asyncio.Lock()

    def create_call(self, phone: str) -> CallSession:
        """
        Create a new call session.

        Args:
            phone: Phone number to call

        Returns:
            Created CallSession

        Raises:
            ValueError: If phone number is invalid
        """
        # Validate phone number
        if not self.PHONE_PATTERN.match(phone):
            raise ValueError(f"Invalid phone number format: {phone}")

        # Normalize phone number to +7 format
        if phone.startswith("8"):
            phone = "+7" + phone[1:]

        # Create call session
        call_session = CallSession(phone=phone)

        # Store in active calls
        self.active_calls[str(call_session.id)] = call_session

        log_call_event(logger, "call_created", str(call_session.id), phone=phone)

        return call_session

    async def start_call(self, call_id: str) -> None:
        """
        Start an outbound call.

        Args:
            call_id: Call session ID
        """
        call_session = self.active_calls.get(call_id)
        if not call_session:
            logger.error(f"Call session not found: {call_id}")
            return

        try:
            log_call_event(logger, "call_starting", call_id, phone=call_session.phone)

            # Initiate call via telephony provider
            await self.telephony.initiate_call(call_id, call_session.phone)

        except Exception as e:
            logger.error(f"Failed to start call | call_id={call_id} | error={e}")
            call_session.status = CallStatus.FAILED
            call_session.ended_at = utcnow()
            await self.finalize_call(call_id)

    async def handle_telephony_event(
        self,
        call_id: str,
        event: TelephonyEvent,
        reason: Optional[str] = None
    ) -> None:
        """
        Handle events from telephony provider.

        Args:
            call_id: Call session ID
            event: Telephony event
            reason: Optional reason/description
        """
        call_session = self.active_calls.get(call_id)
        if not call_session:
            logger.warning(f"Received event for unknown call | call_id={call_id} | event={event.value}")
            return

        log_call_event(
            logger,
            f"telephony_event_{event.value}",
            call_id,
            reason=reason or "none"
        )

        try:
            if event == TelephonyEvent.RINGING:
                call_session.status = CallStatus.DIALING

            elif event == TelephonyEvent.ANSWERED:
                call_session.status = CallStatus.IN_PROGRESS
                call_session.started_at = utcnow()

                # Dialog is managed by Voximplant scenario via HTTP callbacks
                # Do NOT start dialog manager here
                logger.info(f"Call answered, dialog managed by Voximplant scenario | call_id={call_id}")

            elif event in [TelephonyEvent.BUSY, TelephonyEvent.NO_ANSWER]:
                call_session.status = CallStatus.NO_ANSWER
                call_session.ended_at = utcnow()
                await self.finalize_call(call_id)

            elif event == TelephonyEvent.ERROR:
                call_session.status = CallStatus.FAILED
                call_session.ended_at = utcnow()
                await self.finalize_call(call_id)

            elif event == TelephonyEvent.HANGUP:
                if call_session.status == CallStatus.IN_PROGRESS:
                    call_session.status = CallStatus.COMPLETED
                call_session.ended_at = utcnow()
                await self.finalize_call(call_id)

        except Exception as e:
            logger.error(
                f"Error handling telephony event | "
                f"call_id={call_id} | event={event.value} | error={e}",
                exc_info=True
            )

    async def _run_dialog_and_finalize(self, call_id: str) -> None:
        """
        Run dialog and finalize call when done.

        Always uses Streaming Dialog Manager with OpenAI Realtime API.

        Args:
            call_id: Call session ID
        """
        call_session = self.active_calls.get(call_id)
        if not call_session:
            return

        try:
            # Use regular Dialog Manager (non-streaming mode)
            # TODO: Fix Node.js bridge for streaming mode
            logger.info(f"Using regular dialog | call_id={call_id}")

            await self.dialog_manager.run_dialog(call_id, call_session)

            # Mark as completed
            call_session.status = CallStatus.COMPLETED
            call_session.ended_at = utcnow()

            # Hangup
            await self.telephony.hangup(call_id)

        except Exception as e:
            logger.error(f"Dialog failed | call_id={call_id} | error={e}", exc_info=True)
            call_session.status = CallStatus.FAILED
            call_session.ended_at = utcnow()

        finally:
            await self.finalize_call(call_id)

    async def finalize_call(self, call_id: str) -> None:
        """
        Finalize call: classify, calculate duration, save to Sheets.

        Args:
            call_id: Call session ID
        """
        async with self._lock:
            call_session = self.active_calls.get(call_id)
            if not call_session:
                logger.warning(f"Cannot finalize unknown call: {call_id}")
                return

            try:
                log_call_event(logger, "call_finalizing", call_id, status=call_session.status.value)

                # Set ended_at if not set
                if not call_session.ended_at:
                    call_session.ended_at = utcnow()

                # Calculate duration
                call_session.calculate_duration()

                # Classify call if there was a dialog
                if call_session.transcript:
                    try:
                        transcript_text = call_session.get_transcript_text()
                        disposition, summary = await self.openai.classify_call(transcript_text)

                        call_session.final_disposition = disposition
                        call_session.short_summary = summary

                        log_call_event(
                            logger,
                            "call_classified",
                            call_id,
                            disposition=disposition.value,
                            summary=summary
                        )

                    except Exception as e:
                        logger.error(f"Classification failed | call_id={call_id} | error={e}")
                        call_session.final_disposition = FinalDisposition.UNKNOWN
                        call_session.short_summary = f"Ошибка классификации: {str(e)}"

                else:
                    # No dialog, set defaults
                    call_session.final_disposition = FinalDisposition.UNKNOWN
                    call_session.short_summary = f"Не дозвонились: статус {call_session.status.value}"
                    call_session.duration_sec = 0

                # Write to Google Sheets
                try:
                    self.sheets.write_call_result(call_session)
                    log_call_event(logger, "call_saved_to_sheets", call_id)

                except Exception as e:
                    logger.error(
                        f"Failed to write to Google Sheets | call_id={call_id} | error={e}",
                        exc_info=True
                    )
                    # Continue anyway, data is in call_session

                # Final log
                log_call_event(
                    logger,
                    "call_finalized",
                    call_id,
                    status=call_session.status.value,
                    disposition=call_session.final_disposition.value if call_session.final_disposition else "none",
                    duration=call_session.duration_sec or 0
                )

            except Exception as e:
                logger.error(f"Error finalizing call | call_id={call_id} | error={e}", exc_info=True)

            finally:
                # Remove from active calls
                if call_id in self.active_calls:
                    del self.active_calls[call_id]
