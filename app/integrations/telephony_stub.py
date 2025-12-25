"""
Stub telephony adapter for testing without real telephony provider.
"""
import asyncio
from typing import Optional, Callable

from app.integrations.telephony_base import TelephonyEvent
from app.utils.logging import logger


class StubTelephonyAdapter:
    """Stub implementation of telephony adapter for testing."""

    def __init__(self, event_callback: Optional[Callable] = None):
        """
        Initialize stub adapter.

        Args:
            event_callback: Callback function for telephony events
                           Should accept (call_id: str, event: TelephonyEvent, reason: Optional[str])
        """
        self.event_callback = event_callback
        self.active_calls: dict[str, dict] = {}
        self.audio_queue: dict[str, asyncio.Queue] = {}

        # Pre-generated test responses from "caller"
        self.test_responses = [
            "Да, здравствуйте",
            "Да, интересно. Расскажите подробнее",
            "А сколько это стоит?",
            "Хорошо, спасибо за информацию",
            "До свидания"
        ]
        self.response_index: dict[str, int] = {}

    async def initiate_call(self, call_id: str, phone: str) -> None:
        """
        Simulate initiating an outbound call.

        Args:
            call_id: Unique identifier for the call
            phone: Phone number to call
        """
        logger.info(f"[STUB] Initiating call | call_id={call_id} | phone={phone}")

        # Store call info
        self.active_calls[call_id] = {
            "phone": phone,
            "status": "initiating"
        }
        self.audio_queue[call_id] = asyncio.Queue()
        self.response_index[call_id] = 0

        # Simulate ringing after 2 seconds
        asyncio.create_task(self._simulate_call_flow(call_id))

    async def _simulate_call_flow(self, call_id: str) -> None:
        """
        Simulate the flow of a call: ringing -> answered.

        Args:
            call_id: Call identifier
        """
        # Wait 2 seconds, then send "ringing" event
        await asyncio.sleep(2)

        if call_id in self.active_calls:
            logger.info(f"[STUB] Call ringing | call_id={call_id}")
            if self.event_callback:
                await self.event_callback(call_id, TelephonyEvent.RINGING, None)

        # Wait another 2 seconds, then send "answered" event
        await asyncio.sleep(2)

        if call_id in self.active_calls:
            logger.info(f"[STUB] Call answered | call_id={call_id}")
            self.active_calls[call_id]["status"] = "answered"
            if self.event_callback:
                await self.event_callback(call_id, TelephonyEvent.ANSWERED, None)

    async def send_audio(self, call_id: str, audio_bytes: bytes) -> None:
        """
        Simulate sending audio to caller.

        Args:
            call_id: Call identifier
            audio_bytes: Audio data
        """
        if call_id not in self.active_calls:
            logger.warning(f"[STUB] Attempted to send audio to non-existent call: {call_id}")
            return

        logger.info(f"[STUB] Sending audio | call_id={call_id} | size={len(audio_bytes)} bytes")

        # Simulate audio playback time (assuming ~2-3 seconds)
        await asyncio.sleep(0.5)

    async def receive_audio(self, call_id: str) -> Optional[bytes]:
        """
        Simulate receiving audio from caller.

        For stub implementation, we'll generate synthetic text responses
        and convert them to "audio" (just text that will be processed by STT).

        Args:
            call_id: Call identifier

        Returns:
            Simulated audio bytes (actually text for testing)
        """
        if call_id not in self.active_calls:
            logger.warning(f"[STUB] Attempted to receive audio from non-existent call: {call_id}")
            return None

        if self.active_calls[call_id]["status"] != "answered":
            return None

        # Get next test response
        idx = self.response_index.get(call_id, 0)

        if idx >= len(self.test_responses):
            # No more responses, caller will hang up
            logger.info(f"[STUB] No more test responses, simulating hangup | call_id={call_id}")
            if self.event_callback:
                await self.event_callback(call_id, TelephonyEvent.HANGUP, None)
            return None

        response_text = self.test_responses[idx]
        self.response_index[call_id] = idx + 1

        # For stub, we'll return text as bytes (in real impl, this would be actual audio)
        # The STT will need to handle this (or we mock STT in stub mode)
        logger.info(f"[STUB] Simulating caller speech | call_id={call_id} | text=\"{response_text}\"")

        # Simulate time to speak
        await asyncio.sleep(1)

        # Return text as bytes (stub mode)
        return response_text.encode('utf-8')

    async def hangup(self, call_id: str) -> None:
        """
        Simulate hanging up the call.

        Args:
            call_id: Call identifier
        """
        if call_id not in self.active_calls:
            logger.warning(f"[STUB] Attempted to hangup non-existent call: {call_id}")
            return

        logger.info(f"[STUB] Hanging up call | call_id={call_id}")

        # Clean up
        del self.active_calls[call_id]
        if call_id in self.audio_queue:
            del self.audio_queue[call_id]
        if call_id in self.response_index:
            del self.response_index[call_id]

        # Send hangup event
        if self.event_callback:
            await self.event_callback(call_id, TelephonyEvent.HANGUP, None)
