"""
API routes for call operations.
"""
from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks
from pydantic import BaseModel, field_validator
import re

from app.config import settings
from app.utils.logging import logger


router = APIRouter()


# Dependency for API key validation
async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """
    Verify API key from request header.

    Args:
        x_api_key: API key from X-API-Key header

    Raises:
        HTTPException: If API key is invalid
    """
    if x_api_key != settings.API_AUTH_KEY:
        logger.warning(f"Invalid API key attempt: {x_api_key[:10]}...")
        raise HTTPException(status_code=401, detail="Invalid API key")


# Request/Response models
class CallRequest(BaseModel):
    """Request model for initiating a call."""
    phone: str

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate phone number format."""
        if not re.match(r'^(\+7|8)\d{10}$', v):
            raise ValueError('Invalid phone number format. Expected: +7XXXXXXXXXX or 8XXXXXXXXXX')
        return v


class CallResponse(BaseModel):
    """Response model for call initiation."""
    call_id: str
    status: str


@router.post("/call", response_model=CallResponse, dependencies=[Depends(verify_api_key)])
async def create_call(
    request: CallRequest,
    background_tasks: BackgroundTasks
):
    """
    Initiate an outbound call.

    Args:
        request: Call request with phone number
        background_tasks: FastAPI background tasks

    Returns:
        Call response with call_id and status

    Raises:
        HTTPException: On validation or processing errors
    """
    # Import here to avoid circular dependency
    from app.main import get_orchestrator

    try:
        logger.info(f"Received call request | phone={request.phone}")

        orchestrator = get_orchestrator()

        # Create call session
        call_session = orchestrator.create_call(request.phone)
        call_id = str(call_session.id)

        # Start call in background
        background_tasks.add_task(orchestrator.start_call, call_id)

        return CallResponse(
            call_id=call_id,
            status=call_session.status.value
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Error creating call: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
