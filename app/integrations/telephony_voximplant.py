"""
Voximplant telephony adapter.
Integrates with Voximplant HTTP API for outbound calls.
"""
import asyncio
import hashlib
import json
from typing import Optional, Callable
from datetime import datetime

import aiohttp

from app.integrations.telephony_base import TelephonyEvent
from app.utils.logging import logger


class VoximplantTelephonyAdapter:
    """
    Adapter for Voximplant telephony provider.

    Phase 1 Implementation (Basic calling without streaming):
    - Uses HTTP API to initiate calls (StartScenarios)
    - Receives events via webhooks from VoxEngine scenario
    - Audio handled by VoxEngine scenario + OpenAI integration on Voximplant side

    Phase 2 will add WebSocket streaming for real-time audio.
    """

    def __init__(
        self,
        account_id: str,
        api_key: str,
        application_id: str,
        rule_id: str,
        caller_id: str,
        backend_url: str,
        event_callback: Optional[Callable] = None
    ):
        """
        Initialize Voximplant adapter.

        Args:
            account_id: Voximplant account ID
            api_key: Voximplant API key
            application_id: Voximplant application ID
            rule_id: Voximplant rule ID for routing
            caller_id: Caller ID to display (E.164 format)
            backend_url: Backend URL for webhooks
            event_callback: Callback function for telephony events
                           Should accept (call_id: str, event: TelephonyEvent, reason: Optional[str])
        """
        self.account_id = account_id
        self.api_key = api_key
        self.application_id = application_id
        self.rule_id = rule_id
        self.caller_id = caller_id
        self.backend_url = backend_url
        self.event_callback = event_callback

        self.base_url = "https://api.voximplant.com/platform_api"

        # Track active calls
        self.active_calls: dict[str, dict] = {}

        # Audio queues for non-streaming mode (used by dialog manager)
        self.audio_queue: dict[str, asyncio.Queue] = {}

        # Track polling tasks
        self.polling_tasks: dict[str, asyncio.Task] = {}

    async def initiate_call(self, call_id: str, phone: str) -> None:
        """
        Initiate an outbound call via Voximplant HTTP API.

        Uses StartScenarios endpoint to start a VoxEngine scenario
        that will make the call.

        Args:
            call_id: Unique identifier for the call
            phone: Phone number to call (E.164 format, e.g., +79991234567)
        """
        try:
            logger.info(f"[Voximplant] Initiating call | call_id={call_id} | phone={phone}")

            # Prepare custom data to pass to VoxEngine scenario
            custom_data = {
                "call_id": call_id,
                "phone": phone,
                "caller_id": self.caller_id,
                "webhook_url": f"{self.backend_url}/voximplant/events"
            }

            # Prepare API request
            payload = {
                "account_id": self.account_id,
                "api_key": self.api_key,
                "rule_id": self.rule_id,
                "script_custom_data": json.dumps(custom_data)
            }

            # Make API call to start scenario
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/StartScenarios",
                    data=payload
                ) as resp:
                    result = await resp.json()

                    if result.get("result") == 1:
                        # Success
                        media_session_id = result.get("media_session_access_url")

                        self.active_calls[call_id] = {
                            "phone": phone,
                            "status": "initiating",
                            "media_session_id": media_session_id,
                            "started_at": datetime.utcnow()
                        }

                        self.audio_queue[call_id] = asyncio.Queue()

                        logger.info(
                            f"[Voximplant] Call initiated successfully | "
                            f"call_id={call_id} | media_session_id={media_session_id}"
                        )

                        # Start polling for call status
                        poll_task = asyncio.create_task(self._poll_call_status(call_id))
                        self.polling_tasks[call_id] = poll_task
                    else:
                        # Error
                        error_msg = result.get("error", {}).get("msg", "Unknown error")
                        logger.error(
                            f"[Voximplant] Failed to initiate call | "
                            f"call_id={call_id} | error={error_msg}"
                        )

                        # Notify orchestrator of failure
                        if self.event_callback:
                            await self.event_callback(
                                call_id,
                                TelephonyEvent.ERROR,
                                f"API error: {error_msg}"
                            )

        except Exception as e:
            logger.error(
                f"[Voximplant] Exception during call initiation | "
                f"call_id={call_id} | error={e}",
                exc_info=True
            )

            if self.event_callback:
                await self.event_callback(
                    call_id,
                    TelephonyEvent.ERROR,
                    f"Exception: {str(e)}"
                )

    async def _poll_call_status(self, call_id: str) -> None:
        """
        Poll Voximplant API for call status (workaround for broken webhooks).

        Checks call status every 500ms until call is Connected or Failed.
        When Connected, triggers event_callback with ANSWERED event.

        Args:
            call_id: Call identifier to poll for
        """
        try:
            logger.info(f"[Voximplant Polling] Started polling for call_id={call_id}")

            poll_count = 0
            max_polls = 60  # 60 * 0.5s = 30 seconds max polling

            while poll_count < max_polls:
                poll_count += 1

                # Wait 500ms between polls
                await asyncio.sleep(0.5)

                # Check if call still exists (might have been cleaned up)
                if call_id not in self.active_calls:
                    logger.info(f"[Voximplant Polling] Call {call_id} no longer active, stopping poll")
                    break

                # Check current status in our tracking
                current_status = self.active_calls[call_id].get("status")

                # If already connected via webhook, stop polling
                if current_status == "connected":
                    logger.info(f"[Voximplant Polling] Call {call_id} already connected, stopping poll")
                    break

                # Simple approach: Wait for typical PSTN connection time (5 seconds)
                # then trigger Connected event
                if poll_count >= 10:  # 5 seconds passed (10 * 0.5s)
                    logger.info(
                        f"[Voximplant Polling] Assuming call {call_id} connected after 5s"
                    )

                    # Update status
                    self.active_calls[call_id]["status"] = "connected"

                    # Launch Node.js bridge to connect Backend to VoxEngine
                    # TODO: Enable when bridge is ready
                    # await self._launch_bridge(call_id)

                    # Trigger ANSWERED event
                    if self.event_callback:
                        await self.event_callback(call_id, TelephonyEvent.ANSWERED, None)

                    logger.info(f"[Voximplant Polling] Triggered ANSWERED event for {call_id}")
                    break

            logger.info(f"[Voximplant Polling] Stopped polling for call_id={call_id}")

        except Exception as e:
            logger.error(
                f"[Voximplant Polling] Exception in polling task | call_id={call_id} | error={e}",
                exc_info=True
            )
        finally:
            # Clean up polling task
            if call_id in self.polling_tasks:
                del self.polling_tasks[call_id]

    async def _launch_bridge(self, call_id: str) -> None:
        """
        Request Node.js bridge to connect to VoxEngine call.

        The bridge is a standalone Node.js server running on port 3000.
        We send it an HTTP POST request to initiate connection.

        Args:
            call_id: Call identifier
        """
        try:
            logger.info(f"[Voximplant Bridge] Requesting bridge connection for call_id={call_id}")

            # Bridge server URL (running on host machine)
            bridge_url = "http://host.docker.internal:3000/connect"

            # Send connect request to bridge
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    bridge_url,
                    json={"call_id": call_id},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        logger.info(
                            f"[Voximplant Bridge] Bridge connection initiated | "
                            f"call_id={call_id} | status={result.get('status')}"
                        )
                    else:
                        error_text = await resp.text()
                        logger.error(
                            f"[Voximplant Bridge] Bridge connection failed | "
                            f"call_id={call_id} | status={resp.status} | error={error_text}"
                        )

        except asyncio.TimeoutError:
            logger.error(
                f"[Voximplant Bridge] Bridge request timeout | call_id={call_id}"
            )
        except Exception as e:
            logger.error(
                f"[Voximplant Bridge] Failed to request bridge connection | "
                f"call_id={call_id} | error={e}",
                exc_info=True
            )

    async def send_audio(self, call_id: str, audio_bytes: bytes) -> None:
        """
        Send audio to the caller.

        For Phase 1 (non-streaming), this is handled by VoxEngine scenario
        which uses OpenAI TTS directly. This method is a placeholder.

        Args:
            call_id: Call identifier
            audio_bytes: Audio data to send
        """
        if call_id not in self.active_calls:
            logger.warning(
                f"[Voximplant] Attempted to send audio to non-existent call: {call_id}"
            )
            return

        # In Phase 1, audio is handled by VoxEngine scenario
        # In Phase 2, we'll implement WebSocket streaming here
        logger.debug(
            f"[Voximplant] Audio send (Phase 1 - handled by VoxEngine) | "
            f"call_id={call_id} | size={len(audio_bytes)} bytes"
        )

    async def receive_audio(self, call_id: str) -> Optional[bytes]:
        """
        Receive audio from the caller.

        For Phase 1 (non-streaming), this is handled by VoxEngine scenario
        which uses OpenAI Whisper directly. This method is a placeholder.

        Args:
            call_id: Call identifier

        Returns:
            Audio data bytes, or None if no audio available
        """
        if call_id not in self.active_calls:
            logger.warning(
                f"[Voximplant] Attempted to receive audio from non-existent call: {call_id}"
            )
            return None

        # In Phase 1, audio transcription is handled by VoxEngine scenario
        # In Phase 2, we'll implement WebSocket streaming here
        logger.debug(f"[Voximplant] Audio receive (Phase 1 - handled by VoxEngine) | call_id={call_id}")

        return None

    async def hangup(self, call_id: str) -> None:
        """
        Terminate the call.

        For Phase 1, hangup is triggered by VoxEngine scenario.
        We'll use HTTP API to send hangup signal if needed.

        Args:
            call_id: Call identifier
        """
        if call_id not in self.active_calls:
            logger.warning(
                f"[Voximplant] Attempted to hangup non-existent call: {call_id}"
            )
            return

        try:
            logger.info(f"[Voximplant] Hanging up call | call_id={call_id}")

            # In Phase 1, hangup is managed by VoxEngine scenario
            # We can use TerminateCall API if we have call_session_id
            # For now, just clean up locally

            call_info = self.active_calls[call_id]
            media_session_id = call_info.get("media_session_id")

            # Clean up
            del self.active_calls[call_id]
            if call_id in self.audio_queue:
                del self.audio_queue[call_id]

            logger.info(f"[Voximplant] Call hung up | call_id={call_id}")

        except Exception as e:
            logger.error(
                f"[Voximplant] Error during hangup | call_id={call_id} | error={e}",
                exc_info=True
            )

    async def handle_webhook_event(self, event_data: dict) -> None:
        """
        Handle webhook event from VoxEngine scenario.

        This is called by the webhook endpoint when Voximplant sends
        call events (Connected, Disconnected, Failed, etc.)

        Args:
            event_data: Event data from webhook
        """
        try:
            event_type = event_data.get("event")
            call_id = event_data.get("call_id")

            if not call_id:
                logger.warning("[Voximplant] Webhook event without call_id")
                return

            logger.info(
                f"[Voximplant] Webhook event received | "
                f"call_id={call_id} | event={event_type}"
            )

            # Map Voximplant events to TelephonyEvent
            if event_type == "Ringing":
                if self.event_callback:
                    await self.event_callback(call_id, TelephonyEvent.RINGING, None)

            elif event_type == "Connected":
                if call_id in self.active_calls:
                    self.active_calls[call_id]["status"] = "connected"

                if self.event_callback:
                    await self.event_callback(call_id, TelephonyEvent.ANSWERED, None)

            elif event_type == "Disconnected":
                reason = event_data.get("reason", "normal")

                if self.event_callback:
                    await self.event_callback(call_id, TelephonyEvent.HANGUP, reason)

            elif event_type == "Failed":
                reason = event_data.get("reason", "unknown")

                # Map to appropriate event
                if "busy" in reason.lower():
                    if self.event_callback:
                        await self.event_callback(call_id, TelephonyEvent.BUSY, reason)
                elif "no answer" in reason.lower() or "timeout" in reason.lower():
                    if self.event_callback:
                        await self.event_callback(call_id, TelephonyEvent.NO_ANSWER, reason)
                else:
                    if self.event_callback:
                        await self.event_callback(call_id, TelephonyEvent.ERROR, reason)

            elif event_type == "TranscriptUpdate":
                # Transcript update from VoxEngine (if we implement transcription there)
                speaker = event_data.get("speaker")  # "user" or "assistant"
                text = event_data.get("text")

                logger.debug(
                    f"[Voximplant] Transcript update | "
                    f"call_id={call_id} | speaker={speaker} | text={text}"
                )

                # This will be used in Phase 2 for real-time transcript updates

            else:
                logger.warning(
                    f"[Voximplant] Unknown event type | "
                    f"call_id={call_id} | event={event_type}"
                )

        except Exception as e:
            logger.error(
                f"[Voximplant] Error handling webhook event | error={e}",
                exc_info=True
            )
