"""
OpenAI Realtime API client for streaming audio conversations.

Provides WebSocket-based real-time communication with OpenAI for:
- Streaming Speech-to-Text (Whisper)
- Streaming GPT responses
- Streaming Text-to-Speech

Documentation: https://platform.openai.com/docs/guides/realtime
"""
import asyncio
import base64
import json
from typing import AsyncGenerator, Optional, Callable
from enum import Enum

import websockets
from websockets.client import WebSocketClientProtocol

from app.utils.logging import logger


class RealtimeEventType(str, Enum):
    """OpenAI Realtime API event types."""
    # Session events
    SESSION_CREATED = "session.created"
    SESSION_UPDATED = "session.updated"

    # Input audio events
    INPUT_AUDIO_BUFFER_APPEND = "input_audio_buffer.append"
    INPUT_AUDIO_BUFFER_COMMIT = "input_audio_buffer.commit"
    INPUT_AUDIO_BUFFER_CLEAR = "input_audio_buffer.clear"

    # Conversation events
    CONVERSATION_ITEM_CREATED = "conversation.item.created"
    CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_COMPLETED = "conversation.item.input_audio_transcription.completed"

    # Response events
    RESPONSE_CREATED = "response.created"
    RESPONSE_DONE = "response.done"
    RESPONSE_AUDIO_DELTA = "response.audio.delta"
    RESPONSE_AUDIO_DONE = "response.audio.done"
    RESPONSE_AUDIO_TRANSCRIPT_DELTA = "response.audio_transcript.delta"
    RESPONSE_AUDIO_TRANSCRIPT_DONE = "response.audio_transcript.done"
    RESPONSE_TEXT_DELTA = "response.text.delta"
    RESPONSE_TEXT_DONE = "response.text.done"

    # Error events
    ERROR = "error"


class VoiceType(str, Enum):
    """Available TTS voices."""
    ALLOY = "alloy"
    ECHO = "echo"
    FABLE = "fable"
    ONYX = "onyx"
    NOVA = "nova"
    SHIMMER = "shimmer"


class OpenAIRealtimeClient:
    """
    Client for OpenAI Realtime API.

    Manages WebSocket connection and provides methods for streaming audio.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-realtime-preview-2024-12-17"
    ):
        """
        Initialize Realtime API client.

        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4o-realtime-preview)
        """
        self.api_key = api_key
        self.model = model
        self.ws_url = f"wss://api.openai.com/v1/realtime?model={model}"

        self.ws: Optional[WebSocketClientProtocol] = None
        self.connected = False

        # Event handlers
        self.on_audio_delta: Optional[Callable[[bytes], None]] = None
        self.on_transcript_delta: Optional[Callable[[str, str], None]] = None
        self.on_error: Optional[Callable[[dict], None]] = None

    async def connect(
        self,
        voice: str = "alloy",
        instructions: str = "",
        temperature: float = 0.8,
        input_audio_format: str = "pcm16",
        output_audio_format: str = "pcm16"
    ) -> None:
        """
        Connect to OpenAI Realtime API and configure session.

        Args:
            voice: TTS voice to use
            instructions: System instructions for the assistant
            temperature: Response randomness (0.0-1.0)
            input_audio_format: Input audio format (pcm16 or g711_ulaw)
            output_audio_format: Output audio format (pcm16 or g711_ulaw)
        """
        try:
            logger.info(f"[OpenAI Realtime] Connecting to {self.ws_url}")

            # Connect to WebSocket with API key in header
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "OpenAI-Beta": "realtime=v1"
            }

            self.ws = await websockets.connect(
                self.ws_url,
                extra_headers=headers,
                ping_interval=20,
                ping_timeout=10
            )

            self.connected = True
            logger.info("[OpenAI Realtime] Connected successfully")

            # Configure session
            await self._configure_session(
                voice=voice,
                instructions=instructions,
                temperature=temperature,
                input_audio_format=input_audio_format,
                output_audio_format=output_audio_format
            )

        except Exception as e:
            logger.error(f"[OpenAI Realtime] Connection error: {e}", exc_info=True)
            self.connected = False
            raise

    async def _configure_session(
        self,
        voice: str,
        instructions: str,
        temperature: float,
        input_audio_format: str,
        output_audio_format: str
    ) -> None:
        """Configure the session with desired settings."""
        config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": instructions or "You are a helpful assistant.",
                "voice": voice,
                "input_audio_format": input_audio_format,
                "output_audio_format": output_audio_format,
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",  # Voice Activity Detection on server
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500
                },
                "temperature": temperature
            }
        }

        await self._send_event(config)
        logger.info(f"[OpenAI Realtime] Session configured | voice={voice} | instructions={instructions[:50]}...")

    async def _send_event(self, event: dict) -> None:
        """Send an event to the API."""
        if not self.ws:
            raise RuntimeError("WebSocket not connected")

        await self.ws.send(json.dumps(event))

    async def send_audio_chunk(self, audio_bytes: bytes) -> None:
        """
        Send audio chunk to OpenAI for processing.

        Args:
            audio_bytes: Raw audio bytes (PCM16 or G.711)
        """
        if not self.connected:
            logger.warning("[OpenAI Realtime] Cannot send audio - not connected")
            return

        # Base64 encode audio
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

        event = {
            "type": "input_audio_buffer.append",
            "audio": audio_b64
        }

        await self._send_event(event)

    async def commit_audio_buffer(self) -> None:
        """Commit the audio buffer to trigger processing."""
        event = {
            "type": "input_audio_buffer.commit"
        }

        await self._send_event(event)

    async def receive_events(self) -> AsyncGenerator[tuple[str, any], None]:
        """
        Receive events from OpenAI Realtime API.

        Yields:
            Tuple of (event_type, event_data)
        """
        if not self.ws:
            raise RuntimeError("WebSocket not connected")

        try:
            async for message in self.ws:
                try:
                    event = json.loads(message)
                    event_type = event.get("type")

                    # Handle different event types
                    if event_type == RealtimeEventType.RESPONSE_AUDIO_DELTA:
                        # TTS audio chunk from assistant
                        audio_b64 = event.get("delta", "")
                        if audio_b64:
                            audio_bytes = base64.b64decode(audio_b64)

                            # Call handler if set
                            if self.on_audio_delta:
                                self.on_audio_delta(audio_bytes)

                            yield ("audio_delta", audio_bytes)

                    elif event_type == RealtimeEventType.RESPONSE_AUDIO_TRANSCRIPT_DELTA:
                        # Assistant speaking (transcript)
                        text = event.get("delta", "")
                        if text and self.on_transcript_delta:
                            self.on_transcript_delta("assistant", text)

                        yield ("assistant_transcript_delta", text)

                    elif event_type == RealtimeEventType.CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_COMPLETED:
                        # User spoke (STT result)
                        transcript = event.get("transcript", "")
                        if transcript and self.on_transcript_delta:
                            self.on_transcript_delta("user", transcript)

                        yield ("user_transcript", transcript)

                    elif event_type == RealtimeEventType.RESPONSE_DONE:
                        # Turn complete
                        yield ("turn_complete", event)

                    elif event_type == RealtimeEventType.ERROR:
                        # Error occurred
                        logger.error(f"[OpenAI Realtime] API error: {event}")

                        if self.on_error:
                            self.on_error(event)

                        yield ("error", event)

                    else:
                        # Other events (logging only)
                        logger.debug(f"[OpenAI Realtime] Event: {event_type}")
                        yield (event_type, event)

                except json.JSONDecodeError as e:
                    logger.error(f"[OpenAI Realtime] Invalid JSON: {e}")
                    continue

        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"[OpenAI Realtime] Connection closed: {e}")
            self.connected = False

        except Exception as e:
            logger.error(f"[OpenAI Realtime] Error receiving events: {e}", exc_info=True)
            self.connected = False

    async def disconnect(self) -> None:
        """Disconnect from the API."""
        if self.ws:
            await self.ws.close()
            self.ws = None
            self.connected = False
            logger.info("[OpenAI Realtime] Disconnected")

    def __del__(self):
        """Cleanup on deletion."""
        if self.ws and self.connected:
            asyncio.create_task(self.disconnect())
