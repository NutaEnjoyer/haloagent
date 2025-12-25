"""
Voximplant webhook API routes.
Receives events from Voximplant VoxEngine scenarios.
"""
from fastapi import APIRouter, Request, HTTPException
from typing import Dict, List

from app.utils.logging import logger

router = APIRouter(prefix="/voximplant", tags=["voximplant"])

# Store conversation history per call_id
# Format: {call_id: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
conversation_history: Dict[str, List[dict]] = {}

# Store session data (greeting, prompt) per call_id
# Format: {call_id: {"greeting": "...", "prompt": "...", "demo_session_id": "..."}}
session_data_store: Dict[str, dict] = {}


@router.api_route("/events", methods=["GET", "POST"])
async def voximplant_events(request: Request):
    """
    Receive events from Voximplant VoxEngine scenario.

    Expected events:
    - Ringing: Call is ringing
    - Connected: Call was answered
    - Disconnected: Call ended normally
    - Failed: Call failed (busy, no answer, error)
    - TranscriptUpdate: Real-time transcript update (Phase 2)

    Example payload:
    {
        "event": "Connected",
        "call_id": "uuid",
        "timestamp": 1234567890,
        "reason": "optional reason for Failed events"
    }

    Returns:
        Status response
    """
    try:
        # Parse incoming event
        if request.method == "POST":
            data = await request.json()
        else:
            # For GET requests, parse query parameters
            params = dict(request.query_params)
            logger.info(f"[Voximplant Webhook] Received GET request | params={params}")

            # Convert to expected format
            data = {
                "event": params.get("event", "unknown"),
                "call_id": params.get("call_id", "unknown"),
                "timestamp": params.get("ts", "unknown")
            }

        event_type = data.get("event")
        call_id = data.get("call_id")

        if not event_type:
            logger.warning(
                f"[Voximplant Webhook] Invalid event: missing event | data={data}"
            )
            raise HTTPException(status_code=400, detail="Missing event")

        # Allow test events without call_id
        if not call_id or call_id == "unknown":
            logger.info(f"[Voximplant Webhook] Test event received | event={event_type}")
            return {"status": "ok", "event": event_type, "message": "test event accepted"}

        logger.info(
            f"[Voximplant Webhook] Received event | "
            f"call_id={call_id} | event={event_type}"
        )

        # Update demo session status if this is a demo call
        if event_type == "CallDisconnected":
            from app.api.routes_demo import demo_sessions, DemoSessionStatus

            # Find demo session using session_data_store
            if call_id in session_data_store:
                demo_session_id = session_data_store[call_id].get('demo_session_id')

                if demo_session_id and demo_session_id in demo_sessions:
                    session = demo_sessions[demo_session_id]

                    # Save conversation history to session_data_store BEFORE deleting
                    if call_id in conversation_history:
                        session_data_store[call_id]['conversation_history'] = conversation_history[call_id].copy()
                        logger.info(
                            f"[Voximplant Webhook] Saved conversation history | "
                            f"messages={len(conversation_history[call_id])}"
                        )

                    logger.info(
                        f"[Voximplant Webhook] Updating demo session status | "
                        f"demo_session_id={demo_session_id} | voximplant_call_id={call_id}"
                    )
                    # Mark call as completed so track_demo_session can continue
                    session.status = DemoSessionStatus.ANALYZING
                else:
                    logger.warning(
                        f"[Voximplant Webhook] Demo session not found | "
                        f"demo_session_id={demo_session_id} | call_id={call_id}"
                    )
            else:
                logger.warning(
                    f"[Voximplant Webhook] No session data for call_id={call_id}"
                )

        # Clean up conversation history when call ends (AFTER saving to session_data_store)
        if event_type == "CallDisconnected" and call_id in conversation_history:
            logger.info(f"[Voximplant Webhook] Cleaning up conversation history for call_id={call_id}")
            del conversation_history[call_id]

        # Get the telephony adapter from main app
        from app.main import get_telephony_adapter

        try:
            adapter = get_telephony_adapter()

            # Forward event to adapter for processing
            await adapter.handle_webhook_event(data)

            return {"status": "ok", "call_id": call_id}

        except RuntimeError as e:
            # Adapter not initialized (app not started yet)
            logger.error(f"[Voximplant Webhook] Adapter not initialized: {e}")
            raise HTTPException(status_code=503, detail="Service not ready")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[Voximplant Webhook] Error processing event | error={e}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.api_route("/process_audio", methods=["GET", "POST"])
async def process_audio(request: Request):
    """
    Process audio from Voximplant VoxEngine.

    Receives audio URL, downloads it, sends to OpenAI Realtime for processing,
    and returns AI response.

    Expected payload (POST JSON or GET query params):
    {
        "call_id": "uuid",
        "audio_url": "https://...",
        "duration": 5.2
    }

    Returns:
        {
            "user_text": "transcribed user speech",
            "ai_text": "AI response text"
        }
    """
    try:
        # Accept both POST JSON and GET query parameters
        if request.method == "POST":
            data = await request.json()
            call_id = data.get("call_id")
            audio_url = data.get("audio_url")
            duration = data.get("duration", 0)
        else:
            # GET - read from query parameters
            params = dict(request.query_params)
            call_id = params.get("call_id")
            audio_url = params.get("audio_url")
            duration = float(params.get("duration", 0))

        if not call_id or not audio_url:
            logger.warning(f"[Voximplant Audio] Missing call_id or audio_url")
            raise HTTPException(status_code=400, detail="Missing call_id or audio_url")

        logger.info(
            f"[Voximplant Audio] Processing audio | "
            f"call_id={call_id} | url={audio_url} | duration={duration}s"
        )

        # Get OpenAI client
        from app.main import get_openai_client

        try:
            openai_client = get_openai_client()

            # Download audio from Voximplant
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(audio_url) as resp:
                    if resp.status != 200:
                        raise HTTPException(status_code=500, detail=f"Failed to download audio: {resp.status}")

                    audio_bytes = await resp.read()
                    logger.info(f"[Voximplant Audio] Downloaded {len(audio_bytes)} bytes")

            # Transcribe audio using OpenAI Whisper
            user_text = await openai_client.transcribe_audio(audio_bytes)
            logger.info(f"[Voximplant Audio] User said: {user_text}")

            # Get AI response using GPT
            ai_text = await openai_client.get_ai_response(
                user_text,
                context="Вы - вежливый голосовой ассистент компании HALO."
            )
            logger.info(f"[Voximplant Audio] AI response: {ai_text}")

            return {
                "user_text": user_text,
                "ai_text": ai_text
            }

        except RuntimeError as e:
            logger.error(f"[Voximplant Audio] Client not initialized: {e}")
            raise HTTPException(status_code=503, detail="Service not ready")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[Voximplant Audio] Error processing audio | error={e}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.api_route("/get_greeting", methods=["GET", "POST"])
async def get_greeting(request: Request):
    """
    Get custom greeting for a call.

    Voximplant scenario calls this BEFORE speaking the greeting
    to get the custom greeting message.

    Expected payload (POST JSON or GET query params):
    {
        "call_id": "uuid" (optional - will find latest session if not mapped)
    }

    Returns:
        {
            "greeting": "custom greeting text",
            "prompt": "custom prompt text"
        }
    """
    try:
        # Accept both POST JSON and GET query parameters
        if request.method == "POST":
            data = await request.json()
            call_id = data.get("call_id")
        else:
            # GET - read from query parameters
            params = dict(request.query_params)
            call_id = params.get("call_id")

        logger.info(f"[Voximplant Get Greeting] Request | call_id={call_id}")

        session_data = None

        # First try to find by exact call_id match
        if call_id and call_id in session_data_store:
            session_data = session_data_store[call_id]
            logger.info(f"[Voximplant Get Greeting] Found session data by call_id")
        else:
            # Try to find the most recent demo session
            from app.api.routes_demo import demo_sessions, DemoSessionStatus
            for session_id, session in sorted(demo_sessions.items(), key=lambda x: x[1].created_at, reverse=True):
                if session.status in [DemoSessionStatus.INITIATED, DemoSessionStatus.CALL_IN_PROGRESS]:
                    # Use this session's data
                    session_data = {
                        'greeting': session.greeting,
                        'prompt': session.prompt,
                        'demo_session_id': session_id
                    }
                    # Store the mapping for future requests if we have call_id
                    if call_id:
                        session_data_store[call_id] = session_data
                        logger.info(f"[Voximplant Get Greeting] Linked call_id={call_id} to session={session_id}")
                    break

        if session_data:
            logger.info(
                f"[Voximplant Get Greeting] Returning custom data | "
                f"greeting={session_data['greeting'][:50]}..."
            )
            return {
                "greeting": session_data['greeting'],
                "prompt": session_data['prompt']
            }
        else:
            # Return defaults if no session found
            logger.warning(f"[Voximplant Get Greeting] No session found, returning defaults")
            return {
                "greeting": "Здравствуйте! Я голосовой ассистент HALO. Чем могу помочь?",
                "prompt": ""
            }

    except Exception as e:
        logger.error(
            f"[Voximplant Get Greeting] Error | error={e}",
            exc_info=True
        )
        # Return defaults on error
        return {
            "greeting": "Здравствуйте! Я голосовой ассистент HALO. Чем могу помочь?",
            "prompt": ""
        }


@router.api_route("/save_ai_message", methods=["GET", "POST"])
async def save_ai_message(request: Request):
    """
    Save AI message to conversation history.

    Used to save the initial greeting or any AI message to the conversation history
    without waiting for user response.

    Expected payload (POST JSON or GET query params):
    {
        "call_id": "uuid",
        "ai_text": "AI message to save"
    }

    Returns:
        Status
    """
    try:
        # Accept both POST JSON and GET query parameters
        if request.method == "POST":
            data = await request.json()
            call_id = data.get("call_id")
            ai_text = data.get("ai_text")
        else:
            # GET - read from query parameters
            params = dict(request.query_params)
            call_id = params.get("call_id")
            ai_text = params.get("ai_text")

        if not call_id or not ai_text:
            logger.warning(f"[Voximplant Save AI] Missing call_id or ai_text")
            raise HTTPException(status_code=400, detail="Missing call_id or ai_text")

        # Check if we have stored session data for this call (or find the latest session)
        session_data = None

        # First try to find by exact call_id match
        if call_id in session_data_store:
            session_data = session_data_store[call_id]
            logger.info(f"[Voximplant Save AI] Found session data by call_id")
        else:
            # Try to find the most recent demo session
            from app.api.routes_demo import demo_sessions, DemoSessionStatus
            for session_id, session in sorted(demo_sessions.items(), key=lambda x: x[1].created_at, reverse=True):
                if session.status in [DemoSessionStatus.INITIATED, DemoSessionStatus.CALL_IN_PROGRESS]:
                    # Use this session's data
                    session_data = {
                        'greeting': session.greeting,
                        'prompt': session.prompt,
                        'demo_session_id': session_id
                    }
                    # Store the mapping for future requests
                    session_data_store[call_id] = session_data
                    logger.info(f"[Voximplant Save AI] Linked call_id={call_id} to session={session_id}")
                    break

        # Override ai_text with custom greeting if this is the first message
        if session_data and call_id not in conversation_history:
            ai_text = session_data['greeting']
            logger.info(f"[Voximplant Save AI] Using custom greeting: {ai_text}")

        logger.info(
            f"[Voximplant Save AI] Saving message | "
            f"call_id={call_id} | ai_text={ai_text}"
        )

        # Initialize conversation history for this call if needed
        if call_id not in conversation_history:
            conversation_history[call_id] = []
            logger.info(f"[Voximplant Save AI] Starting new conversation for call_id={call_id}")

        # Add assistant message to history
        conversation_history[call_id].append({
            "role": "assistant",
            "content": ai_text
        })

        logger.info(
            f"[Voximplant Save AI] Message saved | "
            f"history_length={len(conversation_history[call_id])}"
        )

        return {"status": "ok", "call_id": call_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[Voximplant Save AI] Error saving message | error={e}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.api_route("/process_text", methods=["GET", "POST"])
async def process_text(request: Request):
    """
    Process text from Voximplant ASR (Automatic Speech Recognition).

    Receives already-transcribed text from ASR, sends to OpenAI GPT for response.
    This is more efficient than process_audio since ASR already did transcription.

    Expected payload (POST JSON or GET query params):
    {
        "call_id": "uuid",
        "user_text": "what the user said"
    }

    Returns:
        {
            "user_text": "what the user said",
            "ai_text": "AI response text"
        }
    """
    import time
    start_time = time.time()

    try:
        # Accept both POST JSON and GET query parameters
        parse_start = time.time()
        if request.method == "POST":
            data = await request.json()
            call_id = data.get("call_id")
            user_text = data.get("user_text")
            custom_prompt = data.get("prompt")  # Optional custom prompt
        else:
            # GET - read from query parameters
            params = dict(request.query_params)
            call_id = params.get("call_id")
            user_text = params.get("user_text")
            custom_prompt = params.get("prompt")  # Optional custom prompt

        parse_time = (time.time() - parse_start) * 1000
        logger.info(f"[LATENCY] Parse request: {parse_time:.2f}ms")

        if not call_id or not user_text:
            logger.warning(f"[Voximplant Text] Missing call_id or user_text")
            raise HTTPException(status_code=400, detail="Missing call_id or user_text")

        # Check if we have stored session data for this call
        if not custom_prompt and call_id in session_data_store:
            custom_prompt = session_data_store[call_id].get('prompt')
            logger.info(f"[Voximplant Text] Using prompt from session data")

        logger.info(
            f"[Voximplant Text] Processing text | "
            f"call_id={call_id} | user_text={user_text}"
        )

        # Get OpenAI client
        from app.main import get_openai_client

        try:
            client_start = time.time()
            openai_client = get_openai_client()
            client_time = (time.time() - client_start) * 1000
            logger.info(f"[LATENCY] Get OpenAI client: {client_time:.2f}ms")

            # Initialize conversation history for this call if needed
            history_start = time.time()
            if call_id not in conversation_history:
                conversation_history[call_id] = []
                logger.info(f"[Voximplant Text] Starting new conversation for call_id={call_id}")

            # Add user message to history
            conversation_history[call_id].append({
                "role": "user",
                "content": user_text
            })

            # Build messages with system context and full history
            # Use custom prompt if provided, otherwise use default
            default_system_prompt = """РОЛЬ ГОЛОСОВОГО АССИСТЕНТА HALO

1. Кто ты в этом разговоре
Ты — живой человек, который позвонил по делу.
Не оператор колл-центра.
Не автоответчик.
Не «ассистент системы».
Ты ведёшь себя так, как ведёт себя:
нормальный консультант,
или менеджер,
или специалист,
который умеет говорить по телефону и чувствует собеседника.
Твоя цель — нормальный разговор, а не отработка сценария.

2. Как ты себя ощущаешь в разговоре (очень важно)
Ты:
не спешишь,
не боишься пауз,
не стараешься «захватить инициативу» любой ценой,
не читаешь заученный текст.
Ты реагируешь, а не декламируешь.
Если человек говорит просто — ты отвечаешь просто.
Если человек напряжён — ты снижаешь давление.
Если человек уверен — ты не сюсюкаешь.

3. Базовая психологическая модель поведения
Используй модель «равный собеседник», а не «продавец ↔ клиент».
Это означает:
ты не выше и не ниже собеседника,
ты не оправдываешься,
ты не давишь,
ты не «выпрашиваешь внимание».
Ты разговариваешь на равных.

4. Как ты строишь ответы
4.1. Фокус на последнюю реплику
Ты всегда отвечаешь на то, что человек сказал последним.
Не возвращайся к старым фразам.
Не продолжай мысль, если разговор уже ушёл в сторону.
Если человек сменил тему — ты принимаешь это как норму.

4.2. Длина ответа
Ты адаптируешь длину ответа:
если человек говорит коротко → ты тоже коротко;
если человек рассуждает → можно объяснять чуть подробнее;
если человек перебивает или торопится → отвечай максимально сжато.

5. Речь и формулировки
Ты используешь живую разговорную речь, как по телефону.
Запрещённые паттерны (строго):
канцелярит,
«официальные» обороты,
шаблоны колл-центров,
избыточная вежливость.
не верно:
«Благодарю вас за уделённое время»
«В соответствии с вашим запросом»
«Данный функционал позволяет»
верно:
«Понял»
«Да, конечно»
«Смотрите, тут так…»

6. Язык общения
Ты всегда говоришь на языке собеседника.
Если собеседник меняет язык — ты полностью переключаешься.
Не смешивай языки.
Не комментируй факт смены языка.
Ты ведёшь себя так, будто изначально владеешь этим языком.

7. Отношение к отказу
Если человек говорит, что ему:
неинтересно,
неудобно,
он не хочет продолжать,
Ты:
не споришь,
не убеждаешь,
не задаёшь лишних вопросов,
не «дожимаешь».

Используй естественную речь обычного живого телефонного разговора.
Избегай конструкций, которые звучат формально, книжно или как заученный скрипт."""

            # Use custom prompt if provided, otherwise use default
            system_prompt = custom_prompt if custom_prompt else default_system_prompt

            logger.info(
                f"[Voximplant Text] Using {'custom' if custom_prompt else 'default'} system prompt | "
                f"length={len(system_prompt)}"
            )

            messages = [
                {"role": "system", "content": system_prompt}
            ] + conversation_history[call_id]

            history_time = (time.time() - history_start) * 1000
            logger.info(
                f"[LATENCY] History processing: {history_time:.2f}ms | "
                f"messages_count={len(conversation_history[call_id])}"
            )

            # Get AI response with full conversation context
            logger.info(f"[LATENCY] Sending request to OpenAI...")
            openai_start = time.time()

            ai_text = await openai_client.generate_response(
                messages=messages,
                temperature=0.7,
                max_tokens=150
            )

            openai_time = (time.time() - openai_start) * 1000
            logger.info(f"[LATENCY] ⚠️ OpenAI API call: {openai_time:.2f}ms")
            logger.info(f"[Voximplant Text] AI response: {ai_text}")

            # Add assistant response to history
            conversation_history[call_id].append({
                "role": "assistant",
                "content": ai_text
            })

            total_time = (time.time() - start_time) * 1000
            logger.info(
                f"[LATENCY] ✅ TOTAL request time: {total_time:.2f}ms | "
                f"breakdown: parse={parse_time:.0f}ms + client={client_time:.0f}ms + "
                f"history={history_time:.0f}ms + openai={openai_time:.0f}ms"
            )

            return {
                "user_text": user_text,
                "ai_text": ai_text
            }

        except RuntimeError as e:
            logger.error(f"[Voximplant Text] Client not initialized: {e}")
            raise HTTPException(status_code=503, detail="Service not ready")

    except HTTPException:
        raise
    except Exception as e:
        total_time = (time.time() - start_time) * 1000
        logger.error(
            f"[Voximplant Text] Error processing text after {total_time:.2f}ms | error={e}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def voximplant_health():
    """
    Health check for Voximplant webhook endpoint.

    Returns:
        Status
    """
    return {"status": "ok", "service": "voximplant_webhook"}
