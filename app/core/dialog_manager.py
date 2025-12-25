"""
Dialog Manager - handles the conversation flow between caller and assistant.
"""
import time
from datetime import datetime
from typing import Optional

from app.config import settings
from app.core.models import CallSession, Speaker
from app.integrations.openai_client import OpenAIClient, SYSTEM_PROMPT
from app.integrations.telephony_base import TelephonyAdapter
from app.utils.logging import logger
from app.utils.time import utcnow


class DialogManager:
    """Manages the dialog flow for a call."""

    # Keywords that indicate the assistant wants to end the call
    GOODBYE_KEYWORDS = [
        "до свидания",
        "всего доброго",
        "всего хорошего",
        "прощайте",
        "до встречи"
    ]

    def __init__(
        self,
        openai_client: OpenAIClient,
        telephony_adapter: TelephonyAdapter,
        max_duration_sec: Optional[int] = None,
        max_turns: Optional[int] = None
    ):
        """
        Initialize Dialog Manager.

        Args:
            openai_client: OpenAI client for STT/GPT/TTS
            telephony_adapter: Telephony adapter for audio I/O
            max_duration_sec: Maximum call duration in seconds
            max_turns: Maximum number of dialog turns
        """
        self.openai_client = openai_client
        self.telephony_adapter = telephony_adapter
        self.max_duration_sec = max_duration_sec or settings.MAX_CALL_DURATION_SEC
        self.max_turns = max_turns or settings.MAX_DIALOG_TURNS

    async def run_dialog(self, call_id: str, call_session: CallSession) -> None:
        """
        Run the dialog loop for a call.

        Args:
            call_id: Call identifier
            call_session: Call session object to update with transcript
        """
        logger.info(f"Starting dialog | call_id={call_id}")

        # Initialize conversation history for GPT
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

        dialog_start_time = time.time()
        turn_count = 0

        try:
            # First, send initial greeting from assistant
            await self._send_initial_greeting(call_id, call_session, messages)
            turn_count += 1

            # Main dialog loop
            while True:
                # Check exit conditions
                elapsed_time = time.time() - dialog_start_time

                if elapsed_time >= self.max_duration_sec:
                    logger.info(
                        f"Max duration reached | call_id={call_id} | "
                        f"duration={elapsed_time:.1f}s"
                    )
                    await self._send_goodbye(call_id, call_session, messages, "Время разговора истекло")
                    break

                if turn_count >= self.max_turns:
                    logger.info(
                        f"Max turns reached | call_id={call_id} | turns={turn_count}"
                    )
                    await self._send_goodbye(call_id, call_session, messages, "Достигнут лимит вопросов")
                    break

                # Receive audio from caller
                turn_start = time.time()
                audio_bytes = await self.telephony_adapter.receive_audio(call_id)

                if audio_bytes is None:
                    logger.info(f"No audio received, ending dialog | call_id={call_id}")
                    break

                # STT: Convert audio to text
                try:
                    # For stub mode, audio_bytes might be text already (not real audio)
                    # Check if it looks like text instead of audio
                    try:
                        decoded = audio_bytes.decode('utf-8')
                        # If decodes cleanly and looks like readable text, it's from stub
                        if len(decoded) < 200 and decoded.isprintable():
                            user_text = decoded
                            logger.info(f"[STUB MODE] Using text directly: {user_text}")
                        else:
                            # Looks like binary data, use STT
                            user_text = await self.openai_client.transcribe_audio(audio_bytes)
                    except UnicodeDecodeError:
                        # Binary data, use STT
                        user_text = await self.openai_client.transcribe_audio(audio_bytes)
                except Exception as e:
                    logger.error(f"STT failed | call_id={call_id} | error={e}")
                    # Try to continue with error message
                    user_text = ""

                if not user_text or len(user_text.strip()) == 0:
                    logger.warning(f"Empty transcription, skipping turn | call_id={call_id}")
                    continue

                # Add user message to transcript
                call_session.add_turn(Speaker.USER, user_text)
                messages.append({"role": "user", "content": user_text})

                logger.info(f"User said: \"{user_text}\" | call_id={call_id}")

                # GPT: Generate response
                try:
                    # Limit message history to last 10 messages (5 pairs) to save tokens
                    recent_messages = [messages[0]] + messages[-10:]

                    assistant_text = await self.openai_client.generate_response(recent_messages)
                except Exception as e:
                    logger.error(f"GPT failed | call_id={call_id} | error={e}")
                    assistant_text = "Извините, произошла техническая ошибка. До свидания."

                # Add assistant message to transcript
                call_session.add_turn(Speaker.ASSISTANT, assistant_text)
                messages.append({"role": "assistant", "content": assistant_text})

                logger.info(f"Assistant said: \"{assistant_text}\" | call_id={call_id}")

                # TTS: Convert response to audio
                try:
                    audio_response = await self.openai_client.text_to_speech(assistant_text)
                except Exception as e:
                    logger.error(f"TTS failed | call_id={call_id} | error={e}")
                    # Can't recover from TTS failure, end call
                    break

                # Send audio to caller
                await self.telephony_adapter.send_audio(call_id, audio_response)

                # Log turn timing
                turn_duration = time.time() - turn_start
                logger.info(f"Dialog turn completed | call_id={call_id} | duration={turn_duration:.3f}s")

                # Check if assistant wants to end conversation
                if self._should_end_conversation(assistant_text):
                    logger.info(f"Assistant indicated end of conversation | call_id={call_id}")
                    break

                turn_count += 1

        except Exception as e:
            logger.error(f"Dialog loop error | call_id={call_id} | error={e}", exc_info=True)

        finally:
            total_duration = time.time() - dialog_start_time
            logger.info(
                f"Dialog ended | call_id={call_id} | "
                f"turns={turn_count} | "
                f"duration={total_duration:.1f}s"
            )

    async def _send_initial_greeting(
        self,
        call_id: str,
        call_session: CallSession,
        messages: list[dict]
    ) -> None:
        """
        Send initial greeting from assistant.

        Args:
            call_id: Call identifier
            call_session: Call session
            messages: Message history
        """
        try:
            # Generate initial greeting
            greeting = await self.openai_client.generate_response(messages)

            # Add to transcript
            call_session.add_turn(Speaker.ASSISTANT, greeting)
            messages.append({"role": "assistant", "content": greeting})

            logger.info(f"Initial greeting: \"{greeting}\" | call_id={call_id}")

            # Convert to speech and send
            audio = await self.openai_client.text_to_speech(greeting)
            await self.telephony_adapter.send_audio(call_id, audio)

        except Exception as e:
            logger.error(f"Failed to send initial greeting | call_id={call_id} | error={e}")

    async def _send_goodbye(
        self,
        call_id: str,
        call_session: CallSession,
        messages: list[dict],
        reason: str
    ) -> None:
        """
        Send goodbye message and end call.

        Args:
            call_id: Call identifier
            call_session: Call session
            messages: Message history
            reason: Reason for ending call
        """
        try:
            # Generate goodbye message
            goodbye_prompt = f"Клиент: {reason}. Вежливо попрощайся с клиентом (1 фраза)."
            messages.append({"role": "user", "content": goodbye_prompt})

            goodbye = await self.openai_client.generate_response(messages)

            # Add to transcript
            call_session.add_turn(Speaker.ASSISTANT, goodbye)

            logger.info(f"Goodbye message: \"{goodbye}\" | call_id={call_id}")

            # Convert to speech and send
            audio = await self.openai_client.text_to_speech(goodbye)
            await self.telephony_adapter.send_audio(call_id, audio)

        except Exception as e:
            logger.error(f"Failed to send goodbye | call_id={call_id} | error={e}")

    def _should_end_conversation(self, text: str) -> bool:
        """
        Check if the text indicates the conversation should end.

        Args:
            text: Text to check

        Returns:
            True if conversation should end
        """
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.GOODBYE_KEYWORDS)
