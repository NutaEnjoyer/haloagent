"""
Demo cabinet API routes.
Endpoints for HALO demo cabinet functionality.
"""
import asyncio
import hashlib
import random
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.core.models import (
    DemoSession,
    DemoSessionStatus,
    Language,
    Voice,
    Analytics,
    Funnel,
    Interaction,
    InteractionType,
    Channel,
    FinalDisposition,
    ChatMessage,
    CRMRecord,
)
from app.core.demo_data_generator import DEMO_CALLS, DEMO_CHATS
from app.utils.logging import logger

router = APIRouter(prefix="/demo", tags=["demo"])

# In-memory storage for demo sessions
demo_sessions: dict[str, DemoSession] = {}
real_calls: dict[str, Any] = {}  # Will store real call data
real_chats: dict[str, Any] = {}  # Will store real chat data

# Voice mapping: Voice enum -> OpenAI Realtime API voice names
VOICE_MAPPING = {
    Voice.MALE: "alloy",      # Male voice
    Voice.FEMALE: "shimmer",  # Female voice
    Voice.NEUTRAL: "echo"     # Neutral voice
}


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateDemoSessionRequest(BaseModel):
    """Request to create a demo session."""
    phone: str = Field(..., description="Phone number in international format")
    language: Language = Field(default=Language.AUTO, description="Language for assistant")
    voice: Voice = Field(default=Voice.FEMALE, description="Voice type")
    greeting: str = Field(..., description="Initial greeting message")
    prompt: str = Field(..., description="Custom prompt for assistant")


class CreateDemoSessionResponse(BaseModel):
    """Response after creating demo session."""
    demo_session_id: str
    status: str


class DemoSessionStatusResponse(BaseModel):
    """Demo session status response."""
    call_status: str  # "pending", "completed", "failed"
    analysis_status: str  # "pending", "done"
    followup_status: str  # "pending", "done"
    sms_status: str  # "pending", "sent"
    crm_status: str  # "pending", "added"
    chat_ready: bool


class InteractionsResponse(BaseModel):
    """Response with list of interactions."""
    items: list[Interaction]


class CallDetailResponse(BaseModel):
    """Detailed call information."""
    id: str
    type: str = "call"
    is_demo: bool
    phone_masked: str
    created_at: str
    duration_sec: int
    disposition: str
    summary: str
    transcript: list[dict]
    crm_record: dict


class ChatDetailResponse(BaseModel):
    """Detailed chat information."""
    id: str
    type: str = "chat"
    is_demo: bool
    created_at: str
    summary: str
    messages: list[dict]


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/session", response_model=CreateDemoSessionResponse)
async def create_demo_session(
    request: CreateDemoSessionRequest,
    background_tasks: BackgroundTasks
):
    """
    Create a new demo session and initiate call.

    This endpoint:
    1. Creates demo session
    2. Generates call_id_hash for deep-link
    3. Initiates actual call via orchestrator
    4. Starts background task to track demo progress
    5. Returns session ID
    """
    try:
        # Generate call_id_hash from phone (for deep-link)
        call_id_hash = hashlib.sha256(
            f"{request.phone}{random.randint(1000, 9999)}".encode()
        ).hexdigest()[:16]

        # Create demo session
        session = DemoSession(
            phone=request.phone,
            language=request.language,
            voice=request.voice,
            greeting=request.greeting,
            prompt=request.prompt,
            call_id_hash=call_id_hash,
            status=DemoSessionStatus.INITIATED
        )

        # Store session
        demo_sessions[str(session.id)] = session

        logger.info(f"Demo session created: {session.id}, phone: {request.phone}")

        # ✅ INTEGRATE WITH VOXIMPLANT ASR CALL
        import requests
        import os
        import json

        try:
            # Get Voximplant credentials from environment
            VOXIMPLANT_ACCOUNT_ID = os.getenv("VOXIMPLANT_ACCOUNT_ID")
            VOXIMPLANT_API_KEY = os.getenv("VOXIMPLANT_API_KEY")
            VOXIMPLANT_RULE_ID = os.getenv("VOXIMPLANT_RULE_ID")
            BACKEND_URL = os.getenv("BACKEND_URL")

            if not all([VOXIMPLANT_ACCOUNT_ID, VOXIMPLANT_API_KEY, VOXIMPLANT_RULE_ID, BACKEND_URL]):
                raise ValueError("Missing Voximplant configuration in environment")

            # Generate call_id for tracking
            import uuid
            voximplant_call_id = str(uuid.uuid4())
            session.call_id = voximplant_call_id

            # Prepare script custom data (passed to VoxEngine scenario)
            script_custom_data = {
                "call_id": voximplant_call_id,
                "webhook_url": BACKEND_URL,
                "demo_session_id": str(session.id),
                "phone": request.phone,
                "greeting": request.greeting,
                "prompt": request.prompt
            }

            logger.info(
                f"Starting Voximplant ASR call | "
                f"demo_session_id={session.id} | call_id={voximplant_call_id} | "
                f"phone={request.phone} | "
                f"greeting={request.greeting[:50]}... | prompt={request.prompt[:50]}..."
            )
            logger.info(f"script_custom_data: {json.dumps(script_custom_data, ensure_ascii=False)}")

            # Store session data for later retrieval by call_id
            from app.api.routes_voximplant import session_data_store
            session_data_store[voximplant_call_id] = {
                'greeting': request.greeting,
                'prompt': request.prompt,
                'demo_session_id': str(session.id)
            }

            logger.info(f"Stored session data for call_id={voximplant_call_id}")

            # Start call via Voximplant Platform API
            response = requests.post('https://api.voximplant.com/platform_api/StartScenarios', data={
                'account_id': VOXIMPLANT_ACCOUNT_ID,
                'api_key': VOXIMPLANT_API_KEY,
                'rule_id': VOXIMPLANT_RULE_ID,
                'script_custom_data': json.dumps(script_custom_data)
            }, timeout=10)

            result = response.json()

            if "error" in result:
                error_msg = result['error'].get('msg', 'Unknown error')
                logger.error(f"Voximplant API error: {error_msg}")
                raise Exception(f"Voximplant error: {error_msg}")

            media_session_uid = result.get('media_session_uid')
            logger.info(
                f"Voximplant call started successfully | "
                f"call_id={voximplant_call_id} | media_session_uid={media_session_uid}"
            )

        except Exception as e:
            logger.error(f"Failed to initiate Voximplant call for demo session: {e}", exc_info=True)
            session.status = DemoSessionStatus.FAILED
            raise HTTPException(status_code=500, detail=f"Failed to initiate call: {str(e)}")

        # Start background task to track demo session progress
        background_tasks.add_task(track_demo_session, str(session.id))

        return CreateDemoSessionResponse(
            demo_session_id=str(session.id),
            status=session.status
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating demo session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/{session_id}")
async def get_demo_analytics(session_id: str):
    """
    Get detailed analytics and analysis results for a demo session.

    Returns:
    - Transcript
    - Analysis summary
    - Interest level
    - Key points
    - Follow-up message
    """
    try:
        if session_id not in demo_sessions:
            raise HTTPException(status_code=404, detail="Demo session not found")

        session = demo_sessions[session_id]

        return {
            "session_id": str(session.id),
            "phone": session.phone,
            "status": session.status,
            "transcript": session.transcript or [],
            "analysis": {
                "summary": session.analysis_summary,
                "interest": session.analysis_interest,
                "key_points": session.analysis_key_points or []
            },
            "followup_message": session.followup_message,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting demo analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}", response_model=DemoSessionStatusResponse)
async def get_demo_session_status(session_id: str):
    """
    Get demo session status.

    Returns the current status of various stages:
    - call_status: pending/completed/failed
    - analysis_status: pending/done
    - followup_status: pending/done
    - sms_status: pending/sent
    - crm_status: pending/added
    - chat_ready: true/false
    """
    try:
        if session_id not in demo_sessions:
            raise HTTPException(status_code=404, detail="Demo session not found")

        session = demo_sessions[session_id]

        # Map session status to frontend-friendly statuses
        status_mapping = {
            DemoSessionStatus.INITIATED: {
                "call_status": "pending",
                "analysis_status": "pending",
                "followup_status": "pending",
                "sms_status": "pending",
                "crm_status": "pending",
                "chat_ready": False
            },
            DemoSessionStatus.CALL_IN_PROGRESS: {
                "call_status": "in_progress",
                "analysis_status": "pending",
                "followup_status": "pending",
                "sms_status": "pending",
                "crm_status": "pending",
                "chat_ready": False
            },
            DemoSessionStatus.ANALYZING: {
                "call_status": "completed",
                "analysis_status": "in_progress",
                "followup_status": "pending",
                "sms_status": "pending",
                "crm_status": "pending",
                "chat_ready": False
            },
            DemoSessionStatus.GENERATING_FOLLOWUP: {
                "call_status": "completed",
                "analysis_status": "done",
                "followup_status": "in_progress",
                "sms_status": "pending",
                "crm_status": "pending",
                "chat_ready": False
            },
            DemoSessionStatus.SENDING_SMS: {
                "call_status": "completed",
                "analysis_status": "done",
                "followup_status": "done",
                "sms_status": "sending",
                "crm_status": "pending",
                "chat_ready": True
            },
            DemoSessionStatus.ADDING_TO_CRM: {
                "call_status": "completed",
                "analysis_status": "done",
                "followup_status": "done",
                "sms_status": "sent",
                "crm_status": "adding",
                "chat_ready": True
            },
            DemoSessionStatus.COMPLETED: {
                "call_status": "completed",
                "analysis_status": "done",
                "followup_status": "done",
                "sms_status": "sent",
                "crm_status": "added",
                "chat_ready": True
            },
            DemoSessionStatus.FAILED: {
                "call_status": "failed",
                "analysis_status": "pending",
                "followup_status": "pending",
                "sms_status": "pending",
                "crm_status": "pending",
                "chat_ready": False
            }
        }

        return DemoSessionStatusResponse(**status_mapping[session.status])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting demo session status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics", response_model=Analytics)
async def get_analytics():
    """
    Get analytics data (demo + real combined).

    Returns:
    - Total stats (calls, chats, lead_rate, avg_call_duration)
    - Funnel (called → talked → interested → lead)
    """
    try:
        # Calculate stats from demo data
        total_calls = len(DEMO_CALLS) + len(real_calls)
        total_chats = len(DEMO_CHATS) + len(real_chats)

        # Count interested calls
        interested_count = sum(
            1 for call in DEMO_CALLS
            if call.disposition == FinalDisposition.INTERESTED
        )

        # Calculate lead rate (simplified: interested / total calls)
        lead_rate = interested_count / total_calls if total_calls > 0 else 0

        # Average call duration
        total_duration = sum(call.duration_sec for call in DEMO_CALLS)
        avg_duration = int(total_duration / total_calls) if total_calls > 0 else 0

        # Funnel data
        called = total_calls
        talked = int(called * 0.79)  # ~79% answer rate
        interested = interested_count
        lead = int(interested * 0.4)  # ~40% of interested become leads

        analytics = Analytics(
            totals={
                "calls": total_calls,
                "chats": total_chats,
                "lead_rate": round(lead_rate, 2),
                "avg_call_duration_sec": avg_duration
            },
            funnel=Funnel(
                called=called,
                talked=talked,
                interested=interested,
                lead=lead
            )
        )

        return analytics

    except Exception as e:
        logger.error(f"Error getting analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/interactions", response_model=InteractionsResponse)
async def get_interactions():
    """
    Get all interactions (demo + real).

    Returns a list of all calls and chats, with demo data + real user data.
    Real user data is marked with is_demo=False.
    """
    try:
        interactions = []

        # Add demo calls
        for call in DEMO_CALLS:
            interactions.append(Interaction(
                id=str(call.id),
                is_demo=True,
                type=InteractionType.CALL,
                channel=Channel.VOICE,
                created_at=call.created_at,
                disposition=call.disposition,
                summary=call.summary,
                phone_masked=call.phone_masked
            ))

        # Add demo chats
        for chat in DEMO_CHATS:
            interactions.append(Interaction(
                id=str(chat.id),
                is_demo=True,
                type=InteractionType.CHAT,
                channel=Channel.TELEGRAM,
                created_at=chat.created_at,
                summary=chat.summary
            ))

        # Add real calls (if any)
        for call_id, call_data in real_calls.items():
            interactions.append(Interaction(
                id=call_id,
                is_demo=False,
                type=InteractionType.CALL,
                channel=Channel.VOICE,
                created_at=call_data["created_at"],
                disposition=call_data.get("disposition"),
                summary=call_data.get("summary"),
                phone_masked=call_data.get("phone_masked")
            ))

        # Add real chats (if any)
        for chat_id, chat_data in real_chats.items():
            interactions.append(Interaction(
                id=chat_id,
                is_demo=False,
                type=InteractionType.CHAT,
                channel=Channel.TELEGRAM,
                created_at=chat_data["created_at"],
                summary=chat_data.get("summary")
            ))

        # Sort by created_at descending (newest first)
        interactions.sort(key=lambda x: x.created_at, reverse=True)

        return InteractionsResponse(items=interactions)

    except Exception as e:
        logger.error(f"Error getting interactions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/interaction/{interaction_id}")
async def get_interaction_detail(interaction_id: str):
    """
    Get detailed information about a specific interaction.

    Returns either CallDetailResponse or ChatDetailResponse depending on type.
    """
    try:
        # Try to find in demo calls
        for call in DEMO_CALLS:
            if str(call.id) == interaction_id:
                return CallDetailResponse(
                    id=str(call.id),
                    is_demo=True,
                    phone_masked=call.phone_masked,
                    created_at=call.created_at.isoformat(),
                    duration_sec=call.duration_sec,
                    disposition=call.disposition.value,
                    summary=call.summary or "",
                    transcript=[
                        {
                            "speaker": turn.speaker.value,
                            "text": turn.text
                        }
                        for turn in call.transcript
                    ],
                    crm_record={
                        "status": call.crm_record.status if call.crm_record else "added",
                        "interest": call.crm_record.interest if call.crm_record else None,
                        "telegram_link_sent": call.crm_record.telegram_link_sent if call.crm_record else False,
                        "telegram_connected": call.crm_record.telegram_connected if call.crm_record else False
                    }
                )

        # Try to find in demo chats
        for chat in DEMO_CHATS:
            if str(chat.id) == interaction_id:
                return ChatDetailResponse(
                    id=str(chat.id),
                    is_demo=True,
                    created_at=chat.created_at.isoformat(),
                    summary=chat.summary or "",
                    messages=[
                        {
                            "from": msg.from_,
                            "text": msg.text,
                            "timestamp": msg.timestamp.isoformat()
                        }
                        for msg in chat.messages
                    ]
                )

        # Try to find in real calls
        if interaction_id in real_calls:
            call_data = real_calls[interaction_id]
            return CallDetailResponse(**call_data)

        # Try to find in real chats
        if interaction_id in real_chats:
            chat_data = real_chats[interaction_id]
            return ChatDetailResponse(**chat_data)

        raise HTTPException(status_code=404, detail="Interaction not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting interaction detail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AI Analysis Functions
# ============================================================================

async def analyze_conversation(session: DemoSession, conversation_history: list[dict]) -> dict:
    """
    Analyze conversation using GPT.

    Args:
        session: Demo session
        conversation_history: List of conversation messages

    Returns:
        dict with analysis results (summary, interest, key_points)
    """
    try:
        from app.main import get_openai_client
        import json

        client = get_openai_client()

        # Format conversation for GPT
        conversation_text = "\n".join([
            f"{'Ассистент' if msg['role'] == 'assistant' else 'Клиент'}: {msg['content']}"
            for msg in conversation_history
        ])

        # Create analysis prompt
        analysis_prompt = f"""Проанализируй этот телефонный разговор между AI ассистентом и клиентом.

Разговор:
{conversation_text}

Предоставь анализ в JSON формате:
{{
    "summary": "Краткое резюме разговора (2-3 предложения)",
    "interest": "interested/not_interested/maybe",
    "key_points": ["пункт 1", "пункт 2", "пункт 3"]
}}

Верни только JSON, без дополнительного текста."""

        # Use generate_response method
        result_text = await client.generate_response(
            messages=[
                {"role": "system", "content": "Ты эксперт по анализу телефонных разговоров. Всегда отвечай только в формате JSON."},
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        # Remove markdown code blocks if present
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
            result_text = result_text.strip()

        analysis = json.loads(result_text)

        logger.info(
            f"Conversation analyzed | session_id={session.id} | "
            f"interest={analysis.get('interest')} | "
            f"summary_length={len(analysis.get('summary', ''))}"
        )

        return analysis

    except Exception as e:
        logger.error(f"Error analyzing conversation: {e}", exc_info=True)
        return {
            "summary": "Не удалось проанализировать разговор",
            "interest": "unknown",
            "key_points": []
        }


async def generate_followup(session: DemoSession, conversation_history: list[dict], analysis: dict) -> str:
    """
    Generate personalized follow-up message using GPT.

    Args:
        session: Demo session
        conversation_history: List of conversation messages
        analysis: Analysis results from analyze_conversation

    Returns:
        Follow-up message
    """
    try:
        from app.main import get_openai_client

        client = get_openai_client()

        # Format conversation for GPT
        conversation_text = "\n".join([
            f"{'Ассистент' if msg['role'] == 'assistant' else 'Клиент'}: {msg['content']}"
            for msg in conversation_history
        ])

        # Create follow-up prompt
        followup_prompt = f"""На основе этого телефонного разговора, создай персонализированное follow-up сообщение для клиента.

Разговор:
{conversation_text}

Анализ разговора:
- Уровень интереса: {analysis.get('interest', 'unknown')}
- Краткое резюме: {analysis.get('summary', '')}

Создай короткое (2-3 предложения) follow-up сообщение, которое:
1. Благодарит за разговор
2. Упоминает ключевые моменты из беседы
3. Предлагает следующий шаг или дополнительную информацию

Сообщение должно быть дружелюбным и естественным."""

        # Use generate_response method
        followup_message = await client.generate_response(
            messages=[
                {"role": "system", "content": "Ты эксперт по написанию персонализированных follow-up сообщений после телефонных разговоров."},
                {"role": "user", "content": followup_prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )

        logger.info(
            f"Follow-up generated | session_id={session.id} | "
            f"message_length={len(followup_message)}"
        )

        return followup_message

    except Exception as e:
        logger.error(f"Error generating follow-up: {e}", exc_info=True)
        return "Спасибо за разговор! Как и обещали, отправляем дополнительную информацию. Если возникнут вопросы — всегда рады помочь!"


# ============================================================================
# Background Tasks
# ============================================================================

async def track_demo_session(session_id: str):
    """
    Background task to track demo session progress.

    Monitors the call status via Voximplant webhooks and updates demo session accordingly:
    - INITIATED → CALL_IN_PROGRESS → ANALYZING → GENERATING_FOLLOWUP →
      SENDING_SMS → ADDING_TO_CRM → COMPLETED

    Note: Call status is updated via webhooks in routes_voximplant.py

    Args:
        session_id: Demo session ID
    """
    try:
        session = demo_sessions.get(session_id)
        if not session:
            logger.error(f"Demo session not found for tracking: {session_id}")
            return

        logger.info(f"Starting demo session tracking | session_id={session_id}")

        call_id = str(session.call_id) if session.call_id else None

        if not call_id:
            logger.error(f"Demo session has no call_id | session_id={session_id}")
            session.status = DemoSessionStatus.FAILED
            return

        # Update status: Call in progress
        session.status = DemoSessionStatus.CALL_IN_PROGRESS
        logger.info(f"Demo session: call in progress | session_id={session_id}")

        # Wait for call to complete (max 5 minutes)
        # Status will be updated via Voximplant webhooks
        max_wait_time = 300  # 5 minutes
        poll_interval = 2  # Check every 2 seconds
        elapsed_time = 0

        while elapsed_time < max_wait_time:
            await asyncio.sleep(poll_interval)
            elapsed_time += poll_interval

            # Check if we received CallDisconnected webhook
            # (webhook handler should update session status)
            if session.status != DemoSessionStatus.CALL_IN_PROGRESS:
                logger.info(
                    f"Demo session: call completed via webhook | "
                    f"session_id={session_id} | status={session.status}"
                )
                break

        # If still in progress after timeout, mark as failed
        if session.status == DemoSessionStatus.CALL_IN_PROGRESS:
            logger.warning(f"Demo session: call timeout | session_id={session_id}")
            session.status = DemoSessionStatus.FAILED
            return

        # Call is done, now do post-processing
        # Update status: Analyzing
        session.status = DemoSessionStatus.ANALYZING
        logger.info(f"Demo session: analyzing | session_id={session_id}")

        # Get conversation history from voximplant
        from app.api.routes_voximplant import conversation_history, session_data_store

        # Find voximplant call_id for this session
        # There might be TWO entries in session_data_store:
        # 1. Our UUID as key (created when session starts)
        # 2. Voximplant call_id as key (created when scenario calls get_greeting)
        voximplant_call_id = None
        our_uuid_key = None

        logger.info(f"Looking for voximplant_call_id | session_id={session_id} | session_data_store_keys={list(session_data_store.keys())}")

        for vox_call_id, session_data in session_data_store.items():
            logger.info(f"Checking vox_call_id={vox_call_id} | demo_session_id={session_data.get('demo_session_id')}")
            if session_data.get('demo_session_id') == session_id:
                # Found a matching entry - check if it has conversation_history
                if 'conversation_history' in session_data:
                    voximplant_call_id = vox_call_id
                    logger.info(f"Found matching voximplant_call_id with history={voximplant_call_id}")
                    break
                else:
                    # This is probably our UUID entry - remember it
                    our_uuid_key = vox_call_id
                    logger.info(f"Found matching UUID entry (no history yet)={vox_call_id}")

        # If we didn't find one with conversation_history, use the UUID one
        if not voximplant_call_id and our_uuid_key:
            voximplant_call_id = our_uuid_key
            logger.info(f"Using UUID key as fallback={voximplant_call_id}")

        if not voximplant_call_id:
            logger.warning(f"Could not find any matching entry for session_id={session_id}")

        # Get conversation history
        conv_history = []
        if voximplant_call_id:
            logger.info(f"Checking for conversation_history | voximplant_call_id={voximplant_call_id}")

            # Try to get from session_data_store
            if voximplant_call_id in session_data_store:
                logger.info(f"Found in session_data_store | keys={list(session_data_store[voximplant_call_id].keys())}")

                if 'conversation_history' in session_data_store[voximplant_call_id]:
                    conv_history = session_data_store[voximplant_call_id]['conversation_history']
                    logger.info(f"Found conversation history in session_data_store | messages={len(conv_history)}")
                else:
                    logger.warning(f"No conversation_history key in session_data_store[{voximplant_call_id}]")
                    # Try to find it in another key with same demo_session_id
                    for key, data in session_data_store.items():
                        if data.get('demo_session_id') == session_id and 'conversation_history' in data:
                            conv_history = data['conversation_history']
                            logger.info(f"Found conversation history in alternate key={key} | messages={len(conv_history)}")
                            break
            # Fallback to conversation_history dict (if still exists)
            elif voximplant_call_id in conversation_history:
                conv_history = conversation_history[voximplant_call_id]
                logger.info(f"Found conversation history in conversation_history dict | messages={len(conv_history)}")

        # Save transcript to session
        session.transcript = [
            {
                "role": msg["role"],
                "content": msg["content"]
            }
            for msg in conv_history
        ]

        # Analyze conversation using GPT
        if conv_history:
            analysis = await analyze_conversation(session, conv_history)
            session.analysis_summary = analysis.get('summary')
            session.analysis_interest = analysis.get('interest')
            session.analysis_key_points = analysis.get('key_points', [])
        else:
            logger.warning(f"No conversation history found for session {session_id}")
            session.analysis_summary = "Нет данных для анализа"
            session.analysis_interest = "unknown"
            session.analysis_key_points = []

        # Update status: Generating follow-up
        session.status = DemoSessionStatus.GENERATING_FOLLOWUP
        logger.info(f"Demo session: generating follow-up | session_id={session_id}")

        # Generate personalized follow-up message
        if conv_history:
            session.followup_message = await generate_followup(
                session,
                conv_history,
                {
                    'interest': session.analysis_interest,
                    'summary': session.analysis_summary
                }
            )
        else:
            session.followup_message = (
                "Спасибо за разговор! Как и обещали, отправляем дополнительную информацию. "
                "Если возникнут вопросы — всегда рады помочь!"
            )

        # Update status: Sending SMS
        session.status = DemoSessionStatus.SENDING_SMS
        logger.info(f"Demo session: sending SMS | session_id={session_id}")

        # TODO: Send actual SMS with deep-link
        # For now, just mark as sent
        session.sms_sent = True

        await asyncio.sleep(1)  # Simulate SMS sending

        # Update status: Adding to CRM
        session.status = DemoSessionStatus.ADDING_TO_CRM
        logger.info(f"Demo session: adding to CRM | session_id={session_id}")

        # TODO: Create actual CRM record and chat record
        # For now, just wait
        await asyncio.sleep(1)

        # Update status: Completed
        session.status = DemoSessionStatus.COMPLETED
        from datetime import datetime
        session.completed_at = datetime.utcnow()

        logger.info(f"Demo session completed | session_id={session_id}")

    except Exception as e:
        logger.error(
            f"Error tracking demo session | session_id={session_id} | error={e}",
            exc_info=True
        )

        # Mark session as failed
        if session_id in demo_sessions:
            demo_sessions[session_id].status = DemoSessionStatus.FAILED
