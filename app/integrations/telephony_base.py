"""
Base interface for telephony providers.
"""
from enum import Enum
from typing import Protocol, Optional


class TelephonyEvent(str, Enum):
    """Events from telephony provider."""
    RINGING = "ringing"
    ANSWERED = "answered"
    HANGUP = "hangup"
    BUSY = "busy"
    NO_ANSWER = "no_answer"
    ERROR = "error"


class TelephonyAdapter(Protocol):
    """Protocol defining the interface for telephony providers."""

    async def initiate_call(self, call_id: str, phone: str) -> None:
        """
        Initiate an outbound call.

        Args:
            call_id: Unique identifier for the call
            phone: Phone number to call (E.164 format)
        """
        ...

    async def send_audio(self, call_id: str, audio_bytes: bytes) -> None:
        """
        Send audio to the caller.

        Args:
            call_id: Call identifier
            audio_bytes: Audio data to send
        """
        ...

    async def receive_audio(self, call_id: str) -> Optional[bytes]:
        """
        Receive audio from the caller.

        Args:
            call_id: Call identifier

        Returns:
            Audio data bytes, or None if no audio available
        """
        ...

    async def hangup(self, call_id: str) -> None:
        """
        Terminate the call.

        Args:
            call_id: Call identifier
        """
        ...
