"""
API routes for telephony callbacks and events.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.integrations.telephony_base import TelephonyEvent
from app.utils.logging import logger


router = APIRouter()


class TelephonyEventRequest(BaseModel):
    """Request model for telephony events."""
    call_id: str
    event: str
    timestamp: str
    reason: Optional[str] = None


@router.post("/telephony/events")
async def handle_telephony_event(request: TelephonyEventRequest):
    """
    Handle events from telephony provider.

    Args:
        request: Telephony event data

    Returns:
        Success response
    """
    # Import here to avoid circular dependency
    from app.main import get_orchestrator

    try:
        logger.info(
            f"Received telephony event | "
            f"call_id={request.call_id} | "
            f"event={request.event} | "
            f"timestamp={request.timestamp}"
        )

        # Map event string to enum
        event_map = {
            "ringing": TelephonyEvent.RINGING,
            "answered": TelephonyEvent.ANSWERED,
            "hangup": TelephonyEvent.HANGUP,
            "busy": TelephonyEvent.BUSY,
            "no_answer": TelephonyEvent.NO_ANSWER,
            "error": TelephonyEvent.ERROR
        }

        event = event_map.get(request.event.lower())
        if not event:
            logger.warning(f"Unknown telephony event: {request.event}")
            # Don't fail, just log and return success
            return {"status": "ok", "message": f"Unknown event: {request.event}"}

        # Handle event
        orchestrator = get_orchestrator()
        await orchestrator.handle_telephony_event(
            request.call_id,
            event,
            request.reason
        )

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Error handling telephony event: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
