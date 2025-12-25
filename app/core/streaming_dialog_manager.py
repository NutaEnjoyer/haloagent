"""
Streaming Dialog Manager for real-time audio conversations.

Manages bidirectional streaming between:
- Voximplant (user audio in, assistant audio out)
- OpenAI Realtime API (STT + GPT + TTS)
"""
import asyncio
from typing import Optional

from app.core.models import CallSession, Speaker
from app.integrations.openai_realtime import OpenAIRealtimeClient
from app.integrations.telephony_voximplant import VoximplantTelephonyAdapter
from app.utils.logging import logger

# Import WebSocket helpers
from app.api import routes_websocket


class StreamingDialogManager:
    """
    Manages real-time dialog flow using OpenAI Realtime API.

    Flow:
    1. Voximplant audio (user) → OpenAI Realtime (STT + GPT)
    2. OpenAI Realtime (TTS) → Voximplant audio (assistant)
    3. Transcripts saved to CallSession
    """

    def __init__(
        self,
        voximplant_adapter: VoximplantTelephonyAdapter,
        openai_api_key: str
    ):
        """
        Initialize Streaming Dialog Manager.

        Args:
            voximplant_adapter: Voximplant telephony adapter
            openai_api_key: OpenAI API key for Realtime API
        """
        self.voximplant = voximplant_adapter
        self.openai_api_key = openai_api_key

    async def run_streaming_dialog(
        self,
        call_id: str,
        call_session: CallSession,
        voice: str = "alloy",
        language: str = "auto",
        prompt: str = ""
    ) -> None:
        """
        Run streaming dialog between user and AI assistant.

        Args:
            call_id: Call identifier
            call_session: Call session to store transcript
            voice: TTS voice (alloy, echo, fable, onyx, nova, shimmer)
            language: Language code (auto, ru, uz, etc.)
            prompt: Custom instructions for assistant
        """
        try:
            logger.info(
                f"[Streaming Dialog] Starting | call_id={call_id} | "
                f"voice={voice} | language={language}"
            )

            # Create OpenAI Realtime client
            realtime_client = OpenAIRealtimeClient(
                api_key=self.openai_api_key
            )

            # Connect and configure session
            instructions = self._build_instructions(prompt, language)

            await realtime_client.connect(
                voice=voice,
                instructions=instructions,
                temperature=0.8
            )

            logger.info(f"[Streaming Dialog] OpenAI Realtime connected | call_id={call_id}")

            # Register OpenAI client with WebSocket endpoint
            # This allows Voximplant audio to be forwarded to OpenAI
            routes_websocket.register_openai_client(call_id, realtime_client)

            # Set up event handlers for transcripts
            async def on_transcript(speaker: str, text: str):
                """Save transcript to call session."""
                if speaker == "user":
                    call_session.add_turn(Speaker.USER, text)
                    logger.info(f"[Streaming Dialog] User: {text}")
                elif speaker == "assistant":
                    call_session.add_turn(Speaker.ASSISTANT, text)
                    logger.info(f"[Streaming Dialog] Assistant: {text}")

            realtime_client.on_transcript_delta = on_transcript

            # Run streaming loop
            await self._streaming_loop(
                call_id=call_id,
                realtime_client=realtime_client
            )

        except Exception as e:
            logger.error(
                f"[Streaming Dialog] Error | call_id={call_id} | error={e}",
                exc_info=True
            )
            raise

        finally:
            # Cleanup
            routes_websocket.unregister_openai_client(call_id)

            if realtime_client and realtime_client.connected:
                await realtime_client.disconnect()

            logger.info(f"[Streaming Dialog] Ended | call_id={call_id}")

    def _build_instructions(self, custom_prompt: str, language: str) -> str:
        """
        Build system instructions for the assistant.

        Args:
            custom_prompt: Custom prompt from user
            language: Language code

        Returns:
            Complete instructions
        """
        base_instructions = custom_prompt or (
            "Вы - вежливый и профессиональный голосовой ассистент компании HALO. "
            "Ваша задача - представить компанию, узнать интерес клиента и предложить следующие шаги. "
            "Говорите естественно, как живой человек. Будьте краткими и по делу."
        )

        # Add language-specific instructions
        if language != "auto":
            language_map = {
                "ru": "Говорите на русском языке.",
                "uz": "Говорите на узбекском языке.",
                "tj": "Говорите на таджикском языке.",
                "kk": "Говорите на казахском языке.",
                "ky": "Говорите на киргизском языке.",
                "tm": "Говорите на туркменском языке.",
                "az": "Говорите на азербайджанском языке.",
                "fa-af": "Говорите на дари (афганском персидском) языке.",
                "en": "Speak in English.",
                "tr": "Türkçe konuşun."
            }

            language_instruction = language_map.get(language, "")
            if language_instruction:
                base_instructions += f" {language_instruction}"
        else:
            base_instructions += (
                " Автоматически определите язык собеседника и общайтесь на нем."
            )

        return base_instructions

    async def _streaming_loop(
        self,
        call_id: str,
        realtime_client: OpenAIRealtimeClient
    ) -> None:
        """
        Main streaming loop: receive events from OpenAI and forward audio to Voximplant.

        Note: Voximplant → OpenAI audio forwarding is handled by the WebSocket endpoint
        in routes_websocket.py. This loop only handles OpenAI → Voximplant.

        Args:
            call_id: Call identifier
            realtime_client: Connected OpenAI Realtime client
        """
        logger.info(f"[Streaming Dialog] Audio forwarding started | call_id={call_id}")

        try:
            # Process events from OpenAI Realtime API
            async for event_type, data in realtime_client.receive_events():
                if event_type == "audio_delta":
                    # TTS audio chunk from OpenAI → send to Voximplant via WebSocket
                    await routes_websocket.send_audio_to_voximplant(call_id, data)

                elif event_type == "turn_complete":
                    # Assistant finished speaking
                    logger.debug(f"[Streaming Dialog] Turn complete | call_id={call_id}")

                elif event_type == "error":
                    # Error from OpenAI
                    logger.error(
                        f"[Streaming Dialog] OpenAI error | "
                        f"call_id={call_id} | error={data}"
                    )
                    break

        except Exception as e:
            logger.error(
                f"[Streaming Dialog] Error in streaming loop | "
                f"call_id={call_id} | error={e}",
                exc_info=True
            )

        logger.info(f"[Streaming Dialog] Audio forwarding ended | call_id={call_id}")
