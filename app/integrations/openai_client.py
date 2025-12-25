"""
OpenAI API client for STT (Whisper), LLM (GPT), and TTS.
"""
import time
from io import BytesIO
from typing import Optional

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from app.config import settings
from app.core.models import FinalDisposition
from app.utils.logging import logger

# System prompt for the voice assistant
SYSTEM_PROMPT = """Ты - вежливый оператор call-центра. Твоя задача:
1. Представить продукт/услугу клиенту
2. Выяснить, интересно ли это клиенту
3. Ответить на базовые вопросы

Правила поведения:
- Говори короткими фразами (1-2 предложения)
- Будь вежливым и нейтральным
- Не спорь с клиентом
- Не обсуждай посторонние темы
- НЕ упоминай, что ты искусственный интеллект
- Говори естественно, как живой человек

Если клиент заинтересован - предложи дальнейшие действия.
Если не заинтересован - вежливо попрощайся.
Если просит перезвонить позже - уточни время и попрощайся.

Представься и начни разговор."""

# Prompt for call classification
CLASSIFICATION_PROMPT = """Проанализируй следующий диалог между оператором и клиентом.

Определи:
1. Уровень интереса клиента: interested, not_interested, call_later, neutral
2. Краткое резюме разговора (1-2 предложения)

Диалог:
{transcript}

Ответь СТРОГО в формате JSON:
{{
    "disposition": "interested|not_interested|call_later|neutral",
    "summary": "краткое описание результата разговора"
}}"""


class OpenAIClient:
    """Client for OpenAI API interactions."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key. If None, uses settings.OPENAI_API_KEY
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.gpt_model = settings.GPT_MODEL
        self.tts_voice = settings.TTS_VOICE

    async def transcribe_audio(self, audio_bytes: bytes, language: str = "ru") -> str:
        """
        Transcribe audio using Whisper STT.

        Args:
            audio_bytes: Audio data as bytes
            language: Language code (default: "ru")

        Returns:
            Transcribed text

        Raises:
            Exception: If transcription fails
        """
        start_time = time.time()

        try:
            # Create a file-like object from bytes
            audio_file = BytesIO(audio_bytes)
            audio_file.name = "audio.mp3"  # OpenAI requires a filename

            # Call Whisper API
            response = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language
            )

            text = response.text
            duration = time.time() - start_time

            logger.info(f"STT completed in {duration:.3f}s | text_length={len(text)}")
            return text

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"STT failed after {duration:.3f}s | error={str(e)}")
            raise

    async def generate_response(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 200
    ) -> str:
        """
        Generate response using GPT.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response

        Returns:
            Generated response text

        Raises:
            Exception: If generation fails
        """
        start_time = time.time()

        # Calculate input size
        total_chars = sum(len(msg.get("content", "")) for msg in messages)

        logger.info(
            f"[LATENCY-OpenAI] Starting GPT request | "
            f"model={self.gpt_model} | messages_count={len(messages)} | "
            f"total_chars={total_chars} | temp={temperature} | max_tokens={max_tokens}"
        )

        try:
            api_start = time.time()

            response: ChatCompletion = await self.client.chat.completions.create(
                model=self.gpt_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            api_duration_ms = (time.time() - api_start) * 1000

            assistant_message = response.choices[0].message.content
            total_duration_ms = (time.time() - start_time) * 1000

            # Detailed token usage
            usage = response.usage
            logger.info(
                f"[LATENCY-OpenAI] ⚠️ GPT API completed in {api_duration_ms:.0f}ms "
                f"(total: {total_duration_ms:.0f}ms) | "
                f"tokens: prompt={usage.prompt_tokens} + "
                f"completion={usage.completion_tokens} = "
                f"total={usage.total_tokens} | "
                f"response_chars={len(assistant_message)}"
            )

            return assistant_message

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"[LATENCY-OpenAI] ❌ GPT failed after {duration_ms:.0f}ms | error={str(e)}"
            )
            raise

    async def text_to_speech(self, text: str, voice: Optional[str] = None) -> bytes:
        """
        Convert text to speech using TTS.

        Args:
            text: Text to convert
            voice: Voice name (default: from settings)

        Returns:
            Audio data as bytes

        Raises:
            Exception: If TTS fails
        """
        start_time = time.time()
        voice = voice or self.tts_voice

        try:
            response = await self.client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text
            )

            # Get audio bytes from response
            audio_bytes = response.content

            duration = time.time() - start_time

            logger.info(
                f"TTS completed in {duration:.3f}s | "
                f"text_length={len(text)} | "
                f"audio_size={len(audio_bytes)} bytes"
            )

            return audio_bytes

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"TTS failed after {duration:.3f}s | error={str(e)}")
            raise

    async def get_ai_response(
        self,
        user_text: str,
        context: str = "",
        temperature: float = 0.8,
        max_tokens: int = 150
    ) -> str:
        """
        Get AI response to user's speech.

        Args:
            user_text: What the user said
            context: System context/instructions
            temperature: Randomness (0.0-2.0)
            max_tokens: Max response length

        Returns:
            AI response text

        Raises:
            Exception: If request fails
        """
        start_time = time.time()

        try:
            messages = [
                {"role": "system", "content": context or SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ]

            response_text = await self.generate_response(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            duration = time.time() - start_time
            logger.info(
                f"AI response generated in {duration:.3f}s | "
                f"input_length={len(user_text)} | "
                f"output_length={len(response_text)}"
            )

            return response_text

        except Exception as e:
            logger.error(f"Failed to get AI response: {e}")
            raise

    async def classify_call(self, transcript_text: str) -> tuple[FinalDisposition, str]:
        """
        Classify call result based on transcript.

        Args:
            transcript_text: Full transcript of the conversation

        Returns:
            Tuple of (final_disposition, short_summary)

        Raises:
            Exception: If classification fails
        """
        start_time = time.time()

        try:
            prompt = CLASSIFICATION_PROMPT.format(transcript=transcript_text)

            response: ChatCompletion = await self.client.chat.completions.create(
                model=self.gpt_model,
                messages=[
                    {"role": "system", "content": "Ты - аналитик разговоров."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )

            result_text = response.choices[0].message.content
            duration = time.time() - start_time

            # Parse JSON response
            import json
            import re
            try:
                # Remove markdown code blocks if present
                cleaned_text = re.sub(r'```json\s*|\s*```', '', result_text).strip()
                result = json.loads(cleaned_text)
                disposition_str = result.get("disposition", "neutral")
                summary = result.get("summary", "Разговор завершен")

                # Map to enum
                disposition_map = {
                    "interested": FinalDisposition.INTERESTED,
                    "not_interested": FinalDisposition.NOT_INTERESTED,
                    "call_later": FinalDisposition.CALL_LATER,
                    "neutral": FinalDisposition.NEUTRAL
                }
                disposition = disposition_map.get(disposition_str, FinalDisposition.NEUTRAL)

                logger.info(
                    f"Classification completed in {duration:.3f}s | "
                    f"disposition={disposition.value} | "
                    f"summary_length={len(summary)}"
                )

                return disposition, summary

            except json.JSONDecodeError:
                logger.warning(f"Failed to parse classification JSON: {result_text}")
                return FinalDisposition.NEUTRAL, "Не удалось определить результат"

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Classification failed after {duration:.3f}s | error={str(e)}")
            raise
